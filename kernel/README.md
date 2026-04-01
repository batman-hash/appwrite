# Linux Kernel Bridge

This directory contains the kernel-space version of the bridge that used to live only in `linux_kernel_bridge.py`.

## What it exposes

- `/dev/linux_kernel_bridge`
- `/proc/linux_kernel_bridge`

## Supported operations

- `read`
- `write`
- `llseek`
- `ioctl`

## Build

From this directory:

```bash
make
```

That uses the installed kernel headers for the running kernel:

```bash
/lib/modules/$(uname -r)/build
```

## Load and unload

```bash
../../build.sh kernel-load-current-user
sudo rmmod linux_kernel_bridge
```

`build.sh kernel-load-current-user` will try to build `linux_kernel_bridge.ko`
automatically if it is missing. If that build fails, install the kernel headers
for your running kernel and run `make -C appwrite/kernel` again.

If you want to hard-code a different user, pass that numeric UID with `sudo insmod linux_kernel_bridge.ko allowed_uid=<uid>`.
The helper script uses `SUDO_USER` when available so `sudo` does not accidentally
turn the current user into `root`; otherwise it falls back to `whoami`.
The device node is created with open filesystem permissions, but the module itself
rejects any `open`, `read`, `write`, `llseek`, or `ioctl` call from a different UID.

The in-kernel byte buffer is tunable with `buffer_capacity`. Lower values reduce
kernel memory use and the amount of data copied through the module:

```bash
sudo insmod linux_kernel_bridge.ko allowed_uid=<uid> buffer_capacity=256
```

`build.sh kernel-load-current-user` also honors the `LKBRIDGE_BUFFER_CAPACITY`
environment variable, so you can load a smaller payload without editing the
command:

```bash
LKBRIDGE_BUFFER_CAPACITY=256 ../../build.sh kernel-load-current-user
```

## IOCTLs

The UAPI definitions live in `linux_kernel_bridge.h`.

- `LKBRIDGE_IOCTL_GET_STATS`
- `LKBRIDGE_IOCTL_CLEAR_BUFFER`
- `LKBRIDGE_IOCTL_GET_CAPACITY`

## Monitor mode

The user-space helper now includes a monitor mode that scans accessible
`/proc/<pid>/maps` entries and prints the main executable base address for
each process.

```bash
python3 ../linux_kernel_bridge.py --monitor --boost-priority --target-nice -10 --interval 1
```

Use `--once` if you only want one snapshot, and `--proc-root` if you are
inspecting a mounted procfs somewhere other than `/proc`.
If you want the monitor to do less work, use a larger `--interval` or `--once`
so it samples less often.
