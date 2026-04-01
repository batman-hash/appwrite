#!/usr/bin/env python3
"""
Secure byte transfer over a TLS socket.

This module gives us a small, explicit client/server transport layer for
moving bytes from a server to a client with:

- TLS encryption
- optional mutual TLS client certificates
- chunked delivery with ACK/NACK retries
- end-to-end SHA-256 verification
- optional packet-loss probing via Scapy, with a ping fallback
- optional loopback packet capture of the TLS socket traffic with Scapy
- CPU-side transfer tuning via sequential reads, larger socket buffers, and TCP_NODELAY

The goal is not to guarantee that the network itself never drops a packet.
The goal is to guarantee that the client only accepts data after it has been
verified and retransmitted until the payload matches exactly.

Examples:

    # Server
    python3 -m backend.secure_transfer server \
        --file ./assets/sample.wav \
        --cert ./certs/server.crt \
        --key ./certs/server.key \
        --host 0.0.0.0 --port 9443

    # Client
    python3 -m backend.secure_transfer client \
        --host 127.0.0.1 --port 9443 \
        --cafile ./certs/server.crt \
        --server-name localhost \
        --output ./downloaded_sample.wav

    # Loss probe
    python3 -m backend.secure_transfer probe-loss --host 127.0.0.1

    # Loopback capture for a localhost server socket
    python3 -m backend.secure_transfer server \
        --file ./assets/sample.wav \
        --cert ./certs/server.crt \
        --key ./certs/server.key \
        --host 127.0.0.1 --port 9443 \
        --loopback-monitor --loopback-iface lo
"""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import logging
import math
import os
import socket
import ssl
import struct
import subprocess
import threading
import time
from dataclasses import dataclass, asdict, field
from pathlib import Path
from typing import Callable, Optional, Tuple


LOGGER = logging.getLogger(__name__)
DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 9443
DEFAULT_CHUNK_SIZE = 64 * 1024
DEFAULT_ACK_TIMEOUT = 10.0
DEFAULT_SOCKET_BUFFER_SIZE = 2 * 1024 * 1024
MAX_FRAME_SIZE = 128 * 1024 * 1024

FRAME_JSON = 1
FRAME_BYTES = 2


@dataclass
class TransferStats:
    bytes_sent: int = 0
    bytes_received: int = 0
    chunks_sent: int = 0
    chunks_received: int = 0
    retransmissions: int = 0
    mismatched_chunks: int = 0
    loss_percentage: float = 0.0
    verified: bool = False
    sha256: str = ""
    filename: str = ""
    peer: str = ""
    loopback_capture: Optional["LoopbackCaptureSummary"] = None


@dataclass
class LossProbeResult:
    method: str
    sent: int
    received: int
    loss_percentage: float


@dataclass
class LoopbackPacketRecord:
    index: int
    timestamp: float
    direction: str
    src: str
    dst: str
    sport: int
    dport: int
    flags: str
    payload_len: int
    payload_hex: str
    payload_truncated: bool = False


@dataclass
class LoopbackCaptureSummary:
    host: str
    port: int
    iface: str
    packets_seen: int = 0
    payload_packets: int = 0
    payload_bytes: int = 0
    records: list[LoopbackPacketRecord] = field(default_factory=list)


def _read_exact(sock: socket.socket, size: int) -> bytes:
    buf = bytearray()
    while len(buf) < size:
        chunk = sock.recv(size - len(buf))
        if not chunk:
            raise ConnectionError("Socket closed while reading frame data.")
        buf.extend(chunk)
    return bytes(buf)


def _send_frame(sock: socket.socket, frame_type: int, payload: bytes) -> None:
    if len(payload) > MAX_FRAME_SIZE:
        raise ValueError(f"Frame too large: {len(payload)} bytes")
    header = struct.pack("!BI", frame_type, len(payload))
    sock.sendall(header + payload)


def _recv_frame(sock: socket.socket) -> Tuple[int, bytes]:
    header = _read_exact(sock, 5)
    frame_type, size = struct.unpack("!BI", header)
    if size > MAX_FRAME_SIZE:
        raise ValueError(f"Frame too large: {size} bytes")
    return frame_type, _read_exact(sock, size)


def _send_json(sock: socket.socket, payload: dict) -> None:
    encoded = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8")
    _send_frame(sock, FRAME_JSON, encoded)


def _recv_json(sock: socket.socket) -> dict:
    frame_type, payload = _recv_frame(sock)
    if frame_type != FRAME_JSON:
        raise ValueError(f"Expected JSON frame, got frame type {frame_type}")
    return json.loads(payload.decode("utf-8"))


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _sha256_stream(stream_factory: Callable[[], io.BufferedReader], chunk_size: int) -> str:
    digest = hashlib.sha256()
    with stream_factory() as stream:
        while True:
            chunk = stream.read(chunk_size)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


def _measure_source(stream_factory: Callable[[], io.BufferedReader], chunk_size: int) -> Tuple[int, int, str]:
    digest = hashlib.sha256()
    total_bytes = 0

    with stream_factory() as stream:
        while True:
            chunk = stream.read(chunk_size)
            if not chunk:
                break
            if not isinstance(chunk, (bytes, bytearray)):
                chunk = bytes(chunk or b"")
            else:
                chunk = bytes(chunk)
            total_bytes += len(chunk)
            digest.update(chunk)

    total_chunks = 0 if total_bytes == 0 else math.ceil(total_bytes / chunk_size)
    return total_bytes, total_chunks, digest.hexdigest()


def _tune_socket(sock: socket.socket, buffer_size: int = DEFAULT_SOCKET_BUFFER_SIZE, tcp_nodelay: bool = True) -> None:
    try:
        if buffer_size > 0:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, buffer_size)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, buffer_size)
        if tcp_nodelay and hasattr(socket, "TCP_NODELAY"):
            sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
    except OSError as exc:
        LOGGER.debug("Socket tuning skipped: %s", exc)


def _build_server_context(
    cert_file: str,
    key_file: str,
    ca_file: Optional[str] = None,
    require_client_cert: bool = False,
) -> ssl.SSLContext:
    cert_path = Path(cert_file).expanduser().resolve()
    key_path = Path(key_file).expanduser().resolve()
    if not cert_path.exists():
        raise FileNotFoundError(f"Server certificate not found: {cert_path}")
    if not key_path.exists():
        raise FileNotFoundError(f"Server key not found: {key_path}")

    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.minimum_version = getattr(ssl.TLSVersion, "TLSv1_2", None) or ssl.TLSVersion.MINIMUM_SUPPORTED
    context.load_cert_chain(certfile=str(cert_path), keyfile=str(key_path))

    if require_client_cert:
        if not ca_file:
            raise ValueError("--require-client-cert needs --ca-file for client verification.")
        ca_path = Path(ca_file).expanduser().resolve()
        if not ca_path.exists():
            raise FileNotFoundError(f"Client CA file not found: {ca_path}")
        context.verify_mode = ssl.CERT_REQUIRED
        context.load_verify_locations(cafile=str(ca_path))

    return context


def _build_client_context(
    cafile: Optional[str] = None,
    cert_file: Optional[str] = None,
    key_file: Optional[str] = None,
    insecure: bool = False,
) -> ssl.SSLContext:
    if insecure:
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
    else:
        context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
        if cafile:
            ca_path = Path(cafile).expanduser().resolve()
            if not ca_path.exists():
                raise FileNotFoundError(f"CA file not found: {ca_path}")
            context.load_verify_locations(cafile=str(ca_path))

    if cert_file or key_file:
        if not (cert_file and key_file):
            raise ValueError("Client cert and key must be provided together.")
        cert_path = Path(cert_file).expanduser().resolve()
        key_path = Path(key_file).expanduser().resolve()
        if not cert_path.exists():
            raise FileNotFoundError(f"Client certificate not found: {cert_path}")
        if not key_path.exists():
            raise FileNotFoundError(f"Client key not found: {key_path}")
        context.load_cert_chain(certfile=str(cert_path), keyfile=str(key_path))

    return context


def _probe_loss_with_scapy(host: str, count: int = 6, timeout: float = 1.0) -> Optional[LossProbeResult]:
    try:
        from scapy.all import ICMP, IP, sr1  # type: ignore
    except Exception:
        return None

    replies = 0
    for seq in range(count):
        packet = IP(dst=host) / ICMP(seq=seq)
        response = sr1(packet, timeout=timeout, verbose=False)
        if response is not None:
            replies += 1

    loss = 0.0 if count <= 0 else ((count - replies) / count) * 100.0
    return LossProbeResult(method="scapy", sent=count, received=replies, loss_percentage=loss)


def _probe_loss_with_ping(host: str, count: int = 6, timeout: float = 1.0) -> LossProbeResult:
    command = [
        "ping",
        "-c",
        str(count),
        "-W",
        str(max(1, int(math.ceil(timeout)))),
        host,
    ]
    result = subprocess.run(command, capture_output=True, text=True)
    if result.returncode != 0:
        detail = (result.stderr or result.stdout or "").strip()
        raise RuntimeError(f"ping loss probe failed: {detail or 'unknown error'}")

    sent = received = None
    for line in result.stdout.splitlines():
        if "packets transmitted" in line and "packet loss" in line:
            parts = [part.strip() for part in line.split(",")]
            try:
                sent = int(parts[0].split()[0])
                received = int(parts[1].split()[0])
                break
            except Exception:
                continue

    if sent is None or received is None:
        raise RuntimeError(f"Unable to parse ping output:\n{result.stdout.strip()}")

    loss = 0.0 if sent <= 0 else ((sent - received) / sent) * 100.0
    return LossProbeResult(method="ping", sent=sent, received=received, loss_percentage=loss)


def probe_loss(host: str, count: int = 6, timeout: float = 1.0) -> LossProbeResult:
    result = _probe_loss_with_scapy(host, count=count, timeout=timeout)
    if result is not None:
        return result
    return _probe_loss_with_ping(host, count=count, timeout=timeout)


def _build_loopback_record(
    packet: object,
    port: int,
    packet_index: int,
    payload_preview_bytes: int,
) -> Optional[LoopbackPacketRecord]:
    try:
        from scapy.layers.inet import IP, TCP  # type: ignore
    except Exception:
        return None

    try:
        from scapy.layers.inet6 import IPv6  # type: ignore
    except Exception:
        IPv6 = None  # type: ignore

    tcp = None
    try:
        tcp = packet[TCP]  # type: ignore[index]
    except Exception:
        return None

    ip_layer = None
    try:
        ip_layer = packet.getlayer(IP)
    except Exception:
        ip_layer = None
    if ip_layer is None and IPv6 is not None:
        try:
            ip_layer = packet.getlayer(IPv6)
        except Exception:
            ip_layer = None
    if ip_layer is None:
        return None

    payload = bytes(getattr(tcp, "payload", b"") or b"")
    if not payload:
        return None

    sport = int(getattr(tcp, "sport", 0) or 0)
    dport = int(getattr(tcp, "dport", 0) or 0)
    if dport == port:
        direction = "client->server"
    elif sport == port:
        direction = "server->client"
    else:
        direction = "unknown"

    preview = payload[: max(0, int(payload_preview_bytes))]
    return LoopbackPacketRecord(
        index=packet_index,
        timestamp=float(getattr(packet, "time", time.time())),
        direction=direction,
        src=str(getattr(ip_layer, "src", "")),
        dst=str(getattr(ip_layer, "dst", "")),
        sport=sport,
        dport=dport,
        flags=str(getattr(tcp, "flags", "")),
        payload_len=len(payload),
        payload_hex=preview.hex(),
        payload_truncated=len(preview) < len(payload),
    )


class LoopbackCaptureSession:
    def __init__(
        self,
        host: str,
        port: int,
        iface: str = "lo",
        payload_preview_bytes: int = 96,
        max_records: int = 256,
    ):
        self.host = host
        self.port = int(port)
        self.iface = iface
        self.payload_preview_bytes = max(0, int(payload_preview_bytes))
        self.max_records = max(0, int(max_records))
        self.summary = LoopbackCaptureSummary(host=host, port=self.port, iface=iface)
        self._sniffer = None
        self._lock = threading.Lock()

    def _load_sniffer(self):
        try:
            from scapy.all import AsyncSniffer  # type: ignore
        except Exception as exc:
            raise RuntimeError("Scapy is required for loopback capture.") from exc
        return AsyncSniffer

    def _handle_packet(self, packet: object) -> None:
        with self._lock:
            self.summary.packets_seen += 1
            record_index = self.summary.payload_packets + 1

        record = _build_loopback_record(packet, self.port, record_index, self.payload_preview_bytes)
        if record is None:
            return

        with self._lock:
            self.summary.payload_packets += 1
            self.summary.payload_bytes += record.payload_len
            if self.max_records == 0 or len(self.summary.records) < self.max_records:
                self.summary.records.append(record)

    def start(self) -> "LoopbackCaptureSession":
        if self._sniffer is not None:
            return self

        AsyncSniffer = self._load_sniffer()
        self._sniffer = AsyncSniffer(
            iface=self.iface,
            filter=f"tcp and port {self.port}",
            prn=self._handle_packet,
            store=False,
        )
        self._sniffer.start()
        time.sleep(0.1)
        return self

    def stop(self) -> LoopbackCaptureSummary:
        sniffer = self._sniffer
        self._sniffer = None
        if sniffer is not None:
            try:
                sniffer.stop()
            except Exception as exc:
                LOGGER.warning("Loopback sniffer stop failed: %s", exc)
        return self.summary


class SecureTransferServer:
    def __init__(
        self,
        host: str,
        port: int,
        cert_file: str,
        key_file: str,
        ca_file: Optional[str] = None,
        require_client_cert: bool = False,
        chunk_size: int = DEFAULT_CHUNK_SIZE,
        ack_timeout: float = DEFAULT_ACK_TIMEOUT,
        max_retries: int = 5,
        socket_buffer_size: int = DEFAULT_SOCKET_BUFFER_SIZE,
        tcp_nodelay: bool = True,
        loopback_monitor: bool = False,
        loopback_iface: str = "lo",
        loopback_payload_preview_bytes: int = 96,
        loopback_max_records: int = 256,
    ):
        self.host = host
        self.port = port
        self.chunk_size = max(1024, int(chunk_size))
        self.ack_timeout = float(ack_timeout)
        self.max_retries = max(1, int(max_retries))
        self.socket_buffer_size = max(0, int(socket_buffer_size))
        self.tcp_nodelay = bool(tcp_nodelay)
        self.loopback_monitor = bool(loopback_monitor)
        self.loopback_iface = loopback_iface
        self.loopback_payload_preview_bytes = max(0, int(loopback_payload_preview_bytes))
        self.loopback_max_records = max(0, int(loopback_max_records))
        self.context = _build_server_context(
            cert_file=cert_file,
            key_file=key_file,
            ca_file=ca_file,
            require_client_cert=require_client_cert,
        )

    def _serve_source(
        self,
        source_factory: Callable[[], io.BufferedReader],
        source_name: str,
        once: bool = False,
    ) -> TransferStats:
        total_bytes, total_chunks, sha256 = _measure_source(source_factory, self.chunk_size)

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
            server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server_socket.bind((self.host, self.port))
            server_socket.listen(1)
            LOGGER.info("Secure transfer server listening on %s:%s", self.host, self.port)
            LOGGER.info("Serving %s (%s bytes, %s chunks)", source_name, total_bytes, total_chunks)
            if self.loopback_monitor:
                LOGGER.info(
                    "Loopback capture enabled on iface=%s for tcp port %s",
                    self.loopback_iface,
                    self.port,
                )

            while True:
                capture_session = None
                if self.loopback_monitor:
                    capture_session = LoopbackCaptureSession(
                        host=self.host,
                        port=self.port,
                        iface=self.loopback_iface,
                        payload_preview_bytes=self.loopback_payload_preview_bytes,
                        max_records=self.loopback_max_records,
                    ).start()

                stats = None
                try:
                    raw_conn, addr = server_socket.accept()
                    _tune_socket(raw_conn, self.socket_buffer_size, self.tcp_nodelay)
                    stats = TransferStats(filename=source_name, peer=f"{addr[0]}:{addr[1]}", sha256=sha256)
                    LOGGER.info("Accepted secure transfer client from %s", stats.peer)
                    with self.context.wrap_socket(raw_conn, server_side=True) as conn:
                        conn.settimeout(self.ack_timeout)
                        self._serve_one_connection(
                            conn=conn,
                            source_factory=source_factory,
                            source_name=source_name,
                            total_bytes=total_bytes,
                            total_chunks=total_chunks,
                            sha256=sha256,
                            stats=stats,
                        )
                finally:
                    if capture_session is not None:
                        capture_summary = capture_session.stop()
                        if stats is not None:
                            stats.loopback_capture = capture_summary

                if stats is None:
                    continue

                LOGGER.info("Transfer finished for %s", stats.peer)
                LOGGER.info("Transfer stats: %s", json.dumps(asdict(stats), sort_keys=True))
                if once:
                    return stats

    def _serve_one_connection(
        self,
        conn: socket.socket,
        source_factory: Callable[[], io.BufferedReader],
        source_name: str,
        total_bytes: int,
        total_chunks: int,
        sha256: str,
        stats: TransferStats,
    ) -> None:
        manifest = {
            "type": "manifest",
            "filename": source_name,
            "size": total_bytes,
            "chunks": total_chunks,
            "chunk_size": self.chunk_size,
            "sha256": sha256,
            "protocol": "secure-transfer-v1",
        }
        _send_json(conn, manifest)
        ready = _recv_json(conn)
        if ready.get("type") != "ready":
            raise ValueError(f"Client did not send ready frame: {ready}")

        with source_factory() as stream:
            seq = 0
            while True:
                chunk = stream.read(self.chunk_size)
                if not isinstance(chunk, (bytes, bytearray)):
                    chunk = bytes(chunk or b"")
                chunk = bytes(chunk)
                if not chunk:
                    break
                chunk_sha = _sha256_bytes(chunk)
                header = {
                    "type": "chunk",
                    "seq": seq,
                    "size": len(chunk),
                    "sha256": chunk_sha,
                }

                for attempt in range(1, self.max_retries + 1):
                    _send_json(conn, header)
                    _send_frame(conn, FRAME_BYTES, chunk)

                    try:
                        ack = _recv_json(conn)
                    except (TimeoutError, socket.timeout):
                        stats.retransmissions += 1
                        if attempt == self.max_retries:
                            raise TimeoutError(f"No ACK for chunk {seq} after {self.max_retries} attempts")
                        continue

                    ack_type = ack.get("type")
                    ack_seq = ack.get("seq")
                    ack_sha = ack.get("sha256")
                    if ack_type == "ack" and ack_seq == seq and ack_sha == chunk_sha:
                        stats.bytes_sent += len(chunk)
                        stats.chunks_sent += 1
                        break

                    stats.retransmissions += 1
                    if ack_type == "nack":
                        stats.mismatched_chunks += 1

                    if attempt == self.max_retries:
                        raise ValueError(f"Chunk {seq} failed verification after {self.max_retries} attempts: {ack}")
                    time.sleep(0.05)
                seq += 1

        final = _recv_json(conn)
        if final.get("type") != "done":
            raise ValueError(f"Client did not confirm completion: {final}")
        if final.get("sha256") != sha256:
            raise ValueError("Client completion hash did not match server payload hash.")
        if int(final.get("bytes") or 0) != total_bytes:
            raise ValueError("Client completion byte count did not match server payload size.")

        stats.verified = True
        stats.loss_percentage = 0.0 if stats.chunks_sent <= 0 else (stats.retransmissions / max(1, stats.chunks_sent)) * 100.0
        _send_json(
            conn,
            {
                "type": "complete",
                "verified": True,
                "sha256": sha256,
                "bytes": total_bytes,
                "chunks": total_chunks,
            },
        )

    def serve_file(self, path: str, once: bool = False) -> TransferStats:
        file_path = Path(path).expanduser().resolve()
        if not file_path.exists():
            raise FileNotFoundError(f"Source file not found: {file_path}")
        return self._serve_source(lambda: file_path.open("rb"), file_path.name, once=once)

    def serve_bytes(self, payload: bytes, name: str = "payload.bin", once: bool = False) -> TransferStats:
        return self._serve_source(lambda: io.BytesIO(payload), name, once=once)


class SecureTransferClient:
    def __init__(
        self,
        host: str,
        port: int,
        cafile: Optional[str] = None,
        cert_file: Optional[str] = None,
        key_file: Optional[str] = None,
        server_name: Optional[str] = None,
        chunk_size: int = DEFAULT_CHUNK_SIZE,
        insecure: bool = False,
        timeout: float = DEFAULT_ACK_TIMEOUT,
        socket_buffer_size: int = DEFAULT_SOCKET_BUFFER_SIZE,
        tcp_nodelay: bool = True,
    ):
        self.host = host
        self.port = port
        self.server_name = server_name or host
        self.chunk_size = max(1024, int(chunk_size))
        self.timeout = float(timeout)
        self.socket_buffer_size = max(0, int(socket_buffer_size))
        self.tcp_nodelay = bool(tcp_nodelay)
        self.context = _build_client_context(
            cafile=cafile,
            cert_file=cert_file,
            key_file=key_file,
            insecure=insecure,
        )

    def download(self, output_path: str) -> TransferStats:
        output = Path(output_path).expanduser().resolve()
        output.parent.mkdir(parents=True, exist_ok=True)

        with socket.create_connection((self.host, self.port), timeout=self.timeout) as raw_sock:
            _tune_socket(raw_sock, self.socket_buffer_size, self.tcp_nodelay)
            with self.context.wrap_socket(raw_sock, server_hostname=self.server_name) as conn:
                conn.settimeout(self.timeout)
                manifest = _recv_json(conn)
                if manifest.get("type") != "manifest":
                    raise ValueError(f"Expected manifest frame, got: {manifest}")

                filename = str(manifest.get("filename") or output.name)
                total_bytes = int(manifest.get("size") or 0)
                total_chunks = int(manifest.get("chunks") or 0)
                sha256 = str(manifest.get("sha256") or "")
                stats = TransferStats(filename=filename, peer=f"{self.host}:{self.port}", sha256=sha256)

                _send_json(
                    conn,
                    {
                        "type": "ready",
                        "requested_filename": filename,
                        "output_path": str(output),
                    },
                )

                received = bytearray()
                expected_seq = 0
                with output.open("wb") as out_file:
                    while expected_seq < total_chunks:
                        header = _recv_json(conn)
                        if header.get("type") != "chunk":
                            raise ValueError(f"Expected chunk header, got: {header}")

                        seq_value = header.get("seq")
                        size_value = header.get("size")
                        seq = int(seq_value) if seq_value is not None else -1
                        expected_size = int(size_value) if size_value is not None else -1
                        expected_chunk_sha = str(header.get("sha256") or "")

                        frame_type, chunk = _recv_frame(conn)
                        if frame_type != FRAME_BYTES:
                            raise ValueError(f"Expected binary frame, got frame type {frame_type}")

                        actual_size = len(chunk)
                        actual_sha = _sha256_bytes(chunk)
                        if seq != expected_seq or actual_size != expected_size or actual_sha != expected_chunk_sha:
                            stats.retransmissions += 1
                            stats.mismatched_chunks += 1
                            _send_json(
                                conn,
                                {
                                    "type": "nack",
                                    "seq": seq,
                                    "expected_seq": expected_seq,
                                    "reason": "chunk-verification-failed",
                                },
                            )
                            continue

                        out_file.write(chunk)
                        received.extend(chunk)
                        stats.bytes_received += actual_size
                        stats.chunks_received += 1
                        _send_json(
                            conn,
                            {
                                "type": "ack",
                                "seq": seq,
                                "sha256": actual_sha,
                            },
                        )
                        expected_seq += 1

                final_sha = _sha256_bytes(bytes(received))
                verified = final_sha == sha256 and len(received) == total_bytes
                stats.verified = verified
                stats.loss_percentage = 0.0 if stats.chunks_received <= 0 else (stats.retransmissions / max(1, stats.chunks_received)) * 100.0

                _send_json(
                    conn,
                    {
                        "type": "done",
                        "bytes": len(received),
                        "sha256": final_sha,
                        "chunks": stats.chunks_received,
                        "verified": verified,
                    },
                )

                complete = _recv_json(conn)
                if complete.get("type") != "complete":
                    raise ValueError(f"Expected complete frame, got: {complete}")
                if not verified or not complete.get("verified"):
                    raise ValueError("Secure transfer did not verify successfully.")

                LOGGER.info("Downloaded %s to %s", filename, output)
                LOGGER.info("Transfer stats: %s", json.dumps(asdict(stats), sort_keys=True))
                return stats


def _configure_logging(verbosity: int) -> None:
    level = logging.WARNING
    if verbosity >= 2:
        level = logging.DEBUG
    elif verbosity == 1:
        level = logging.INFO

    logging.basicConfig(level=level, format="%(asctime)s - %(levelname)s - %(message)s")


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="TLS secure byte transfer helper.")
    parser.add_argument("-v", "--verbose", action="count", default=0, help="Increase logging verbosity.")

    subparsers = parser.add_subparsers(dest="command", required=True)

    server = subparsers.add_parser("server", help="Run a secure transfer server.")
    server.add_argument("--host", default=os.getenv("SOCKET_HOST", DEFAULT_HOST))
    server.add_argument("--port", type=int, default=int(os.getenv("SOCKET_PORT", str(DEFAULT_PORT))))
    server.add_argument("--file", required=True, help="File to stream to the client.")
    server.add_argument("--cert", default=os.getenv("SSL_CERT_FILE", ""))
    server.add_argument("--key", default=os.getenv("SSL_KEY_FILE", ""))
    server.add_argument("--ca-file", default=os.getenv("SSL_CA_FILE", ""))
    server.add_argument("--require-client-cert", action="store_true")
    server.add_argument("--chunk-size", type=int, default=DEFAULT_CHUNK_SIZE)
    server.add_argument("--ack-timeout", type=float, default=DEFAULT_ACK_TIMEOUT)
    server.add_argument("--max-retries", type=int, default=5)
    server.add_argument(
        "--socket-buffer-size",
        type=int,
        default=DEFAULT_SOCKET_BUFFER_SIZE,
        help="Increase kernel socket buffers to improve transfer throughput.",
    )
    server_tcp = server.add_mutually_exclusive_group()
    server_tcp.add_argument(
        "--tcp-nodelay",
        dest="tcp_nodelay",
        action="store_true",
        help="Disable Nagle's algorithm for lower per-chunk latency.",
    )
    server_tcp.add_argument(
        "--no-tcp-nodelay",
        dest="tcp_nodelay",
        action="store_false",
        help="Keep Nagle's algorithm enabled.",
    )
    server.set_defaults(tcp_nodelay=True)
    server.add_argument("--once", action="store_true", help="Serve one client and exit.")
    server.add_argument(
        "--loopback-monitor",
        action="store_true",
        help="Capture localhost TCP payload bytes on the loopback interface with Scapy while serving.",
    )
    server.add_argument(
        "--loopback-iface",
        default="lo",
        help="Interface used for loopback capture when --loopback-monitor is enabled.",
    )
    server.add_argument(
        "--loopback-payload-preview-bytes",
        type=int,
        default=96,
        help="How many payload bytes to keep in each captured record preview.",
    )
    server.add_argument(
        "--loopback-max-records",
        type=int,
        default=256,
        help="Maximum number of payload records to retain in memory.",
    )

    client = subparsers.add_parser("client", help="Run a secure transfer client.")
    client.add_argument("--host", default=os.getenv("SOCKET_HOST", DEFAULT_HOST))
    client.add_argument("--port", type=int, default=int(os.getenv("SOCKET_PORT", str(DEFAULT_PORT))))
    client.add_argument("--output", required=True, help="Destination path for the downloaded bytes.")
    client.add_argument("--cafile", default=os.getenv("SSL_CA_FILE", ""))
    client.add_argument("--cert", default=os.getenv("SSL_CLIENT_CERT_FILE", ""))
    client.add_argument("--key", default=os.getenv("SSL_CLIENT_KEY_FILE", ""))
    client.add_argument("--server-name", default=os.getenv("SSL_SERVER_NAME", ""))
    client.add_argument("--chunk-size", type=int, default=DEFAULT_CHUNK_SIZE)
    client.add_argument("--timeout", type=float, default=DEFAULT_ACK_TIMEOUT)
    client.add_argument(
        "--socket-buffer-size",
        type=int,
        default=DEFAULT_SOCKET_BUFFER_SIZE,
        help="Increase kernel socket buffers to improve transfer throughput.",
    )
    client_tcp = client.add_mutually_exclusive_group()
    client_tcp.add_argument(
        "--tcp-nodelay",
        dest="tcp_nodelay",
        action="store_true",
        help="Disable Nagle's algorithm for lower per-chunk latency.",
    )
    client_tcp.add_argument(
        "--no-tcp-nodelay",
        dest="tcp_nodelay",
        action="store_false",
        help="Keep Nagle's algorithm enabled.",
    )
    client.set_defaults(tcp_nodelay=True)
    client.add_argument("--insecure", action="store_true", help="Disable certificate verification for local testing.")

    probe = subparsers.add_parser("probe-loss", help="Measure packet loss using Scapy or ping.")
    probe.add_argument("--host", required=True)
    probe.add_argument("--count", type=int, default=6)
    probe.add_argument("--timeout", type=float, default=1.0)

    return parser


def main(argv: Optional[list[str]] = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    _configure_logging(args.verbose)

    if args.command == "server":
        if not args.cert or not args.key:
            parser.error("server mode requires --cert and --key")
        server = SecureTransferServer(
            host=args.host,
            port=args.port,
            cert_file=args.cert,
            key_file=args.key,
            ca_file=args.ca_file or None,
            require_client_cert=args.require_client_cert,
            chunk_size=args.chunk_size,
            ack_timeout=args.ack_timeout,
            max_retries=args.max_retries,
            socket_buffer_size=args.socket_buffer_size,
            tcp_nodelay=args.tcp_nodelay,
            loopback_monitor=args.loopback_monitor,
            loopback_iface=args.loopback_iface,
            loopback_payload_preview_bytes=args.loopback_payload_preview_bytes,
            loopback_max_records=args.loopback_max_records,
        )
        server.serve_file(args.file, once=args.once)
        return 0

    if args.command == "client":
        client = SecureTransferClient(
            host=args.host,
            port=args.port,
            cafile=args.cafile or None,
            cert_file=args.cert or None,
            key_file=args.key or None,
            server_name=args.server_name or None,
            chunk_size=args.chunk_size,
            timeout=args.timeout,
            socket_buffer_size=args.socket_buffer_size,
            tcp_nodelay=args.tcp_nodelay,
            insecure=args.insecure,
        )
        client.download(args.output)
        return 0

    if args.command == "probe-loss":
        result = probe_loss(args.host, count=args.count, timeout=args.timeout)
        print(json.dumps(asdict(result), indent=2, sort_keys=True))
        return 0

    parser.error(f"Unsupported command: {args.command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
