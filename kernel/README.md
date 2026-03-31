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
sudo insmod linux_kernel_bridge.ko allowed_uid=$(id -u)
sudo rmmod linux_kernel_bridge
```

If you want to hard-code a different user, pass that numeric UID instead of `$(id -u)`.
The device node is created with open filesystem permissions, but the module itself
rejects any `open`, `read`, `write`, `llseek`, or `ioctl` call from a different UID.

## IOCTLs

The UAPI definitions live in `linux_kernel_bridge.h`.

- `LKBRIDGE_IOCTL_GET_STATS`
- `LKBRIDGE_IOCTL_CLEAR_BUFFER`
- `LKBRIDGE_IOCTL_GET_CAPACITY`
