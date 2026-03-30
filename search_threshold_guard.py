#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import time
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Dict, List, Optional, Sequence

try:
    import psutil
except ImportError as exc:  # pragma: no cover - dependency missing in runtime only
    psutil = None
    PSUTIL_IMPORT_ERROR = exc
else:
    PSUTIL_IMPORT_ERROR = None


@dataclass
class ThresholdConfig:
    root_path: str = "."
    max_cpu_percent: float = 85.0
    max_memory_percent: float = 80.0
    max_disk_percent: float = 90.0
    max_process_count: int = 600
    max_listening_ports: int = 256
    max_single_process_cpu_percent: float = 25.0
    max_single_process_memory_percent: float = 25.0
    max_single_process_io_mbps: float = 25.0
    warn_only_process_names: Sequence[str] = ("code", "gnome-shell")
    cpu_sample_seconds: float = 0.15
    warn_only: bool = False


@dataclass
class ProcessSnapshot:
    pid: int
    name: str
    username: str
    cpu_percent: float
    memory_percent: float
    io_mb_per_sec: float


@dataclass
class ThresholdSnapshot:
    root_path: str
    cpu_percent: float
    memory_percent: float
    disk_percent: float
    process_count: int
    listening_ports: List[int]
    logical_cpu_cores: int
    physical_cpu_cores: Optional[int]
    total_memory_mb: int
    disk_total_gb: float
    current_username: str
    user_process_count: int
    top_user_processes: List[ProcessSnapshot]


def _env_float(name: str, default: float) -> float:
    raw = os.getenv(name, "").strip()
    if not raw:
        return default
    try:
        return float(raw)
    except ValueError:
        return default


def _env_int(name: str, default: int) -> int:
    raw = os.getenv(name, "").strip()
    if not raw:
        return default
    try:
        return int(raw)
    except ValueError:
        return default


def _env_csv(name: str, default: Sequence[str]) -> List[str]:
    raw = os.getenv(name, "").strip()
    if not raw:
        return list(default)
    if raw.lower() in {"none", "off", "false", "0"}:
        return []
    return [item.strip() for item in raw.split(",") if item.strip()]


def _env_bool(name: str, default: bool = False) -> bool:
    raw = os.getenv(name, "").strip().lower()
    if not raw:
        return default
    return raw in {"1", "true", "yes", "on"}


def load_config_from_env(root_path: str = ".") -> ThresholdConfig:
    return ThresholdConfig(
        root_path=root_path,
        max_cpu_percent=_env_float("SEARCH_MAX_CPU_PERCENT", 85.0),
        max_memory_percent=_env_float("SEARCH_MAX_MEMORY_PERCENT", 80.0),
        max_disk_percent=_env_float("SEARCH_MAX_DISK_PERCENT", 90.0),
        max_process_count=_env_int("SEARCH_MAX_PROCESS_COUNT", 600),
        max_listening_ports=_env_int("SEARCH_MAX_LISTENING_PORTS", 256),
        max_single_process_cpu_percent=_env_float("SEARCH_MAX_SINGLE_PROCESS_CPU_PERCENT", 25.0),
        max_single_process_memory_percent=_env_float("SEARCH_MAX_SINGLE_PROCESS_MEMORY_PERCENT", 25.0),
        max_single_process_io_mbps=_env_float("SEARCH_MAX_SINGLE_PROCESS_IO_MBPS", 25.0),
        warn_only_process_names=_env_csv("SEARCH_WARN_ONLY_PROCESS_NAMES", ("code", "gnome-shell")),
        cpu_sample_seconds=_env_float("SEARCH_CPU_SAMPLE_SECONDS", 0.15),
        warn_only=_env_bool("SEARCH_THRESHOLD_WARN_ONLY", False),
    )


def _ensure_psutil() -> None:
    if psutil is None:  # pragma: no cover - runtime dependency check
        raise RuntimeError(
            "psutil is required for threshold checks. "
            "Install dependencies with: pip install -r requirements.txt"
        ) from PSUTIL_IMPORT_ERROR


def _current_username() -> str:
    _ensure_psutil()
    try:
        return psutil.Process().username()
    except Exception:  # pragma: no cover - best effort only
        return os.getenv("USER") or os.getenv("USERNAME") or "unknown"


def collect_user_process_samples(config: ThresholdConfig) -> List[ProcessSnapshot]:
    """Sample the current user's processes and compute CPU / memory / disk-I/O usage."""
    _ensure_psutil()

    username = _current_username()
    baseline: Dict[int, Dict[str, float | str]] = {}

    for proc in psutil.process_iter(["pid", "name", "username"]):
        try:
            info = proc.info
            if info.get("username") != username:
                continue

            cpu_times = proc.cpu_times()
            io_counters = proc.io_counters()
            baseline[info["pid"]] = {
                "name": info.get("name") or f"pid-{info['pid']}",
                "cpu_time": float(cpu_times.user + cpu_times.system),
                "io_bytes": float((io_counters.read_bytes if io_counters else 0) + (io_counters.write_bytes if io_counters else 0)),
            }
        except (psutil.AccessDenied, psutil.NoSuchProcess, psutil.ZombieProcess):  # pragma: no cover - host dependent
            continue

    sample_started = time.monotonic()
    psutil.cpu_percent(interval=max(0.0, config.cpu_sample_seconds))
    elapsed = max(time.monotonic() - sample_started, 0.001)

    samples: List[ProcessSnapshot] = []
    for pid, base in baseline.items():
        try:
            proc = psutil.Process(pid)
            cpu_times = proc.cpu_times()
            io_counters = proc.io_counters()
            cpu_time = float(cpu_times.user + cpu_times.system)
            io_bytes = float((io_counters.read_bytes if io_counters else 0) + (io_counters.write_bytes if io_counters else 0))
            memory_percent = float(proc.memory_percent())
            cpu_percent = max(0.0, (cpu_time - float(base["cpu_time"])) / elapsed * 100.0)
            io_mb_per_sec = max(0.0, (io_bytes - float(base["io_bytes"])) / elapsed / (1024 * 1024))
            samples.append(
                ProcessSnapshot(
                    pid=pid,
                    name=str(base["name"]),
                    username=username,
                    cpu_percent=cpu_percent,
                    memory_percent=memory_percent,
                    io_mb_per_sec=io_mb_per_sec,
                )
            )
        except (psutil.AccessDenied, psutil.NoSuchProcess, psutil.ZombieProcess):  # pragma: no cover - host dependent
            continue

    samples.sort(key=lambda proc: (proc.cpu_percent, proc.io_mb_per_sec, proc.memory_percent), reverse=True)
    return samples


def collect_snapshot(config: ThresholdConfig) -> ThresholdSnapshot:
    _ensure_psutil()

    cpu_percent = float(psutil.cpu_percent(interval=max(0.0, config.cpu_sample_seconds)))
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage(str(Path(config.root_path).resolve()))
    process_count = len(psutil.pids())
    user_processes = collect_user_process_samples(config)

    listening_ports = set()
    try:
        connections = psutil.net_connections(kind="inet")
    except (psutil.AccessDenied, psutil.ZombieProcess):  # pragma: no cover - depends on host permissions
        connections = []

    for connection in connections:
        if connection.status != psutil.CONN_LISTEN or connection.laddr is None:
            continue
        port = getattr(connection.laddr, "port", None)
        if port is not None:
            listening_ports.add(int(port))

    return ThresholdSnapshot(
        root_path=str(Path(config.root_path).resolve()),
        cpu_percent=cpu_percent,
        memory_percent=float(memory.percent),
        disk_percent=float(disk.percent),
        process_count=process_count,
        listening_ports=sorted(listening_ports),
        logical_cpu_cores=psutil.cpu_count(logical=True) or 0,
        physical_cpu_cores=psutil.cpu_count(logical=False),
        total_memory_mb=int(memory.total / (1024 * 1024)),
        disk_total_gb=float(disk.total / (1024 * 1024 * 1024)),
        current_username=_current_username(),
        user_process_count=len(user_processes),
        top_user_processes=user_processes[:10],
    )


def _matches_warn_only_process(name: str, allowlist: Sequence[str]) -> bool:
    normalized = name.strip().lower()
    for item in allowlist:
        candidate = item.strip().lower()
        if not candidate:
            continue
        if normalized == candidate or normalized.startswith(candidate):
            return True
    return False


def evaluate_snapshot(snapshot: ThresholdSnapshot, config: ThresholdConfig) -> tuple[List[str], List[str]]:
    issues: List[str] = []
    warnings: List[str] = []

    if snapshot.cpu_percent > config.max_cpu_percent:
        issues.append(
            f"CPU usage {snapshot.cpu_percent:.1f}% exceeds threshold {config.max_cpu_percent:.1f}%"
        )
    if snapshot.memory_percent > config.max_memory_percent:
        issues.append(
            f"Memory usage {snapshot.memory_percent:.1f}% exceeds threshold {config.max_memory_percent:.1f}%"
        )
    if snapshot.disk_percent > config.max_disk_percent:
        issues.append(
            f"Disk usage {snapshot.disk_percent:.1f}% exceeds threshold {config.max_disk_percent:.1f}%"
        )
    if snapshot.process_count > config.max_process_count:
        issues.append(
            f"Process count {snapshot.process_count} exceeds threshold {config.max_process_count}"
        )
    if len(snapshot.listening_ports) > config.max_listening_ports:
        issues.append(
            f"Listening port count {len(snapshot.listening_ports)} exceeds threshold {config.max_listening_ports}"
        )

    for proc in snapshot.top_user_processes:
        warn_only_process = _matches_warn_only_process(proc.name, config.warn_only_process_names)
        bucket = warnings if warn_only_process else issues
        if proc.cpu_percent > config.max_single_process_cpu_percent:
            bucket.append(
                f"Process {proc.name} (pid {proc.pid}) CPU {proc.cpu_percent:.1f}% exceeds per-process threshold {config.max_single_process_cpu_percent:.1f}%"
            )
        if proc.memory_percent > config.max_single_process_memory_percent:
            bucket.append(
                f"Process {proc.name} (pid {proc.pid}) memory {proc.memory_percent:.1f}% exceeds per-process threshold {config.max_single_process_memory_percent:.1f}%"
            )
        if proc.io_mb_per_sec > config.max_single_process_io_mbps:
            bucket.append(
                f"Process {proc.name} (pid {proc.pid}) disk I/O {proc.io_mb_per_sec:.1f} MB/s exceeds per-process threshold {config.max_single_process_io_mbps:.1f} MB/s"
            )

    return issues, warnings


def format_snapshot(snapshot: ThresholdSnapshot, config: ThresholdConfig) -> List[str]:
    ports_preview = ", ".join(str(port) for port in snapshot.listening_ports[:8]) or "none"
    if len(snapshot.listening_ports) > 8:
        ports_preview += ", ..."

    hardware_text = (
        f"{snapshot.logical_cpu_cores} logical cores"
        + (
            f", {snapshot.physical_cpu_cores} physical cores"
            if snapshot.physical_cpu_cores is not None
            else ""
        )
        + f", {snapshot.total_memory_mb} MB RAM, {snapshot.disk_total_gb:.1f} GB disk"
    )

    return [
        f"Root: {snapshot.root_path}",
        f"User: {snapshot.current_username}",
        f"CPU: {snapshot.cpu_percent:.1f}%",
        f"Memory: {snapshot.memory_percent:.1f}%",
        f"Disk: {snapshot.disk_percent:.1f}%",
        f"Processes: {snapshot.process_count}",
        f"User processes: {snapshot.user_process_count}",
        f"Listening ports: {len(snapshot.listening_ports)} [{ports_preview}]",
        f"Hardware: {hardware_text}",
        f"Per-process caps: CPU {config.max_single_process_cpu_percent:.1f}%, memory {config.max_single_process_memory_percent:.1f}%, disk I/O {config.max_single_process_io_mbps:.1f} MB/s",
        *(
            [
        "Top user processes:",
        *[
                    f"  - pid {proc.pid} {proc.name}: CPU {proc.cpu_percent:.1f}% | RAM {proc.memory_percent:.1f}% | disk I/O {proc.io_mb_per_sec:.1f} MB/s"
                    for proc in snapshot.top_user_processes[:3]
                ],
            ]
            if snapshot.top_user_processes
            else []
        ),
        (
            f"Warn-only processes: {', '.join(config.warn_only_process_names) if config.warn_only_process_names else 'none'}"
        ),
    ]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog=Path(sys.argv[0]).name,
        description="Check local CPU, memory, disk, process, and listening-port thresholds before running internet search jobs.",
    )
    parser.add_argument("--root", default=".", help="Filesystem root to measure disk usage against")
    parser.add_argument("--max-cpu-percent", type=float, default=None, help="Maximum allowed CPU percent")
    parser.add_argument("--max-memory-percent", type=float, default=None, help="Maximum allowed memory percent")
    parser.add_argument("--max-disk-percent", type=float, default=None, help="Maximum allowed disk usage percent")
    parser.add_argument("--max-process-count", type=int, default=None, help="Maximum allowed running process count")
    parser.add_argument("--max-listening-ports", type=int, default=None, help="Maximum allowed listening port count")
    parser.add_argument("--max-single-process-cpu-percent", type=float, default=None, help="Maximum allowed CPU percent for any single current-user process")
    parser.add_argument("--max-single-process-memory-percent", type=float, default=None, help="Maximum allowed memory percent for any single current-user process")
    parser.add_argument("--max-single-process-io-mbps", type=float, default=None, help="Maximum allowed disk I/O rate in MB/s for any single current-user process")
    parser.add_argument("--cpu-sample-seconds", type=float, default=None, help="Seconds to sample CPU usage")
    parser.add_argument("--warn-only", action="store_true", help="Print warnings but exit successfully")
    parser.add_argument("--json", action="store_true", help="Print the snapshot and evaluation as JSON")
    return parser


def run_guard(args: argparse.Namespace) -> int:
    config = load_config_from_env(root_path=args.root)
    if args.max_cpu_percent is not None:
        config.max_cpu_percent = args.max_cpu_percent
    if args.max_memory_percent is not None:
        config.max_memory_percent = args.max_memory_percent
    if args.max_disk_percent is not None:
        config.max_disk_percent = args.max_disk_percent
    if args.max_process_count is not None:
        config.max_process_count = args.max_process_count
    if args.max_listening_ports is not None:
        config.max_listening_ports = args.max_listening_ports
    if args.max_single_process_cpu_percent is not None:
        config.max_single_process_cpu_percent = args.max_single_process_cpu_percent
    if args.max_single_process_memory_percent is not None:
        config.max_single_process_memory_percent = args.max_single_process_memory_percent
    if args.max_single_process_io_mbps is not None:
        config.max_single_process_io_mbps = args.max_single_process_io_mbps
    if args.cpu_sample_seconds is not None:
        config.cpu_sample_seconds = args.cpu_sample_seconds
    if args.warn_only:
        config.warn_only = True

    snapshot = collect_snapshot(config)
    issues, warnings = evaluate_snapshot(snapshot, config)
    reported_issues = list(issues)
    reported_warnings = list(warnings)

    if config.warn_only:
        reported_warnings.extend(reported_issues)
        reported_issues = []

    if args.json:
        payload = {
            "snapshot": asdict(snapshot),
            "thresholds": asdict(config),
            "issues": reported_issues,
            "warnings": reported_warnings,
            "status": (
                "warn"
                if reported_warnings
                else ("blocked" if reported_issues else "ok")
            ),
        }
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print("System threshold guard")
        print("-" * 40)
        for line in format_snapshot(snapshot, config):
            print(line)
        if reported_warnings:
            print("\nThreshold warnings:")
            for warning in reported_warnings:
                print(f"- {warning}")
        if reported_issues:
            print("\nThreshold issues:")
            for issue in reported_issues:
                print(f"- {issue}")
        else:
            print("\nThreshold status: warn" if reported_warnings else "\nThreshold status: ok")

    if reported_issues and not config.warn_only:
        return 1
    return 0


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return run_guard(args)
    except Exception as exc:  # pragma: no cover - CLI guard
        print(f"threshold guard error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
