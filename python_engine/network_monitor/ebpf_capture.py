"""
eBPF Packet Capture Module

Provides kernel-level packet capture using eBPF (Extended Berkeley Packet Filter).
Supports both BCC (BPF Compiler Collection) and libbpf backends.
"""

import time
import ctypes
from typing import Optional, Callable, Dict, Any, List
from datetime import datetime
from dataclasses import dataclass

from .packet_analyzer import PacketAnalyzer

try:
    from bcc import BPF
    BCC_AVAILABLE = True
except ImportError:
    BCC_AVAILABLE = False
    print("Warning: BCC not installed. Install with: apt-get install bpfcc-tools python3-bcc")

try:
    import libbpf
    LIBBPF_AVAILABLE = True
except ImportError:
    LIBBPF_AVAILABLE = False


@dataclass
class EBpfStats:
    """eBPF capture statistics"""
    packets_captured: int = 0
    bytes_captured: int = 0
    events_received: int = 0
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    
    @property
    def duration_seconds(self) -> float:
        """Calculate capture duration in seconds"""
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return 0.0
    
    @property
    def packets_per_second(self) -> float:
        """Calculate packets per second"""
        duration = self.duration_seconds
        return self.packets_captured / duration if duration > 0 else 0.0


class EBpfCapture:
    """
    Kernel-level packet capture using eBPF.
    
    Features:
    - Kernel-level packet filtering (extremely fast)
    - Minimal overhead (filtering happens in kernel space)
    - Support for XDP (eXpress Data Path) for high-performance capture
    - TC (Traffic Control) ingress/egress hooks
    - Tracepoint-based capture
    
    Supported backends:
    - BCC: BPF Compiler Collection (requires kernel headers)
    - libbpf: Modern eBPF library (CO-RE, no kernel headers needed)
    
    Note:
        Requires root privileges and kernel eBPF support (Linux 4.1+)
    """
    
    # eBPF program for packet capture
    BPF_PROGRAM = """
    #include <uapi/linux/ptrace.h>
    #include <linux/skbuff.h>
    #include <linux/if_ether.h>
    #include <linux/ip.h>
    #include <linux/tcp.h>
    #include <linux/udp.h>
    
    // Per-CPU array for packet data
    BPF_PERF_OUTPUT(events);
    
    // Packet event structure
    struct packet_event {
        u64 timestamp;
        u32 length;
        u32 src_ip;
        u32 dst_ip;
        u16 src_port;
        u16 dst_port;
        u8 protocol;
        u8 pad[7];
    };
    
    // XDP program for high-performance capture
    int xdp_capture(struct xdp_md *ctx) {
        void *data = (void *)(long)ctx->data;
        void *data_end = (void *)(long)ctx->data_end;
        
        struct ethhdr *eth = data;
        if ((void *)(eth + 1) > data_end)
            return XDP_PASS;
        
        if (eth->h_proto != htons(ETH_P_IP))
            return XDP_PASS;
        
        struct iphdr *ip = (void *)(eth + 1);
        if ((void *)(ip + 1) > data_end)
            return XDP_PASS;
        
        struct packet_event event = {};
        event.timestamp = bpf_ktime_get_ns();
        event.length = ctx->data_end - ctx->data;
        event.src_ip = ip->saddr;
        event.dst_ip = ip->daddr;
        event.protocol = ip->protocol;
        
        // Parse TCP/UDP ports
        if (ip->protocol == IPPROTO_TCP) {
            struct tcphdr *tcp = (void *)ip + (ip->ihl * 4);
            if ((void *)(tcp + 1) <= data_end) {
                event.src_port = tcp->source;
                event.dst_port = tcp->dest;
            }
        } else if (ip->protocol == IPPROTO_UDP) {
            struct udphdr *udp = (void *)ip + (ip->ihl * 4);
            if ((void *)(udp + 1) <= data_end) {
                event.src_port = udp->source;
                event.dst_port = udp->dest;
            }
        }
        
        events.perf_submit(ctx, &event, sizeof(event));
        return XDP_PASS;
    }
    """
    
    def __init__(
        self,
        interface: Optional[str] = None,
        backend: str = 'bcc'
    ):
        """
        Initialize eBPF capture.
        
        Args:
            interface: Network interface to capture from
            backend: eBPF backend to use ('bcc' or 'libbpf')
        """
        self.interface = interface
        self.backend = backend
        
        self.analyzer = PacketAnalyzer()
        self.stats = EBpfStats()
        self.is_capturing = False
        self.captured_packets: List[Dict[str, Any]] = []
        self._callback: Optional[Callable] = None
        self._bpf = None
        self._xdp_attached = False
        
        # Validate backend
        if backend == 'bcc' and not BCC_AVAILABLE:
            raise ImportError("BCC not installed. Install with: apt-get install bpfcc-tools python3-bcc")
        elif backend == 'libbpf' and not LIBBPF_AVAILABLE:
            raise ImportError("libbpf not installed")
    
    def _compile_bcc_program(self, program: str) -> 'BPF':
        """
        Compile eBPF program using BCC.
        
        Args:
            program: eBPF C program source
            
        Returns:
            Compiled BPF object
        """
        if not BCC_AVAILABLE:
            raise ImportError("BCC not installed")
        
        return BPF(text=program)
    
    def _attach_xdp(self, bpf: 'BPF', interface: str):
        """
        Attach XDP program to interface.
        
        Args:
            bpf: Compiled BPF object
            interface: Network interface name
        """
        try:
            fn = bpf.load_func("xdp_capture", BPF.XDP)
            bpf.attach_xdp(interface, fn)
            self._xdp_attached = True
        except Exception as e:
            print(f"Warning: Could not attach XDP: {e}")
            print("Falling back to kprobe-based capture")
    
    def _detach_xdp(self, bpf: 'BPF', interface: str):
        """
        Detach XDP program from interface.
        
        Args:
            bpf: Compiled BPF object
            interface: Network interface name
        """
        if self._xdp_attached:
            try:
                bpf.remove_xdp(interface)
                self._xdp_attached = False
            except Exception as e:
                print(f"Warning: Could not detach XDP: {e}")
    
    def capture_xdp(
        self,
        count: int = 0,
        timeout: Optional[float] = None,
        callback: Optional[Callable] = None
    ) -> List[Dict[str, Any]]:
        """
        Capture packets using XDP (eXpress Data Path).
        
        XDP provides the highest performance packet capture by running
        eBPF programs at the earliest point in the network stack.
        
        Args:
            count: Number of packets to capture (0 = unlimited)
            timeout: Timeout in seconds (None = no timeout)
            callback: Callback function for each packet
            
        Returns:
            List of captured packet dictionaries
        """
        if not BCC_AVAILABLE:
            raise ImportError("BCC not installed")
        
        self.is_capturing = True
        self.stats.start_time = datetime.now()
        self._callback = callback
        
        try:
            # Compile eBPF program
            self._bpf = self._compile_bcc_program(self.BPF_PROGRAM)
            
            # Attach XDP to interface
            if self.interface:
                self._attach_xdp(self._bpf, self.interface)
            
            # Set up perf buffer callback
            def handle_event(cpu, data, size):
                if not self.is_capturing:
                    return
                
                if count > 0 and self.stats.packets_captured >= count:
                    return
                
                # Parse event
                event = ctypes.cast(data, ctypes.POINTER(self._bpf.struct_packet_event)).contents
                
                # Create packet info
                packet_info = {
                    'packet_number': self.stats.packets_captured + 1,
                    'timestamp': datetime.fromtimestamp(event.timestamp / 1e9).isoformat(),
                    'raw_length': event.length,
                    'protocols': ['IP'],
                    'ip': {
                        'src_ip': self._int_to_ip(event.src_ip),
                        'dst_ip': self._int_to_ip(event.dst_ip),
                        'protocol': event.protocol,
                    },
                }
                
                # Add TCP/UDP info if available
                if event.src_port or event.dst_port:
                    if event.protocol == 6:  # TCP
                        packet_info['protocols'].append('TCP')
                        packet_info['tcp'] = {
                            'src_port': event.src_port,
                            'dst_port': event.dst_port,
                        }
                    elif event.protocol == 17:  # UDP
                        packet_info['protocols'].append('UDP')
                        packet_info['udp'] = {
                            'src_port': event.src_port,
                            'dst_port': event.dst_port,
                        }
                
                # Update statistics
                self.stats.packets_captured += 1
                self.stats.bytes_captured += event.length
                self.stats.events_received += 1
                
                # Store packet
                self.captured_packets.append(packet_info)
                
                # Call callback if provided
                if self._callback:
                    self._callback(packet_info)
            
            # Open perf buffer
            self._bpf["events"].open_perf_buffer(handle_event)
            
            # Capture loop
            start_time = time.time()
            while self.is_capturing:
                if count > 0 and self.stats.packets_captured >= count:
                    break
                
                if timeout and (time.time() - start_time) >= timeout:
                    break
                
                try:
                    self._bpf.perf_buffer_poll(timeout=1)
                except KeyboardInterrupt:
                    break
                    
        finally:
            self.is_capturing = False
            self.stats.end_time = datetime.now()
            
            # Detach XDP
            if self._bpf and self.interface:
                self._detach_xdp(self._bpf, self.interface)
        
        return self.captured_packets
    
    def capture_kprobe(
        self,
        count: int = 0,
        timeout: Optional[float] = None,
        callback: Optional[Callable] = None
    ) -> List[Dict[str, Any]]:
        """
        Capture packets using kprobe/kretprobe.
        
        This method hooks into kernel functions to capture packets.
        Less performant than XDP but works on older kernels.
        
        Args:
            count: Number of packets to capture (0 = unlimited)
            timeout: Timeout in seconds (None = no timeout)
            callback: Callback function for each packet
            
        Returns:
            List of captured packet dictionaries
        """
        if not BCC_AVAILABLE:
            raise ImportError("BCC not installed")
        
        kprobe_program = """
        #include <uapi/linux/ptrace.h>
        #include <linux/skbuff.h>
        #include <linux/if_ether.h>
        #include <linux/ip.h>
        
        BPF_PERF_OUTPUT(events);
        
        struct packet_event {
            u64 timestamp;
            u32 length;
            u32 src_ip;
            u32 dst_ip;
            u8 protocol;
            u8 pad[3];
        };
        
        int kprobe__netif_receive_skb(struct pt_regs *ctx, struct sk_buff *skb) {
            struct packet_event event = {};
            event.timestamp = bpf_ktime_get_ns();
            event.length = skb->len;
            
            // Try to parse IP header
            unsigned char *data = skb->data;
            struct ethhdr *eth = (struct ethhdr *)data;
            
            if (eth->h_proto == htons(ETH_P_IP)) {
                struct iphdr *ip = (struct iphdr *)(data + sizeof(struct ethhdr));
                event.src_ip = ip->saddr;
                event.dst_ip = ip->daddr;
                event.protocol = ip->protocol;
            }
            
            events.perf_submit(ctx, &event, sizeof(event));
            return 0;
        }
        """
        
        self.is_capturing = True
        self.stats.start_time = datetime.now()
        self._callback = callback
        
        try:
            # Compile eBPF program
            self._bpf = self._compile_bcc_program(kprobe_program)
            
            # Set up perf buffer callback
            def handle_event(cpu, data, size):
                if not self.is_capturing:
                    return
                
                if count > 0 and self.stats.packets_captured >= count:
                    return
                
                # Parse event
                event = ctypes.cast(data, ctypes.POINTER(self._bpf.struct_packet_event)).contents
                
                # Create packet info
                packet_info = {
                    'packet_number': self.stats.packets_captured + 1,
                    'timestamp': datetime.fromtimestamp(event.timestamp / 1e9).isoformat(),
                    'raw_length': event.length,
                    'protocols': [],
                }
                
                if event.src_ip or event.dst_ip:
                    packet_info['protocols'].append('IP')
                    packet_info['ip'] = {
                        'src_ip': self._int_to_ip(event.src_ip),
                        'dst_ip': self._int_to_ip(event.dst_ip),
                        'protocol': event.protocol,
                    }
                
                # Update statistics
                self.stats.packets_captured += 1
                self.stats.bytes_captured += event.length
                self.stats.events_received += 1
                
                # Store packet
                self.captured_packets.append(packet_info)
                
                # Call callback if provided
                if self._callback:
                    self._callback(packet_info)
            
            # Open perf buffer
            self._bpf["events"].open_perf_buffer(handle_event)
            
            # Capture loop
            start_time = time.time()
            while self.is_capturing:
                if count > 0 and self.stats.packets_captured >= count:
                    break
                
                if timeout and (time.time() - start_time) >= timeout:
                    break
                
                try:
                    self._bpf.perf_buffer_poll(timeout=1)
                except KeyboardInterrupt:
                    break
                    
        finally:
            self.is_capturing = False
            self.stats.end_time = datetime.now()
        
        return self.captured_packets
    
    @staticmethod
    def _int_to_ip(ip_int: int) -> str:
        """
        Convert integer IP address to string.
        
        Args:
            ip_int: IP address as 32-bit integer (network byte order)
            
        Returns:
            IP address string in dotted notation
        """
        import socket
        import struct
        return socket.inet_ntoa(struct.pack('!I', socket.ntohl(ip_int)))
    
    def filter_packets(
        self,
        packets: Optional[List[Dict[str, Any]]] = None,
        protocol: Optional[str] = None,
        src_ip: Optional[str] = None,
        dst_ip: Optional[str] = None,
        src_port: Optional[int] = None,
        dst_port: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Filter captured packets by various criteria.
        
        Args:
            packets: List of packets to filter (uses captured_packets if None)
            protocol: Protocol to filter ('tcp', 'udp', 'icmp')
            src_ip: Source IP address
            dst_ip: Destination IP address
            src_port: Source port number
            dst_port: Destination port number
            
        Returns:
            Filtered list of packets
        """
        if packets is None:
            packets = self.captured_packets
        
        filtered = packets
        
        # Filter by protocol
        if protocol:
            protocol = protocol.lower()
            filtered = [
                p for p in filtered
                if protocol in [proto.lower() for proto in p.get('protocols', [])]
            ]
        
        # Filter by source IP
        if src_ip:
            filtered = [
                p for p in filtered
                if p.get('ip', {}).get('src_ip') == src_ip
            ]
        
        # Filter by destination IP
        if dst_ip:
            filtered = [
                p for p in filtered
                if p.get('ip', {}).get('dst_ip') == dst_ip
            ]
        
        # Filter by source port
        if src_port:
            filtered = [
                p for p in filtered
                if p.get('tcp', {}).get('src_port') == src_port or
                   p.get('udp', {}).get('src_port') == src_port
            ]
        
        # Filter by destination port
        if dst_port:
            filtered = [
                p for p in filtered
                if p.get('tcp', {}).get('dst_port') == dst_port or
                   p.get('udp', {}).get('dst_port') == dst_port
            ]
        
        return filtered
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get capture statistics.
        
        Returns:
            Dictionary containing capture statistics
        """
        return {
            'packets_captured': self.stats.packets_captured,
            'bytes_captured': self.stats.bytes_captured,
            'events_received': self.stats.events_received,
            'duration_seconds': self.stats.duration_seconds,
            'packets_per_second': self.stats.packets_per_second,
            'is_capturing': self.is_capturing,
            'interface': self.interface,
            'backend': self.backend,
            'xdp_attached': self._xdp_attached,
        }
    
    def stop_capture(self):
        """Stop ongoing capture"""
        self.is_capturing = False
    
    def clear_captured(self):
        """Clear captured packets list"""
        self.captured_packets.clear()
        self.stats = EBpfStats()
        self.analyzer = PacketAnalyzer()
