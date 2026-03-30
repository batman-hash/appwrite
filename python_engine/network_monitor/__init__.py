"""
Network Monitor Module for DevNavigator

Provides multiple packet capture and network monitoring capabilities:
- User-space High-Level APIs (Scapy, PyShark)
- Raw Socket Interfaces (AF_PACKET, SOCK_RAW)
- libpcap Wrappers (pcapy, pylibpcap, PyPcap)
- Kernel-Level via eBPF (BCC, libbpf)
- Command-Line Bridging (TShark, tcpdump subprocess)
- Packet Filtering Queues (NetfilterQueue)
"""

from .scapy_capture import ScapyCapture
from .raw_socket_capture import RawSocketCapture
from .libpcap_capture import LibpcapCapture
from .ebpf_capture import EBpfCapture
from .cli_capture import CliCapture
from .netfilter_capture import NetfilterCapture
from .packet_analyzer import PacketAnalyzer
from .network_monitor import NetworkMonitor

__all__ = [
    'ScapyCapture',
    'RawSocketCapture',
    'LibpcapCapture',
    'EBpfCapture',
    'CliCapture',
    'NetfilterCapture',
    'PacketAnalyzer',
    'NetworkMonitor',
]
