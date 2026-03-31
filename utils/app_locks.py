import atexit
import os
import platform
import subprocess

_ACQUIRED_LOCK_FILES = []
_CLEANUP_REGISTERED = False


def _pid_is_running(pid):
    if not isinstance(pid, int) or pid <= 0:
        return False

    # Windows: avoid os.kill(pid, 0) instability (can raise WinError 87 / SystemError).
    if platform.system().lower().startswith("win"):
        try:
            import ctypes

            PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
            handle = ctypes.windll.kernel32.OpenProcess(
                PROCESS_QUERY_LIMITED_INFORMATION, False, pid
            )
            if handle:
                ctypes.windll.kernel32.CloseHandle(handle)
                return True
        except Exception:
            pass

        # Fallback for restricted environments.
        try:
            result = subprocess.run(
                ["tasklist", "/FI", f"PID eq {pid}"],
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                text=True,
                encoding="utf-8",
                errors="ignore",
            )
            return str(pid) in (result.stdout or "")
        except Exception:
            return False

    try:
        os.kill(pid, 0)
        return True
    except PermissionError:
        return True
    except Exception:
        return False


def _cleanup_locks():
    for lock_path in list(_ACQUIRED_LOCK_FILES):
        try:
            if os.path.exists(lock_path):
                with open(lock_path, "r", encoding="utf-8") as f:
                    pid_in_file = int((f.read() or "0").strip())
                if pid_in_file == os.getpid():
                    os.remove(lock_path)
        except Exception:
            pass


def _register_cleanup_once():
    global _CLEANUP_REGISTERED
    if not _CLEANUP_REGISTERED:
        atexit.register(_cleanup_locks)
        _CLEANUP_REGISTERED = True


def _acquire_pid_lock(lock_path, lock_label):
    if os.path.exists(lock_path):
        try:
            with open(lock_path, "r", encoding="utf-8") as f:
                existing_pid = int((f.read() or "0").strip())
        except Exception:
            existing_pid = 0

        if _pid_is_running(existing_pid):
            return False, f"{lock_label} is already running (PID {existing_pid})."

        try:
            os.remove(lock_path)
        except OSError:
            pass

    with open(lock_path, "w", encoding="utf-8") as f:
        f.write(str(os.getpid()))

    _ACQUIRED_LOCK_FILES.append(lock_path)
    _register_cleanup_once()
    return True, ""


def acquire_process_locks(
    project_lock_path=None,
    app_lock_path=None,
    project_label="Another project process",
    app_label="Another app process",
):
    """
    Acquire optional project and app lock files.
    Returns (ok: bool, message: str).
    """
    if project_lock_path:
        ok, msg = _acquire_pid_lock(project_lock_path, project_label)
        if not ok:
            return False, msg

    if app_lock_path:
        ok, msg = _acquire_pid_lock(app_lock_path, app_label)
        if not ok:
            return False, msg

    return True, ""
