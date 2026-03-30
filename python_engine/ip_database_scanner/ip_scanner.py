"""
IP Scanner Module

Provides IP range scanning capabilities for discovering exposed databases.
"""

import socket
import ipaddress
import concurrent.futures
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime


@dataclass
class ScanResult:
    """IP scan result"""
    ip: str
    port: int
    is_open: bool
    service: Optional[str] = None
    response_time: Optional[float] = None
    banner: Optional[str] = None


class IPScanner:
    """
    IP range scanner for discovering exposed databases and services.
    
    Features:
    - Scan IP ranges for open ports
    - Detect common database ports
    - Multi-threaded scanning
    - Service identification
    - Banner grabbing
    """
    
    # Common database ports
    DATABASE_PORTS = {
        27017: 'MongoDB',
        27018: 'MongoDB (Shard)',
        27019: 'MongoDB (Config Server)',
        9200: 'Elasticsearch',
        9300: 'Elasticsearch (Transport)',
        6379: 'Redis',
        6380: 'Redis (Sentinel)',
        26379: 'Redis (Sentinel)',
        3306: 'MySQL',
        5432: 'PostgreSQL',
        1433: 'Microsoft SQL Server',
        1434: 'Microsoft SQL Server (Browser)',
        1521: 'Oracle Database',
        5000: 'CouchDB',
        5984: 'CouchDB (HTTP)',
        8086: 'InfluxDB',
        8088: 'InfluxDB (Admin)',
        8529: 'ArangoDB',
        7474: 'Neo4j',
        7687: 'Neo4j (Bolt)',
        9042: 'Cassandra',
        9160: 'Cassandra (Thrift)',
        11211: 'Memcached',
        28015: 'RethinkDB',
        29015: 'RethinkDB (Cluster)',
    }
    
    # Common web ports
    WEB_PORTS = {
        80: 'HTTP',
        443: 'HTTPS',
        8080: 'HTTP (Alternative)',
        8443: 'HTTPS (Alternative)',
        3000: 'Node.js/Express',
        5000: 'Flask/Python',
        8000: 'Django/Python',
        8888: 'Jupyter Notebook',
    }
    
    def __init__(
        self,
        timeout: float = 1.0,
        max_workers: int = 100
    ):
        """
        Initialize IP scanner.
        
        Args:
            timeout: Socket timeout in seconds
            max_workers: Maximum number of concurrent workers
        """
        self.timeout = timeout
        self.max_workers = max_workers
        self.results: List[ScanResult] = []
    
    def scan_port(
        self,
        ip: str,
        port: int,
        grab_banner: bool = False
    ) -> ScanResult:
        """
        Scan a single IP:port combination.
        
        Args:
            ip: IP address to scan
            port: Port number to scan
            grab_banner: Whether to grab service banner
            
        Returns:
            ScanResult object
        """
        start_time = datetime.now()
        
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(self.timeout)
            
            result = sock.connect_ex((ip, port))
            
            if result == 0:
                # Port is open
                banner = None
                if grab_banner:
                    try:
                        sock.send(b'HEAD / HTTP/1.0\r\n\r\n')
                        banner = sock.recv(1024).decode('utf-8', errors='ignore')
                    except:
                        pass
                
                response_time = (datetime.now() - start_time).total_seconds()
                
                # Identify service
                service = self._identify_service(port, banner)
                
                sock.close()
                
                return ScanResult(
                    ip=ip,
                    port=port,
                    is_open=True,
                    service=service,
                    response_time=response_time,
                    banner=banner
                )
            else:
                sock.close()
                return ScanResult(
                    ip=ip,
                    port=port,
                    is_open=False
                )
                
        except socket.timeout:
            return ScanResult(
                ip=ip,
                port=port,
                is_open=False
            )
        except Exception as e:
            return ScanResult(
                ip=ip,
                port=port,
                is_open=False
            )
    
    def _identify_service(
        self,
        port: int,
        banner: Optional[str] = None
    ) -> str:
        """
        Identify service based on port and banner.
        
        Args:
            port: Port number
            banner: Service banner
            
        Returns:
            Service name
        """
        # Check database ports
        if port in self.DATABASE_PORTS:
            return self.DATABASE_PORTS[port]
        
        # Check web ports
        if port in self.WEB_PORTS:
            return self.WEB_PORTS[port]
        
        # Try to identify from banner
        if banner:
            banner_lower = banner.lower()
            if 'mongodb' in banner_lower:
                return 'MongoDB'
            elif 'elasticsearch' in banner_lower:
                return 'Elasticsearch'
            elif 'redis' in banner_lower:
                return 'Redis'
            elif 'mysql' in banner_lower:
                return 'MySQL'
            elif 'postgresql' in banner_lower:
                return 'PostgreSQL'
            elif 'http' in banner_lower:
                return 'HTTP'
        
        return 'Unknown'
    
    def scan_ip_range(
        self,
        ip_range: str,
        ports: Optional[List[int]] = None,
        grab_banner: bool = False,
        only_open: bool = True
    ) -> List[ScanResult]:
        """
        Scan an IP range for open ports.
        
        Args:
            ip_range: IP range in CIDR notation (e.g., '192.168.1.0/24')
            ports: List of ports to scan (default: common database ports)
            grab_banner: Whether to grab service banners
            only_open: Whether to return only open ports
            
        Returns:
            List of ScanResult objects
        """
        if ports is None:
            ports = list(self.DATABASE_PORTS.keys())
        
        # Parse IP range
        try:
            network = ipaddress.ip_network(ip_range, strict=False)
            ips = [str(ip) for ip in network.hosts()]
        except ValueError as e:
            print(f"Invalid IP range: {e}")
            return []
        
        # Create scan tasks
        tasks = []
        for ip in ips:
            for port in ports:
                tasks.append((ip, port))
        
        # Scan with thread pool
        results = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_task = {
                executor.submit(self.scan_port, ip, port, grab_banner): (ip, port)
                for ip, port in tasks
            }
            
            for future in concurrent.futures.as_completed(future_to_task):
                result = future.result()
                if only_open and result.is_open:
                    results.append(result)
                elif not only_open:
                    results.append(result)
        
        self.results = results
        return results
    
    def scan_ip_list(
        self,
        ips: List[str],
        ports: Optional[List[int]] = None,
        grab_banner: bool = False,
        only_open: bool = True
    ) -> List[ScanResult]:
        """
        Scan a list of IP addresses.
        
        Args:
            ips: List of IP addresses
            ports: List of ports to scan
            grab_banner: Whether to grab service banners
            only_open: Whether to return only open ports
            
        Returns:
            List of ScanResult objects
        """
        if ports is None:
            ports = list(self.DATABASE_PORTS.keys())
        
        # Create scan tasks
        tasks = []
        for ip in ips:
            for port in ports:
                tasks.append((ip, port))
        
        # Scan with thread pool
        results = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_task = {
                executor.submit(self.scan_port, ip, port, grab_banner): (ip, port)
                for ip, port in tasks
            }
            
            for future in concurrent.futures.as_completed(future_to_task):
                result = future.result()
                if only_open and result.is_open:
                    results.append(result)
                elif not only_open:
                    results.append(result)
        
        self.results = results
        return results
    
    def scan_single_ip(
        self,
        ip: str,
        ports: Optional[List[int]] = None,
        grab_banner: bool = False
    ) -> List[ScanResult]:
        """
        Scan a single IP address.
        
        Args:
            ip: IP address to scan
            ports: List of ports to scan
            grab_banner: Whether to grab service banners
            
        Returns:
            List of ScanResult objects
        """
        if ports is None:
            ports = list(self.DATABASE_PORTS.keys())
        
        results = []
        for port in ports:
            result = self.scan_port(ip, port, grab_banner)
            if result.is_open:
                results.append(result)
        
        self.results = results
        return results
    
    def get_database_services(self) -> List[ScanResult]:
        """
        Get only database services from scan results.
        
        Returns:
            List of ScanResult objects for database services
        """
        return [
            result for result in self.results
            if result.service in self.DATABASE_PORTS.values()
        ]
    
    def get_web_services(self) -> List[ScanResult]:
        """
        Get only web services from scan results.
        
        Returns:
            List of ScanResult objects for web services
        """
        return [
            result for result in self.results
            if result.service in self.WEB_PORTS.values()
        ]
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get scan statistics.
        
        Returns:
            Dictionary containing scan statistics
        """
        total_scanned = len(self.results)
        open_ports = sum(1 for r in self.results if r.is_open)
        
        services = {}
        for result in self.results:
            if result.service:
                services[result.service] = services.get(result.service, 0) + 1
        
        return {
            'total_scanned': total_scanned,
            'open_ports': open_ports,
            'closed_ports': total_scanned - open_ports,
            'services': services,
        }
    
    def export_results(self, filename: str):
        """
        Export scan results to file.
        
        Args:
            filename: Output filename
        """
        import json
        
        export_data = []
        for result in self.results:
            export_data.append({
                'ip': result.ip,
                'port': result.port,
                'is_open': result.is_open,
                'service': result.service,
                'response_time': result.response_time,
                'banner': result.banner,
            })
        
        with open(filename, 'w') as f:
            json.dump(export_data, f, indent=2)
        
        print(f"Exported {len(export_data)} results to {filename}")
