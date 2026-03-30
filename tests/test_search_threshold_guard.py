from types import SimpleNamespace

import search_threshold_guard as guard


def test_evaluate_snapshot_detects_threshold_overages():
    snapshot = guard.ThresholdSnapshot(
        root_path="/workspace",
        cpu_percent=91.2,
        memory_percent=81.4,
        disk_percent=92.0,
        process_count=812,
        listening_ports=[80, 443, 8080],
        logical_cpu_cores=8,
        physical_cpu_cores=4,
        total_memory_mb=16384,
        disk_total_gb=512.0,
        current_username="kali",
        user_process_count=0,
        top_user_processes=[],
    )
    config = guard.ThresholdConfig(
        root_path="/workspace",
        max_cpu_percent=85.0,
        max_memory_percent=80.0,
        max_disk_percent=90.0,
        max_process_count=600,
        max_listening_ports=2,
    )

    issues, warnings = guard.evaluate_snapshot(snapshot, config)

    assert len(issues) == 5
    assert warnings == []
    assert any("CPU usage" in issue for issue in issues)
    assert any("Memory usage" in issue for issue in issues)
    assert any("Disk usage" in issue for issue in issues)
    assert any("Process count" in issue for issue in issues)
    assert any("Listening port count" in issue for issue in issues)


def test_evaluate_snapshot_detects_single_process_overages():
    snapshot = guard.ThresholdSnapshot(
        root_path="/workspace",
        cpu_percent=12.0,
        memory_percent=12.0,
        disk_percent=12.0,
        process_count=12,
        listening_ports=[],
        logical_cpu_cores=8,
        physical_cpu_cores=4,
        total_memory_mb=16384,
        disk_total_gb=512.0,
        current_username="kali",
        user_process_count=1,
        top_user_processes=[
            guard.ProcessSnapshot(
                pid=1234,
                name="worker",
                username="kali",
                cpu_percent=41.5,
                memory_percent=27.2,
                io_mb_per_sec=31.0,
            )
        ],
    )
    config = guard.ThresholdConfig(
        root_path="/workspace",
        max_single_process_cpu_percent=25.0,
        max_single_process_memory_percent=25.0,
        max_single_process_io_mbps=25.0,
    )

    issues, warnings = guard.evaluate_snapshot(snapshot, config)

    assert any("CPU" in issue and "worker" in issue for issue in issues)
    assert any("memory" in issue and "worker" in issue for issue in issues)
    assert any("disk I/O" in issue and "worker" in issue for issue in issues)
    assert warnings == []


def test_evaluate_snapshot_warns_for_allowlisted_process_names():
    snapshot = guard.ThresholdSnapshot(
        root_path="/workspace",
        cpu_percent=12.0,
        memory_percent=12.0,
        disk_percent=12.0,
        process_count=12,
        listening_ports=[],
        logical_cpu_cores=8,
        physical_cpu_cores=4,
        total_memory_mb=16384,
        disk_total_gb=512.0,
        current_username="kali",
        user_process_count=1,
        top_user_processes=[
            guard.ProcessSnapshot(
                pid=77,
                name="code",
                username="kali",
                cpu_percent=41.0,
                memory_percent=27.2,
                io_mb_per_sec=31.0,
            )
        ],
    )
    config = guard.ThresholdConfig(
        root_path="/workspace",
        max_single_process_cpu_percent=25.0,
        max_single_process_memory_percent=25.0,
        max_single_process_io_mbps=25.0,
        warn_only_process_names=("code", "gnome-shell"),
    )

    issues, warnings = guard.evaluate_snapshot(snapshot, config)

    assert issues == []
    assert any("code" in warning for warning in warnings)


def test_main_reports_ok_when_under_thresholds(monkeypatch, capsys, tmp_path):
    monkeypatch.setattr(guard.psutil, "cpu_percent", lambda interval=0.0: 12.5)
    monkeypatch.setattr(
        guard.psutil,
        "virtual_memory",
        lambda: SimpleNamespace(percent=40.0, total=8 * 1024 * 1024 * 1024),
    )
    monkeypatch.setattr(
        guard.psutil,
        "disk_usage",
        lambda path: SimpleNamespace(percent=55.0, total=100 * 1024 * 1024 * 1024),
    )
    monkeypatch.setattr(guard.psutil, "pids", lambda: [1, 2, 3])
    monkeypatch.setattr(
        guard.psutil,
        "net_connections",
        lambda kind="inet": [SimpleNamespace(status=guard.psutil.CONN_LISTEN, laddr=SimpleNamespace(port=80))],
    )
    monkeypatch.setattr(guard.psutil, "cpu_count", lambda logical=True: 8 if logical else 4)
    monkeypatch.setattr(
        guard,
        "collect_user_process_samples",
        lambda config: [
            guard.ProcessSnapshot(
                pid=1,
                name="search-wrapper",
                username="kali",
                cpu_percent=12.0,
                memory_percent=8.0,
                io_mb_per_sec=1.0,
            )
        ],
    )

    exit_code = guard.main(["--root", str(tmp_path)])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Threshold status: ok" in output
    assert "Listening ports: 1" in output


def test_main_blocks_when_thresholds_are_exceeded(monkeypatch, capsys, tmp_path):
    monkeypatch.setattr(guard.psutil, "cpu_percent", lambda interval=0.0: 95.0)
    monkeypatch.setattr(
        guard.psutil,
        "virtual_memory",
        lambda: SimpleNamespace(percent=40.0, total=8 * 1024 * 1024 * 1024),
    )
    monkeypatch.setattr(
        guard.psutil,
        "disk_usage",
        lambda path: SimpleNamespace(percent=55.0, total=100 * 1024 * 1024 * 1024),
    )
    monkeypatch.setattr(guard.psutil, "pids", lambda: [1, 2, 3])
    monkeypatch.setattr(guard.psutil, "net_connections", lambda kind="inet": [])
    monkeypatch.setattr(guard.psutil, "cpu_count", lambda logical=True: 8 if logical else 4)
    monkeypatch.setattr(
        guard,
        "collect_user_process_samples",
        lambda config: [
            guard.ProcessSnapshot(
                pid=2,
                name="busy-worker",
                username="kali",
                cpu_percent=12.0,
                memory_percent=8.0,
                io_mb_per_sec=1.0,
            )
        ],
    )

    exit_code = guard.main([
        "--root",
        str(tmp_path),
        "--max-cpu-percent",
        "50",
    ])

    output = capsys.readouterr().out
    assert exit_code == 1
    assert "CPU usage 95.0% exceeds threshold 50.0%" in output


def test_main_blocks_when_single_process_cpu_exceeds_threshold(monkeypatch, capsys, tmp_path):
    monkeypatch.setattr(guard.psutil, "cpu_percent", lambda interval=0.0: 12.0)
    monkeypatch.setattr(
        guard.psutil,
        "virtual_memory",
        lambda: SimpleNamespace(percent=40.0, total=8 * 1024 * 1024 * 1024),
    )
    monkeypatch.setattr(
        guard.psutil,
        "disk_usage",
        lambda path: SimpleNamespace(percent=55.0, total=100 * 1024 * 1024 * 1024),
    )
    monkeypatch.setattr(guard.psutil, "pids", lambda: [1, 2, 3])
    monkeypatch.setattr(guard.psutil, "net_connections", lambda kind="inet": [])
    monkeypatch.setattr(guard.psutil, "cpu_count", lambda logical=True: 8 if logical else 4)
    monkeypatch.setattr(
        guard,
        "collect_user_process_samples",
        lambda config: [
            guard.ProcessSnapshot(
                pid=99,
                name="primary-search",
                username="kali",
                cpu_percent=41.0,
                memory_percent=9.0,
                io_mb_per_sec=3.0,
            )
        ],
    )

    exit_code = guard.main([
        "--root",
        str(tmp_path),
    ])

    output = capsys.readouterr().out
    assert exit_code == 1
    assert "primary-search" in output
    assert "CPU 41.0% exceeds per-process threshold 25.0%" in output


def test_main_warns_instead_of_blocking_for_allowlisted_editor_process(monkeypatch, capsys, tmp_path):
    monkeypatch.setattr(guard.psutil, "cpu_percent", lambda interval=0.0: 12.0)
    monkeypatch.setattr(
        guard.psutil,
        "virtual_memory",
        lambda: SimpleNamespace(percent=40.0, total=8 * 1024 * 1024 * 1024),
    )
    monkeypatch.setattr(
        guard.psutil,
        "disk_usage",
        lambda path: SimpleNamespace(percent=55.0, total=100 * 1024 * 1024 * 1024),
    )
    monkeypatch.setattr(guard.psutil, "pids", lambda: [1, 2, 3])
    monkeypatch.setattr(guard.psutil, "net_connections", lambda kind="inet": [])
    monkeypatch.setattr(guard.psutil, "cpu_count", lambda logical=True: 8 if logical else 4)
    monkeypatch.setattr(
        guard,
        "collect_user_process_samples",
        lambda config: [
            guard.ProcessSnapshot(
                pid=3,
                name="code",
                username="kali",
                cpu_percent=41.0,
                memory_percent=9.0,
                io_mb_per_sec=3.0,
            )
        ],
    )

    exit_code = guard.main([
        "--root",
        str(tmp_path),
    ])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Threshold warnings:" in output
    assert "code" in output
    assert "Threshold status: warn" in output


def test_main_warn_only_mode_turns_process_overages_into_warnings(monkeypatch, capsys, tmp_path):
    monkeypatch.setattr(guard.psutil, "cpu_percent", lambda interval=0.0: 12.0)
    monkeypatch.setattr(
        guard.psutil,
        "virtual_memory",
        lambda: SimpleNamespace(percent=40.0, total=8 * 1024 * 1024 * 1024),
    )
    monkeypatch.setattr(
        guard.psutil,
        "disk_usage",
        lambda path: SimpleNamespace(percent=55.0, total=100 * 1024 * 1024 * 1024),
    )
    monkeypatch.setattr(guard.psutil, "pids", lambda: [1, 2, 3])
    monkeypatch.setattr(guard.psutil, "net_connections", lambda kind="inet": [])
    monkeypatch.setattr(guard.psutil, "cpu_count", lambda logical=True: 8 if logical else 4)
    monkeypatch.setattr(
        guard,
        "collect_user_process_samples",
        lambda config: [
            guard.ProcessSnapshot(
                pid=4,
                name="worker",
                username="kali",
                cpu_percent=41.0,
                memory_percent=31.0,
                io_mb_per_sec=3.0,
            )
        ],
    )

    exit_code = guard.main([
        "--root",
        str(tmp_path),
        "--warn-only",
    ])

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Threshold warnings:" in output
    assert "Threshold issues:" not in output
    assert "worker" in output
    assert "Threshold status: warn" in output
