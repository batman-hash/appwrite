// SPDX-License-Identifier: GPL-2.0
/*
 * linux_kernel_bridge.c
 *
 * Kernel-space companion to the user-space ctypes bridge.
 *
 * Exposes:
 *   - /dev/linux_kernel_bridge   (misc character device)
 *   - /proc/linux_kernel_bridge  (status and stats)
 *
 * The device behaves like a tiny in-kernel byte buffer:
 *   - read() streams the current buffer contents
 *   - write() updates the buffer at the current file position
 *   - llseek() moves the file position
 *   - ioctl() can fetch stats or clear the buffer
 */

#include <linux/fs.h>
#include <linux/miscdevice.h>
#include <linux/mutex.h>
#include <linux/module.h>
#include <linux/proc_fs.h>
#include <linux/seq_file.h>
#include <linux/slab.h>
#include <linux/uaccess.h>
#include <linux/version.h>

#include "linux_kernel_bridge.h"

struct lkbridge_device {
	char *buffer;
	size_t capacity;
	size_t size;
	struct mutex lock;
	struct lkbridge_stats stats;
	struct proc_dir_entry *proc_entry;
	bool registered;
};

static struct lkbridge_device g_dev;

static int lkbridge_proc_show(struct seq_file *m, void *v);
static void lkbridge_reset_locked(void);

static int lkbridge_open(struct inode *inode, struct file *file)
{
	(void)inode;

	mutex_lock(&g_dev.lock);
	g_dev.stats.opens++;
	mutex_unlock(&g_dev.lock);

	file->private_data = &g_dev;
	return 0;
}

static int lkbridge_release(struct inode *inode, struct file *file)
{
	(void)inode;

	mutex_lock(&g_dev.lock);
	g_dev.stats.closes++;
	mutex_unlock(&g_dev.lock);
	return 0;
}

static ssize_t lkbridge_read(struct file *file, char __user *buf, size_t count, loff_t *ppos)
{
	ssize_t ret;
	size_t available;
	size_t to_copy;

	(void)file;

	if (!count)
		return 0;

	if (mutex_lock_interruptible(&g_dev.lock))
		return -ERESTARTSYS;

	if (*ppos >= g_dev.size) {
		ret = 0;
		goto out_unlock;
	}

	available = g_dev.size - (size_t)*ppos;
	to_copy = min(count, available);

	if (copy_to_user(buf, g_dev.buffer + *ppos, to_copy)) {
		ret = -EFAULT;
		goto out_unlock;
	}

	*ppos += to_copy;
	g_dev.stats.reads++;
	g_dev.stats.bytes_read += to_copy;
	ret = (ssize_t)to_copy;

out_unlock:
	mutex_unlock(&g_dev.lock);
	return ret;
}

static ssize_t lkbridge_write(struct file *file, const char __user *buf, size_t count, loff_t *ppos)
{
	ssize_t ret;
	size_t space_left;
	size_t to_copy;

	(void)file;

	if (!count)
		return 0;

	if (mutex_lock_interruptible(&g_dev.lock))
		return -ERESTARTSYS;

	if (*ppos >= g_dev.capacity) {
		ret = -ENOSPC;
		goto out_unlock;
	}

	space_left = g_dev.capacity - (size_t)*ppos;
	to_copy = min(count, space_left);

	if (copy_from_user(g_dev.buffer + *ppos, buf, to_copy)) {
		ret = -EFAULT;
		goto out_unlock;
	}

	*ppos += to_copy;
	if ((size_t)*ppos > g_dev.size)
		g_dev.size = (size_t)*ppos;

	g_dev.stats.writes++;
	g_dev.stats.bytes_written += to_copy;
	ret = (ssize_t)to_copy;

out_unlock:
	mutex_unlock(&g_dev.lock);
	return ret;
}

static loff_t lkbridge_llseek(struct file *file, loff_t offset, int whence)
{
	loff_t new_pos;
	loff_t limit;
	loff_t current;

	if (mutex_lock_interruptible(&g_dev.lock))
		return -ERESTARTSYS;

	current = file->f_pos;
	limit = g_dev.capacity;

	switch (whence) {
	case SEEK_SET:
		new_pos = offset;
		break;
	case SEEK_CUR:
		new_pos = current + offset;
		break;
	case SEEK_END:
		new_pos = (loff_t)g_dev.size + offset;
		break;
	default:
		mutex_unlock(&g_dev.lock);
		return -EINVAL;
	}

	if (new_pos < 0 || new_pos > limit) {
		mutex_unlock(&g_dev.lock);
		return -EINVAL;
	}

	file->f_pos = new_pos;
	mutex_unlock(&g_dev.lock);
	return new_pos;
}

static long lkbridge_ioctl(struct file *file, unsigned int cmd, unsigned long arg)
{
	struct lkbridge_stats stats_snapshot;
	__u32 capacity_snapshot;

	(void)file;

	switch (cmd) {
	case LKBRIDGE_IOCTL_GET_STATS:
		if (mutex_lock_interruptible(&g_dev.lock))
			return -ERESTARTSYS;
		stats_snapshot = g_dev.stats;
		mutex_unlock(&g_dev.lock);
		if (copy_to_user((void __user *)arg, &stats_snapshot, sizeof(stats_snapshot)))
			return -EFAULT;
		return 0;

	case LKBRIDGE_IOCTL_CLEAR_BUFFER:
		if (mutex_lock_interruptible(&g_dev.lock))
			return -ERESTARTSYS;
		lkbridge_reset_locked();
		mutex_unlock(&g_dev.lock);
		return 0;

	case LKBRIDGE_IOCTL_GET_CAPACITY:
		capacity_snapshot = (__u32)g_dev.capacity;
		if (copy_to_user((void __user *)arg, &capacity_snapshot, sizeof(capacity_snapshot)))
			return -EFAULT;
		return 0;

	default:
		return -ENOTTY;
	}
}

#ifdef CONFIG_COMPAT
static long lkbridge_compat_ioctl(struct file *file, unsigned int cmd, unsigned long arg)
{
	return lkbridge_ioctl(file, cmd, arg);
}
#endif

static const struct file_operations lkbridge_fops = {
	.owner = THIS_MODULE,
	.open = lkbridge_open,
	.release = lkbridge_release,
	.read = lkbridge_read,
	.write = lkbridge_write,
	.llseek = lkbridge_llseek,
	.unlocked_ioctl = lkbridge_ioctl,
#ifdef CONFIG_COMPAT
	.compat_ioctl = lkbridge_compat_ioctl,
#endif
};

static struct miscdevice lkbridge_miscdev = {
	.minor = MISC_DYNAMIC_MINOR,
	.name = LKBRIDGE_DEVICE_NAME,
	.fops = &lkbridge_fops,
	.mode = 0660,
};

static void lkbridge_reset_locked(void)
{
	memset(g_dev.buffer, 0, g_dev.capacity);
	g_dev.size = 0;
	g_dev.stats.clears++;
}

static int lkbridge_proc_open(struct inode *inode, struct file *file)
{
	(void)inode;

	return single_open(file, lkbridge_proc_show, NULL);
}

#if LINUX_VERSION_CODE >= KERNEL_VERSION(5, 6, 0)
static const struct proc_ops lkbridge_proc_ops = {
	.proc_open = lkbridge_proc_open,
	.proc_read = seq_read,
	.proc_lseek = seq_lseek,
	.proc_release = single_release,
};
#else
static const struct file_operations lkbridge_proc_ops = {
	.owner = THIS_MODULE,
	.open = lkbridge_proc_open,
	.read = seq_read,
	.llseek = seq_lseek,
	.release = single_release,
};
#endif

static int lkbridge_proc_show(struct seq_file *m, void *v)
{
	(void)v;

	struct lkbridge_stats stats;
	size_t used;
	size_t capacity;

	if (mutex_lock_interruptible(&g_dev.lock))
		return -ERESTARTSYS;

	stats = g_dev.stats;
	used = g_dev.size;
	capacity = g_dev.capacity;
	mutex_unlock(&g_dev.lock);

	seq_puts(m, "linux_kernel_bridge\n");
	seq_printf(m, "device: /dev/%s\n", LKBRIDGE_DEVICE_NAME);
	seq_printf(m, "proc: /proc/%s\n", LKBRIDGE_PROC_NAME);
	seq_printf(m, "buffer_used: %zu\n", used);
	seq_printf(m, "buffer_capacity: %zu\n", capacity);
	seq_printf(m, "opens: %llu\n", (unsigned long long)stats.opens);
	seq_printf(m, "closes: %llu\n", (unsigned long long)stats.closes);
	seq_printf(m, "reads: %llu\n", (unsigned long long)stats.reads);
	seq_printf(m, "writes: %llu\n", (unsigned long long)stats.writes);
	seq_printf(m, "bytes_read: %llu\n", (unsigned long long)stats.bytes_read);
	seq_printf(m, "bytes_written: %llu\n", (unsigned long long)stats.bytes_written);
	seq_printf(m, "clears: %llu\n", (unsigned long long)stats.clears);
	return 0;
}

static int __init lkbridge_init(void)
{
	int ret;

	memset(&g_dev, 0, sizeof(g_dev));
	mutex_init(&g_dev.lock);
	g_dev.capacity = LKBRIDGE_BUFFER_CAPACITY;
	g_dev.buffer = kzalloc(g_dev.capacity, GFP_KERNEL);
	if (!g_dev.buffer)
		return -ENOMEM;

	ret = misc_register(&lkbridge_miscdev);
	if (ret)
		goto err_buffer;
	g_dev.registered = true;

	g_dev.proc_entry = proc_create(LKBRIDGE_PROC_NAME, 0444, NULL, &lkbridge_proc_ops);
	if (!g_dev.proc_entry) {
		ret = -ENOMEM;
		goto err_misc;
	}

	pr_info("linux_kernel_bridge loaded: /dev/%s and /proc/%s\n",
		LKBRIDGE_DEVICE_NAME, LKBRIDGE_PROC_NAME);
	return 0;

err_misc:
	misc_deregister(&lkbridge_miscdev);
	g_dev.registered = false;
err_buffer:
	kfree(g_dev.buffer);
	g_dev.buffer = NULL;
	return ret;
}

static void __exit lkbridge_exit(void)
{
	if (g_dev.proc_entry) {
		proc_remove(g_dev.proc_entry);
		g_dev.proc_entry = NULL;
	}

	if (g_dev.registered) {
		misc_deregister(&lkbridge_miscdev);
		g_dev.registered = false;
	}

	kfree(g_dev.buffer);
	g_dev.buffer = NULL;

	pr_info("linux_kernel_bridge unloaded\n");
}

module_init(lkbridge_init);
module_exit(lkbridge_exit);

MODULE_AUTHOR("OpenAI");
MODULE_DESCRIPTION("Kernel-space bridge for a tiny user-facing byte buffer");
MODULE_LICENSE("GPL");
