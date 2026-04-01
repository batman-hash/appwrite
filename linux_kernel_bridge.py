#!/usr/bin/env python3
"""
linux_kernel_bridge.py

A safe-ish ctypes scaffold for Linux user-space code that interacts with
kernel interfaces through libc/syscalls.

Important:
- This runs in user space, not kernel space.
- Requires Linux.
- Some operations may require root.
- Extend carefully: wrong signatures can crash the process.
"""

from __future__ import annotations

import argparse
import ctypes
import ctypes.util
import errno
import os
import time
from dataclasses import dataclass
from typing import Optional, Union, Iterable


# ---------------------------------------------------------------------------
# libc loading
# ---------------------------------------------------------------------------

def _load_libc() -> ctypes.CDLL:
    libc_name = ctypes.util.find_library("c")
    if not libc_name:
        raise RuntimeError("Could not locate libc")
    return ctypes.CDLL(libc_name, use_errno=True)


libc = _load_libc()


# ---------------------------------------------------------------------------
# Basic C aliases
# ---------------------------------------------------------------------------

c_int = ctypes.c_int
c_uint = ctypes.c_uint
c_long = ctypes.c_long
c_ulong = ctypes.c_ulong
c_size_t = ctypes.c_size_t
c_ssize_t = ctypes.c_ssize_t
c_void_p = ctypes.c_void_p
c_char_p = ctypes.c_char_p
c_ubyte = ctypes.c_ubyte
c_ushort = ctypes.c_ushort
c_uint32 = ctypes.c_uint32
c_uint64 = ctypes.c_uint64


# ---------------------------------------------------------------------------
# Linux constants
# ---------------------------------------------------------------------------

AT_FDCWD = -100

O_RDONLY = os.O_RDONLY
O_WRONLY = os.O_WRONLY
O_RDWR = os.O_RDWR
O_CLOEXEC = getattr(os, "O_CLOEXEC", 0)
O_NONBLOCK = getattr(os, "O_NONBLOCK", 0)

SEEK_SET = os.SEEK_SET
SEEK_CUR = os.SEEK_CUR
SEEK_END = os.SEEK_END


# ---------------------------------------------------------------------------
# Exceptions and helpers
# ---------------------------------------------------------------------------

class KernelBridgeError(OSError):
    """Raised on syscall/libc wrapper failure."""


def _raise_errno(prefix: str) -> None:
    err = ctypes.get_errno()
    raise KernelBridgeError(err, f"{prefix}: {os.strerror(err)}")


def _check_neg1(result: int, func_name: str) -> int:
    if result == -1:
        _raise_errno(func_name)
    return result


def _ensure_bytes(value: Union[str, bytes, os.PathLike]) -> bytes:
    if isinstance(value, bytes):
        return value
    if isinstance(value, os.PathLike):
        value = os.fspath(value)
    if isinstance(value, str):
        return value.encode("utf-8")
    raise TypeError(f"Expected str/bytes/pathlike, got {type(value)!r}")


# ---------------------------------------------------------------------------
# libc function declarations
# ---------------------------------------------------------------------------

# int open(const char *pathname, int flags, mode_t mode);
libc.open.argtypes = [c_char_p, c_int, c_int]
libc.open.restype = c_int

# int close(int fd);
libc.close.argtypes = [c_int]
libc.close.restype = c_int

# ssize_t read(int fd, void *buf, size_t count);
libc.read.argtypes = [c_int, c_void_p, c_size_t]
libc.read.restype = c_ssize_t

# ssize_t write(int fd, const void *buf, size_t count);
libc.write.argtypes = [c_int, c_void_p, c_size_t]
libc.write.restype = c_ssize_t

# off_t lseek(int fd, off_t offset, int whence);
libc.lseek.argtypes = [c_int, c_long, c_int]
libc.lseek.restype = c_long

# int ioctl(int fd, unsigned long request, ...);
# Variadic functions are tricky in ctypes. We declare the fixed prefix and pass
# a pointer/value manually from wrappers below.
libc.ioctl.argtypes = [c_int, c_ulong, c_void_p]
libc.ioctl.restype = c_int

# long syscall(long number, ...);
libc.syscall.argtypes = None
libc.syscall.restype = c_long


# ---------------------------------------------------------------------------
# Optional kernel-ish structs
# ---------------------------------------------------------------------------

class TimeVal(ctypes.Structure):
    _fields_ = [
        ("tv_sec", c_long),
        ("tv_usec", c_long),
    ]


@dataclass
class SyscallResult:
    value: int
    errno_name: Optional[str] = None


@dataclass
class PriorityBoostResult:
    realtime: bool
    scheduler: str
    scheduler_priority: int
    nice_level: int
    message: str = ""


@dataclass(frozen=True)
class ProcessMapEntry:
    start: int
    end: int
    offset: int
    pathname: str


@dataclass(frozen=True)
class ProcessBaseAddress:
    pid: int
    comm: str
    exe_path: Optional[str]
    base_address: Optional[int]


# ---------------------------------------------------------------------------
# High-level wrapper class
# ---------------------------------------------------------------------------

class LinuxKernelBridge:
    """
    Thin Python wrapper over selected libc/syscall entry points.
    """

    def open(self, path: Union[str, bytes, os.PathLike], flags: int, mode: int = 0o644) -> int:
        bpath = _ensure_bytes(path)
        fd = libc.open(bpath, flags, mode)
        return _check_neg1(fd, "open")

    def close(self, fd: int) -> None:
        rc = libc.close(fd)
        _check_neg1(rc, "close")

    def read(self, fd: int, size: int) -> bytes:
        if size < 0:
            raise ValueError("size must be >= 0")
        buf = ctypes.create_string_buffer(size)
        n = libc.read(fd, ctypes.byref(buf), size)
        _check_neg1(n, "read")
        return buf.raw[:n]

    def write(self, fd: int, data: Union[bytes, bytearray, memoryview]) -> int:
        payload = bytes(data)
        buf = ctypes.create_string_buffer(payload, len(payload))
        n = libc.write(fd, ctypes.byref(buf), len(payload))
        return _check_neg1(n, "write")

    def lseek(self, fd: int, offset: int, whence: int = SEEK_SET) -> int:
        pos = libc.lseek(fd, offset, whence)
        return _check_neg1(pos, "lseek")

    def ioctl_ptr(self, fd: int, request: int, obj: ctypes._CData) -> int:
        rc = libc.ioctl(fd, request, ctypes.byref(obj))
        return _check_neg1(rc, "ioctl")

    def ioctl_value(self, fd: int, request: int, value: int = 0) -> int:
        ptr = ctypes.c_ulong(value)
        rc = libc.ioctl(fd, request, ctypes.byref(ptr))
        return _check_neg1(rc, "ioctl")

    def syscall0(self, nr: int) -> int:
        rc = libc.syscall(c_long(nr))
        return _check_neg1(rc, "syscall")

    def syscall1(self, nr: int, a1: int) -> int:
        rc = libc.syscall(c_long(nr), c_long(a1))
        return _check_neg1(rc, "syscall")

    def syscall2(self, nr: int, a1: int, a2: int) -> int:
        rc = libc.syscall(c_long(nr), c_long(a1), c_long(a2))
        return _check_neg1(rc, "syscall")

    def syscall3(self, nr: int, a1: int, a2: int, a3: int) -> int:
        rc = libc.syscall(c_long(nr), c_long(a1), c_long(a2), c_long(a3))
        return _check_neg1(rc, "syscall")

    def syscall6(self, nr: int, a1: int, a2: int, a3: int, a4: int, a5: int, a6: int) -> int:
        rc = libc.syscall(
            c_long(nr),
            c_long(a1),
            c_long(a2),
            c_long(a3),
            c_long(a4),
            c_long(a5),
            c_long(a6),
        )
        return _check_neg1(rc, "syscall")


# ---------------------------------------------------------------------------
# Context manager for file descriptors
# ---------------------------------------------------------------------------

class FD:
    def __init__(self, bridge: LinuxKernelBridge, fd: int):
        self.bridge = bridge
        self.fd = fd
        self.closed = False

    def close(self) -> None:
        if not self.closed:
            self.bridge.close(self.fd)
            self.closed = True

    def fileno(self) -> int:
        return self.fd

    def __enter__(self) -> "FD":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()


# ---------------------------------------------------------------------------
# Example helpers
# ---------------------------------------------------------------------------

def read_file(path: Union[str, bytes, os.PathLike], chunk_size: int = 4096) -> bytes:
    bridge = LinuxKernelBridge()
    fd = bridge.open(path, O_RDONLY | O_CLOEXEC)
    with FD(bridge, fd) as f:
        parts = []
        while True:
            chunk = bridge.read(f.fileno(), chunk_size)
            if not chunk:
                break
            parts.append(chunk)
        return b"".join(parts)


def write_file(path: Union[str, bytes, os.PathLike], data: bytes, mode: int = 0o644) -> int:
    bridge = LinuxKernelBridge()
    flags = O_WRONLY | O_CLOEXEC | os.O_CREAT | os.O_TRUNC
    fd = bridge.open(path, flags, mode)
    with FD(bridge, fd) as f:
        total = 0
        mv = memoryview(data)
        while total < len(data):
            written = bridge.write(f.fileno(), mv[total:])
            total += written
        return total


# ---------------------------------------------------------------------------
# Minimal ioctl example placeholder
# ---------------------------------------------------------------------------

# Replace with the actual request code for your device/subsystem.
DUMMY_IOCTL_REQUEST = 0x00000000


class DummyIoctlStruct(ctypes.Structure):
    _fields_ = [
        ("field1", c_uint32),
        ("field2", c_uint32),
    ]


def example_ioctl(device_path: str) -> DummyIoctlStruct:
    bridge = LinuxKernelBridge()
    fd = bridge.open(device_path, O_RDWR | O_CLOEXEC)
    payload = DummyIoctlStruct(123, 456)
    with FD(bridge, fd) as f:
        bridge.ioctl_ptr(f.fileno(), DUMMY_IOCTL_REQUEST, payload)
    return payload


# ---------------------------------------------------------------------------
# Raw syscall numbers
# ---------------------------------------------------------------------------
# Syscall numbers are architecture-specific. Fill these from the correct
# unistd header/man pages for your target arch/kernel/userspace ABI.

class SyscallNumbers:
    """
    Example placeholders. Do not trust these blindly.
    Populate per architecture, e.g. x86_64 Linux.
    """
    GETPID = 39      # common on x86_64
    GETUID = 102     # common on x86_64
    GETTID = 186     # common on x86_64


def getpid_via_syscall() -> int:
    bridge = LinuxKernelBridge()
    return bridge.syscall0(SyscallNumbers.GETPID)


def getuid_via_syscall() -> int:
    bridge = LinuxKernelBridge()
    return bridge.syscall0(SyscallNumbers.GETUID)


def gettid_via_syscall() -> int:
    bridge = LinuxKernelBridge()
    return bridge.syscall0(SyscallNumbers.GETTID)


# ---------------------------------------------------------------------------
# Error decoding helpers
# ---------------------------------------------------------------------------

def errno_name(err: int) -> str:
    return errno.errorcode.get(err, f"ERRNO_{err}")


def describe_last_errno() -> str:
    err = ctypes.get_errno()
    return f"{errno_name(err)} ({err}): {os.strerror(err)}"


# ---------------------------------------------------------------------------
# Device-file helper patterns
# ---------------------------------------------------------------------------

def read_from_procfs(path: str) -> str:
    return read_file(path).decode("utf-8", errors="replace")


def read_from_sysfs(path: str) -> str:
    return read_file(path).decode("utf-8", errors="replace").strip()


def write_to_sysfs(path: str, value: str) -> int:
    return write_file(path, value.encode("utf-8"))


# ---------------------------------------------------------------------------
# Process monitoring helpers
# ---------------------------------------------------------------------------

def _normalize_proc_path(path: str) -> str:
    cleaned = (path or "").strip()
    if not cleaned or cleaned.startswith("["):
        return ""
    if cleaned.endswith(" (deleted)"):
        cleaned = cleaned[:-10]
    return os.path.realpath(cleaned)


def _parse_proc_maps_line(line: str) -> Optional[ProcessMapEntry]:
    stripped = line.strip()
    if not stripped:
        return None

    parts = stripped.split(None, 5)
    if len(parts) < 5:
        return None

    address_range, _perms, offset_str, _dev, _inode = parts[:5]
    pathname = parts[5] if len(parts) == 6 else ""

    try:
        start_str, end_str = address_range.split("-", 1)
        return ProcessMapEntry(
            start=int(start_str, 16),
            end=int(end_str, 16),
            offset=int(offset_str, 16),
            pathname=pathname,
        )
    except ValueError:
        return None


def _main_executable_base_from_maps_text(maps_text: str, exe_path: Optional[str] = None) -> Optional[int]:
    normalized_exe = _normalize_proc_path(exe_path) if exe_path else ""
    fallback = None

    for raw_line in maps_text.splitlines():
        entry = _parse_proc_maps_line(raw_line)
        if entry is None or entry.offset != 0:
            continue

        normalized_path = _normalize_proc_path(entry.pathname)
        if normalized_exe and normalized_path and normalized_path == normalized_exe:
            return entry.start

        if fallback is None and normalized_path:
            fallback = entry.start

    return fallback


def get_process_main_base_address(pid: int, proc_root: str = "/proc") -> Optional[int]:
    if pid < 0:
        raise ValueError("pid must be >= 0")

    maps_path = os.path.join(proc_root, str(pid), "maps")
    exe_link = os.path.join(proc_root, str(pid), "exe")

    exe_path = None
    try:
        exe_path = os.readlink(exe_link)
    except OSError:
        exe_path = None

    try:
        maps_text = read_file(maps_path).decode("utf-8", errors="replace")
    except OSError:
        return None

    return _main_executable_base_from_maps_text(maps_text, exe_path)


def list_process_base_addresses(proc_root: str = "/proc") -> list[ProcessBaseAddress]:
    entries = []

    try:
        proc_names = sorted((name for name in os.listdir(proc_root) if name.isdigit()), key=int)
    except OSError:
        return entries

    for name in proc_names:
        pid = int(name)
        comm = f"pid-{pid}"
        try:
            comm = read_from_procfs(os.path.join(proc_root, name, "comm")).strip() or comm
        except Exception:
            pass

        exe_path = None
        try:
            exe_path = os.readlink(os.path.join(proc_root, name, "exe"))
        except OSError:
            exe_path = None

        entries.append(
            ProcessBaseAddress(
                pid=pid,
                comm=comm,
                exe_path=exe_path,
                base_address=get_process_main_base_address(pid, proc_root),
            )
        )

    return entries


def format_process_base_snapshot(entries: Iterable[ProcessBaseAddress]) -> str:
    rows = list(entries)
    lines = [
        f"{'PID':>7} {'BASE':>18} {'COMM':<24} EXE",
        f"{'---':>7} {'----':>18} {'----':<24} ---",
    ]

    for entry in rows:
        base = f"0x{entry.base_address:x}" if entry.base_address is not None else "n/a"
        exe = entry.exe_path or ""
        comm = entry.comm[:24]
        lines.append(f"{entry.pid:>7} {base:>18} {comm:<24} {exe}")

    lines.append(f"processes: {len(rows)}")
    return "\n".join(lines)


def monitor_process_base_addresses(interval: float = 1.0, proc_root: str = "/proc", once: bool = False) -> int:
    require_linux()

    if interval < 0:
        raise ValueError("interval must be >= 0")

    try:
        while True:
            stamp = time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime())
            print(f"== process base address monitor @ {stamp} ==")
            print(format_process_base_snapshot(list_process_base_addresses(proc_root)))

            if once or interval <= 0:
                break

            print()
            time.sleep(interval)
    except KeyboardInterrupt:
        print("\nMonitor stopped.")

    return 0


# ---------------------------------------------------------------------------
# Safety checks
# ---------------------------------------------------------------------------

def require_linux() -> None:
    if os.name != "posix":
        raise RuntimeError("This template is Linux/Unix oriented")
    if not os.path.exists("/proc"):
        raise RuntimeError("This does not appear to be a Linux environment")


def require_root() -> None:
    if os.geteuid() != 0:
        raise PermissionError("This operation typically requires root privileges")


def get_current_nice() -> int:
    """
    Return the current process nice value.

    On Linux, os.nice(0) reports the current niceness without changing it.
    """
    require_linux()
    return os.nice(0)


def get_current_scheduler_policy() -> Optional[int]:
    require_linux()
    getter = getattr(os, "sched_getscheduler", None)
    if getter is None:
        return None

    try:
        return getter(0)
    except OSError:
        return None


def _scheduler_name(policy: Optional[int]) -> str:
    policy_map = {
        getattr(os, "SCHED_OTHER", None): "SCHED_OTHER",
        getattr(os, "SCHED_FIFO", None): "SCHED_FIFO",
        getattr(os, "SCHED_RR", None): "SCHED_RR",
    }
    return policy_map.get(policy, "UNKNOWN")


def boost_current_process_priority(target_nice: int = -20) -> PriorityBoostResult:
    """
    Try to raise the current process to the highest priority the OS allows.

    This only affects the current process, not the whole user session.
    The returned value captures whether a realtime scheduler was granted.
    """
    require_linux()

    if not isinstance(target_nice, int):
        raise TypeError("target_nice must be an int")

    # Linux nice values range from -20 (highest priority) to 19 (lowest).
    target_nice = max(-20, min(19, target_nice))
    current_policy = get_current_scheduler_policy()
    current_nice = get_current_nice()
    result = PriorityBoostResult(
        realtime=False,
        scheduler=_scheduler_name(current_policy),
        scheduler_priority=0,
        nice_level=current_nice,
        message="",
    )

    # Try to move to a realtime scheduler first. This is the true "highest"
    # priority level on Linux when permitted by the kernel and capabilities.
    sched_setscheduler = getattr(os, "sched_setscheduler", None)
    sched_get_priority_max = getattr(os, "sched_get_priority_max", None)
    sched_param = getattr(os, "sched_param", None)
    realtime_policies = []
    fifo = getattr(os, "SCHED_FIFO", None)
    rr = getattr(os, "SCHED_RR", None)
    if fifo is not None:
        realtime_policies.append(fifo)
    if rr is not None:
        realtime_policies.append(rr)

    if sched_setscheduler and sched_get_priority_max and sched_param and realtime_policies:
        realtime_errors = []
        for policy in realtime_policies:
            try:
                priority = sched_get_priority_max(policy)
                sched_setscheduler(0, policy, sched_param(priority))
                result.realtime = True
                result.scheduler = _scheduler_name(policy)
                result.scheduler_priority = priority
                result.nice_level = get_current_nice()
                result.message = f"Applied realtime scheduler {result.scheduler} with priority {priority}"
                return result
            except (PermissionError, OSError, AttributeError, ValueError) as exc:
                realtime_errors.append(f"{_scheduler_name(policy)} unavailable: {exc}")
        if realtime_errors:
            result.message = "; ".join(realtime_errors)

    # Fall back to the highest nice priority if realtime is unavailable.
    setter = getattr(os, "setpriority", None)
    prio_process = getattr(os, "PRIO_PROCESS", 0)
    if setter is not None:
        try:
            setter(prio_process, 0, target_nice)
            result.nice_level = get_current_nice()
        except (PermissionError, OSError, AttributeError):
            pass
    else:
        while result.nice_level > target_nice:
            try:
                result.nice_level = os.nice(-1)
            except OSError:
                break

    if result.nice_level <= target_nice:
        if result.message:
            result.message += "; "
        result.message += f"Reached nice level {result.nice_level}"
    elif result.message:
        result.message += f"; nice level remained {result.nice_level}"
    else:
        result.message = "Priority boost limited by OS permissions"

    return result


# ---------------------------------------------------------------------------
# Debugging utilities
# ---------------------------------------------------------------------------

def hexdump(data: bytes, width: int = 16) -> str:
    lines = []
    for offset in range(0, len(data), width):
        chunk = data[offset:offset + width]
        hex_part = " ".join(f"{b:02x}" for b in chunk)
        ascii_part = "".join(chr(b) if 32 <= b < 127 else "." for b in chunk)
        lines.append(f"{offset:08x}  {hex_part:<{width * 3}}  {ascii_part}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI demo
# ---------------------------------------------------------------------------

def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="LinuxKernelBridge demo plus a process base-address monitor"
    )
    parser.add_argument(
        "--monitor",
        action="store_true",
        help="Continuously scan accessible /proc/<pid>/maps entries and print base addresses",
    )
    parser.add_argument(
        "--interval",
        type=float,
        default=1.0,
        help="Seconds between refreshes in monitor mode",
    )
    parser.add_argument(
        "--once",
        action="store_true",
        help="Print one monitor snapshot and exit instead of looping",
    )
    parser.add_argument(
        "--proc-root",
        default="/proc",
        help="Procfs root to scan in monitor mode",
    )
    parser.add_argument(
        "--boost-priority",
        action="store_true",
        help="Raise the current process priority before running the demo or monitor",
    )
    parser.add_argument(
        "--target-nice",
        type=int,
        default=-20,
        help="Target nice level used with --boost-priority",
    )
    return parser


def main(argv: Optional[list[str]] = None) -> int:
    require_linux()

    parser = _build_arg_parser()
    args = parser.parse_args(argv)

    if args.boost_priority:
        result = boost_current_process_priority(target_nice=args.target_nice)
        print(
            "CPU priority adjusted: "
            f"scheduler={result.scheduler}, "
            f"realtime={result.realtime}, "
            f"nice={result.nice_level}. "
            f"{result.message}"
        )

    if args.monitor:
        return monitor_process_base_addresses(
            interval=args.interval,
            proc_root=args.proc_root,
            once=args.once,
        )

    print("== LinuxKernelBridge demo ==")

    print("\n[1] libc/syscall examples")
    try:
        print("getpid() via syscall:", getpid_via_syscall())
        print("getuid() via syscall:", getuid_via_syscall())
        print("gettid() via syscall:", gettid_via_syscall())
    except Exception as e:
        print("syscall demo failed:", e)

    print("\n[2] Reading /proc/version")
    try:
        version = read_from_procfs("/proc/version")
        print(version.strip())
    except Exception as e:
        print("procfs demo failed:", e)

    print("\n[3] Reading /sys/kernel/hostname if present")
    candidate_paths = [
        "/proc/sys/kernel/hostname",
        "/etc/hostname",
    ]
    for p in candidate_paths:
        try:
            text = read_file(p).decode("utf-8", errors="replace").strip()
            print(f"{p}: {text}")
            break
        except Exception:
            continue

    print("\n[4] Hexdump first 64 bytes of /proc/self/stat")
    try:
        blob = read_file("/proc/self/stat")[:64]
        print(hexdump(blob))
    except Exception as e:
        print("hexdump demo failed:", e)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
