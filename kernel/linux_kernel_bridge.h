/* SPDX-License-Identifier: GPL-2.0 */
#ifndef LKBRIDGE_LINUX_KERNEL_BRIDGE_H
#define LKBRIDGE_LINUX_KERNEL_BRIDGE_H

#include <linux/ioctl.h>
#include <linux/types.h>

#define LKBRIDGE_DEVICE_NAME "linux_kernel_bridge"
#define LKBRIDGE_PROC_NAME "linux_kernel_bridge"
#define LKBRIDGE_BUFFER_CAPACITY 1024
#define LKBRIDGE_MAGIC 'k'

struct lkbridge_stats {
	__u64 opens;
	__u64 closes;
	__u64 reads;
	__u64 writes;
	__u64 bytes_read;
	__u64 bytes_written;
	__u64 clears;
};

#define LKBRIDGE_IOCTL_GET_STATS _IOR(LKBRIDGE_MAGIC, 0x01, struct lkbridge_stats)
#define LKBRIDGE_IOCTL_CLEAR_BUFFER _IO(LKBRIDGE_MAGIC, 0x02)
#define LKBRIDGE_IOCTL_GET_CAPACITY _IOR(LKBRIDGE_MAGIC, 0x03, __u32)

#endif /* LKBRIDGE_LINUX_KERNEL_BRIDGE_H */
