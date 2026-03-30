"""
Packet Analyzer Module

Provides packet parsing and analysis capabilities for raw network packets.
Supports Ethernet, IP, TCP, UDP, and ICMP header parsing.
"""

import struct
import socket
from typing import Dict, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime


@dataclass
class EthernetHeader:
    """Ethernet frame header"""
    dst_mac: str
    src_mac: str
    ethertype: int
    payload: bytes


@dataclass
class IPHeader:
    """IP packet header"""
    version: int
    header_length: int
    tos: int
    total_length: int
    identification: int
    flags: int
    fragment_offset: int
    ttl: int
    protocol: int
    checksum: int
    src_ip: str
    dst_ip: str
    payload: bytes


@dataclass
class TCPHeader:
    """TCP segment header"""
    src_port: int
    dst_port: int
    sequence: int
    acknowledgment: int
    header_length: int
    flags: int
    window_size: int
    checksum: int
    urgent_pointer: int
    payload: bytes


@dataclass
class UDPHeader:
    """UDP datagram header"""
    src_port: int
    dst_port: int
    length: int
    checksum: int
    payload: bytes


@dataclass
class ICMPHeader:
    """ICMP message header"""
    type: int
    code: int
    checksum: int
    identifier: int
    sequence: int
    payload: bytes


class PacketAnalyzer:
    """
    Analyzes raw network packets and extracts protocol information.
    
    Supports parsing of:
    - Ethernet frames (Layer 2)
    - IP packets (Layer 3)
    - TCP segments (Layer 4)
    - UDP datagrams (Layer 4)
    - ICMP messages (Layer 4)
    """
    
    # EtherType constants
    ETH_P_IP = 0x0800
    ETH_P_ARP = 0x0806
    ETH_P_IPV6 = 0x86DD
    
    # IP protocol constants
    IPPROTO_TCP = 6
    IPPROTO_UDP = 17
    IPPROTO_ICMP = 1
    
    # TCP flag constants
    TCP_FIN = 0x01
    TCP_SYN = 0x02
    TCP_RST = 0x04
    TCP_PSH = 0x08
    TCP_ACK = 0x10
    TCP_URG = 0x20
    
    def __init__(self):
        """Initialize the packet analyzer"""
        self.packet_count = 0
        self.start_time = datetime.now()
    
    def parse_ethernet(self, raw_data: bytes) -> Optional[EthernetHeader]:
        """
        Parse Ethernet frame header.
        
        Args:
            raw_data: Raw Ethernet frame bytes
            
        Returns:
            EthernetHeader object or None if parsing fails
        """
        try:
            if len(raw_data) < 14:
                return None
            
            # Parse Ethernet header (14 bytes)
            dst_mac_bytes = raw_data[0:6]
            src_mac_bytes = raw_data[6:12]
            ethertype = struct.unpack('!H', raw_data[12:14])[0]
            
            # Format MAC addresses
            dst_mac = ':'.join(f'{b:02x}' for b in dst_mac_bytes)
            src_mac = ':'.join(f'{b:02x}' for b in src_mac_bytes)
            
            return EthernetHeader(
                dst_mac=dst_mac,
                src_mac=src_mac,
                ethertype=ethertype,
                payload=raw_data[14:]
            )
        except Exception as e:
            print(f"Error parsing Ethernet header: {e}")
            return None
    
    def parse_ip(self, raw_data: bytes) -> Optional[IPHeader]:
        """
        Parse IP packet header.
        
        Args:
            raw_data: Raw IP packet bytes
            
        Returns:
            IPHeader object or None if parsing fails
        """
        try:
            if len(raw_data) < 20:
                return None
            
            # Parse IP header (minimum 20 bytes)
            version_ihl = raw_data[0]
            version = (version_ihl >> 4) & 0x0F
            ihl = (version_ihl & 0x0F) * 4
            
            tos = raw_data[1]
            total_length = struct.unpack('!H', raw_data[2:4])[0]
            identification = struct.unpack('!H', raw_data[4:6])[0]
            flags_fragment = struct.unpack('!H', raw_data[6:8])[0]
            flags = (flags_fragment >> 13) & 0x07
            fragment_offset = flags_fragment & 0x1FFF
            
            ttl = raw_data[8]
            protocol = raw_data[9]
            checksum = struct.unpack('!H', raw_data[10:12])[0]
            
            src_ip = socket.inet_ntoa(raw_data[12:16])
            dst_ip = socket.inet_ntoa(raw_data[16:20])
            
            # Extract payload (after IP header)
            payload = raw_data[ihl:]
            
            return IPHeader(
                version=version,
                header_length=ihl,
                tos=tos,
                total_length=total_length,
                identification=identification,
                flags=flags,
                fragment_offset=fragment_offset,
                ttl=ttl,
                protocol=protocol,
                checksum=checksum,
                src_ip=src_ip,
                dst_ip=dst_ip,
                payload=payload
            )
        except Exception as e:
            print(f"Error parsing IP header: {e}")
            return None
    
    def parse_tcp(self, raw_data: bytes) -> Optional[TCPHeader]:
        """
        Parse TCP segment header.
        
        Args:
            raw_data: Raw TCP segment bytes
            
        Returns:
            TCPHeader object or None if parsing fails
        """
        try:
            if len(raw_data) < 20:
                return None
            
            # Parse TCP header (minimum 20 bytes)
            src_port = struct.unpack('!H', raw_data[0:2])[0]
            dst_port = struct.unpack('!H', raw_data[2:4])[0]
            sequence = struct.unpack('!I', raw_data[4:8])[0]
            acknowledgment = struct.unpack('!I', raw_data[8:12])[0]
            
            offset_flags = struct.unpack('!H', raw_data[12:14])[0]
            header_length = ((offset_flags >> 12) & 0x0F) * 4
            flags = offset_flags & 0x03F
            
            window_size = struct.unpack('!H', raw_data[14:16])[0]
            checksum = struct.unpack('!H', raw_data[16:18])[0]
            urgent_pointer = struct.unpack('!H', raw_data[18:20])[0]
            
            # Extract payload (after TCP header)
            payload = raw_data[header_length:]
            
            return TCPHeader(
                src_port=src_port,
                dst_port=dst_port,
                sequence=sequence,
                acknowledgment=acknowledgment,
                header_length=header_length,
                flags=flags,
                window_size=window_size,
                checksum=checksum,
                urgent_pointer=urgent_pointer,
                payload=payload
            )
        except Exception as e:
            print(f"Error parsing TCP header: {e}")
            return None
    
    def parse_udp(self, raw_data: bytes) -> Optional[UDPHeader]:
        """
        Parse UDP datagram header.
        
        Args:
            raw_data: Raw UDP datagram bytes
            
        Returns:
            UDPHeader object or None if parsing fails
        """
        try:
            if len(raw_data) < 8:
                return None
            
            # Parse UDP header (8 bytes)
            src_port = struct.unpack('!H', raw_data[0:2])[0]
            dst_port = struct.unpack('!H', raw_data[2:4])[0]
            length = struct.unpack('!H', raw_data[4:6])[0]
            checksum = struct.unpack('!H', raw_data[6:8])[0]
            
            # Extract payload (after UDP header)
            payload = raw_data[8:]
            
            return UDPHeader(
                src_port=src_port,
                dst_port=dst_port,
                length=length,
                checksum=checksum,
                payload=payload
            )
        except Exception as e:
            print(f"Error parsing UDP header: {e}")
            return None
    
    def parse_icmp(self, raw_data: bytes) -> Optional[ICMPHeader]:
        """
        Parse ICMP message header.
        
        Args:
            raw_data: Raw ICMP message bytes
            
        Returns:
            ICMPHeader object or None if parsing fails
        """
        try:
            if len(raw_data) < 8:
                return None
            
            # Parse ICMP header (8 bytes)
            icmp_type = raw_data[0]
            code = raw_data[1]
            checksum = struct.unpack('!H', raw_data[2:4])[0]
            identifier = struct.unpack('!H', raw_data[4:6])[0]
            sequence = struct.unpack('!H', raw_data[6:8])[0]
            
            # Extract payload (after ICMP header)
            payload = raw_data[8:]
            
            return ICMPHeader(
                type=icmp_type,
                code=code,
                checksum=checksum,
                identifier=identifier,
                sequence=sequence,
                payload=payload
            )
        except Exception as e:
            print(f"Error parsing ICMP header: {e}")
            return None
    
    def analyze_packet(self, raw_data: bytes) -> Dict[str, Any]:
        """
        Analyze a complete packet and extract all protocol information.
        
        Args:
            raw_data: Raw packet bytes (starting from Ethernet frame)
            
        Returns:
            Dictionary containing parsed protocol information
        """
        self.packet_count += 1
        
        result = {
            'packet_number': self.packet_count,
            'timestamp': datetime.now().isoformat(),
            'raw_length': len(raw_data),
            'protocols': [],
            'ethernet': None,
            'ip': None,
            'tcp': None,
            'udp': None,
            'icmp': None,
        }
        
        # Parse Ethernet frame
        eth_header = self.parse_ethernet(raw_data)
        if eth_header:
            result['ethernet'] = {
                'dst_mac': eth_header.dst_mac,
                'src_mac': eth_header.src_mac,
                'ethertype': hex(eth_header.ethertype),
            }
            result['protocols'].append('Ethernet')
            
            # Parse IP packet if present
            if eth_header.ethertype == self.ETH_P_IP:
                ip_header = self.parse_ip(eth_header.payload)
                if ip_header:
                    result['ip'] = {
                        'version': ip_header.version,
                        'header_length': ip_header.header_length,
                        'total_length': ip_header.total_length,
                        'ttl': ip_header.ttl,
                        'protocol': ip_header.protocol,
                        'src_ip': ip_header.src_ip,
                        'dst_ip': ip_header.dst_ip,
                    }
                    result['protocols'].append('IP')
                    
                    # Parse transport layer protocol
                    if ip_header.protocol == self.IPPROTO_TCP:
                        tcp_header = self.parse_tcp(ip_header.payload)
                        if tcp_header:
                            result['tcp'] = {
                                'src_port': tcp_header.src_port,
                                'dst_port': tcp_header.dst_port,
                                'sequence': tcp_header.sequence,
                                'acknowledgment': tcp_header.acknowledgment,
                                'flags': self._decode_tcp_flags(tcp_header.flags),
                                'window_size': tcp_header.window_size,
                                'payload_length': len(tcp_header.payload),
                            }
                            result['protocols'].append('TCP')
                    
                    elif ip_header.protocol == self.IPPROTO_UDP:
                        udp_header = self.parse_udp(ip_header.payload)
                        if udp_header:
                            result['udp'] = {
                                'src_port': udp_header.src_port,
                                'dst_port': udp_header.dst_port,
                                'length': udp_header.length,
                                'payload_length': len(udp_header.payload),
                            }
                            result['protocols'].append('UDP')
                    
                    elif ip_header.protocol == self.IPPROTO_ICMP:
                        icmp_header = self.parse_icmp(ip_header.payload)
                        if icmp_header:
                            result['icmp'] = {
                                'type': icmp_header.type,
                                'code': icmp_header.code,
                                'identifier': icmp_header.identifier,
                                'sequence': icmp_header.sequence,
                                'payload_length': len(icmp_header.payload),
                            }
                            result['protocols'].append('ICMP')
        
        return result
    
    def _decode_tcp_flags(self, flags: int) -> Dict[str, bool]:
        """
        Decode TCP flags bitmask into human-readable format.
        
        Args:
            flags: TCP flags bitmask
            
        Returns:
            Dictionary of flag names and their states
        """
        return {
            'FIN': bool(flags & self.TCP_FIN),
            'SYN': bool(flags & self.TCP_SYN),
            'RST': bool(flags & self.TCP_RST),
            'PSH': bool(flags & self.TCP_PSH),
            'ACK': bool(flags & self.TCP_ACK),
            'URG': bool(flags & self.TCP_URG),
        }
    
    def get_protocol_name(self, protocol_number: int) -> str:
        """
        Get protocol name from protocol number.
        
        Args:
            protocol_number: IP protocol number
            
        Returns:
            Protocol name string
        """
        protocols = {
            1: 'ICMP',
            6: 'TCP',
            17: 'UDP',
            27: 'RDP',
            47: 'GRE',
            50: 'ESP',
            51: 'AH',
            58: 'ICMPv6',
            132: 'SCTP',
        }
        return protocols.get(protocol_number, f'Unknown ({protocol_number})')
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get analyzer statistics.
        
        Returns:
            Dictionary containing analyzer statistics
        """
        uptime = (datetime.now() - self.start_time).total_seconds()
        return {
            'packets_analyzed': self.packet_count,
            'uptime_seconds': uptime,
            'packets_per_second': self.packet_count / uptime if uptime > 0 else 0,
        }
