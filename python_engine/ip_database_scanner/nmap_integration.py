"""
Nmap Integration Module

Provides integration with Nmap for advanced port scanning and service detection.
"""

import subprocess
import json
import re
import xml.etree.ElementTree as ET
from typing import List, Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class NmapHost:
    """Nmap host information"""
    ip: str
    hostname: Optional[str] = None
    state: str = 'unknown'
    os: Optional[str] = None
    ports: List[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.ports is None:
            self.ports = []


@dataclass
class NmapPort:
    """Nmap port information"""
    port: int
    protocol: str
    state: str
    service: str
    version: Optional[str] = None
    product: Optional[str] = None
    extra_info: Optional[str] = None


@dataclass
class NmapScanResult:
    """Nmap scan result"""
    target: str
    scan_type: str
    hosts: List[NmapHost]
    scan_time: float
    command: str


class NmapIntegration:
    """
    Integration with Nmap for advanced network scanning.
    
    Features:
    - Port scanning with service detection
    - OS fingerprinting
    - Vulnerability scanning
    - Script scanning
    - Database service detection
    """
    
    # Database service signatures
    DATABASE_SIGNATURES = {
        'mongodb': {
            'ports': [27017, 27018, 27019],
            'service': 'mongodb',
            'product': 'MongoDB',
        },
        'elasticsearch': {
            'ports': [9200, 9300],
            'service': 'http',
            'product': 'Elasticsearch',
        },
        'redis': {
            'ports': [6379, 6380, 26379],
            'service': 'redis',
            'product': 'Redis',
        },
        'mysql': {
            'ports': [3306],
            'service': 'mysql',
            'product': 'MySQL',
        },
        'postgresql': {
            'ports': [5432],
            'service': 'postgresql',
            'product': 'PostgreSQL',
        },
        'couchdb': {
            'ports': [5984],
            'service': 'http',
            'product': 'CouchDB',
        },
        'influxdb': {
            'ports': [8086, 8088],
            'service': 'http',
            'product': 'InfluxDB',
        },
        'arangodb': {
            'ports': [8529],
            'service': 'http',
            'product': 'ArangoDB',
        },
        'neo4j': {
            'ports': [7474, 7687],
            'service': 'http',
            'product': 'Neo4j',
        },
        'cassandra': {
            'ports': [9042, 9160],
            'service': 'cassandra',
            'product': 'Cassandra',
        },
        'memcached': {
            'ports': [11211],
            'service': 'memcached',
            'product': 'Memcached',
        },
        'rethinkdb': {
            'ports': [28015, 29015],
            'service': 'rethinkdb',
            'product': 'RethinkDB',
        },
    }
    
    def __init__(self, nmap_path: str = 'nmap'):
        """
        Initialize Nmap integration.
        
        Args:
            nmap_path: Path to nmap executable
        """
        self.nmap_path = nmap_path
    
    def check_nmap_installed(self) -> bool:
        """
        Check if Nmap is installed.
        
        Returns:
            True if Nmap is installed
        """
        try:
            result = subprocess.run(
                [self.nmap_path, '--version'],
                capture_output=True,
                text=True,
                timeout=10
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False
    
    def scan_ports(
        self,
        target: str,
        ports: Optional[str] = None,
        scan_type: str = '-sS',
        service_detection: bool = True,
        os_detection: bool = False,
        script_scan: bool = False
    ) -> NmapScanResult:
        """
        Scan ports on target.
        
        Args:
            target: Target IP or hostname
            ports: Port range (e.g., '1-1000', '22,80,443')
            scan_type: Scan type (-sS, -sT, -sU, etc.)
            service_detection: Enable service detection
            os_detection: Enable OS detection
            script_scan: Enable script scanning
            
        Returns:
            NmapScanResult object
        """
        import time
        start_time = time.time()
        
        # Build command
        cmd = [self.nmap_path]
        
        # Add scan type
        cmd.append(scan_type)
        
        # Add port range
        if ports:
            cmd.extend(['-p', ports])
        
        # Add service detection
        if service_detection:
            cmd.append('-sV')
        
        # Add OS detection
        if os_detection:
            cmd.append('-O')
        
        # Add script scanning
        if script_scan:
            cmd.append('-sC')
        
        # Output as XML
        cmd.extend(['-oX', '-'])
        
        # Add target
        cmd.append(target)
        
        try:
            # Run nmap
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300
            )
            
            # Parse XML output
            hosts = self._parse_nmap_xml(result.stdout)
            
            return NmapScanResult(
                target=target,
                scan_type=scan_type,
                hosts=hosts,
                scan_time=time.time() - start_time,
                command=' '.join(cmd)
            )
            
        except subprocess.TimeoutExpired:
            return NmapScanResult(
                target=target,
                scan_type=scan_type,
                hosts=[],
                scan_time=time.time() - start_time,
                command=' '.join(cmd)
            )
        except Exception as e:
            print(f"Error running nmap: {e}")
            return NmapScanResult(
                target=target,
                scan_type=scan_type,
                hosts=[],
                scan_time=time.time() - start_time,
                command=' '.join(cmd)
            )
    
    def _parse_nmap_xml(self, xml_output: str) -> List[NmapHost]:
        """
        Parse Nmap XML output.
        
        Args:
            xml_output: Nmap XML output
            
        Returns:
            List of NmapHost objects
        """
        hosts = []
        
        try:
            root = ET.fromstring(xml_output)
            
            for host_elem in root.findall('.//host'):
                # Get IP address
                ip = None
                hostname = None
                
                for addr in host_elem.findall('.//address'):
                    if addr.get('addrtype') == 'ipv4':
                        ip = addr.get('addr')
                
                # Get hostname
                hostnames = host_elem.findall('.//hostname')
                if hostnames:
                    hostname = hostnames[0].get('name')
                
                # Get host state
                state_elem = host_elem.find('.//status')
                state = state_elem.get('state') if state_elem is not None else 'unknown'
                
                # Get OS information
                os = None
                os_elem = host_elem.find('.//osmatch')
                if os_elem is not None:
                    os = os_elem.get('name')
                
                # Get ports
                ports = []
                for port_elem in host_elem.findall('.//port'):
                    port_num = int(port_elem.get('portid'))
                    protocol = port_elem.get('protocol')
                    
                    # Get port state
                    state_elem = port_elem.find('.//state')
                    port_state = state_elem.get('state') if state_elem is not None else 'unknown'
                    
                    # Get service information
                    service_elem = port_elem.find('.//service')
                    service = service_elem.get('name') if service_elem is not None else 'unknown'
                    version = service_elem.get('version') if service_elem is not None else None
                    product = service_elem.get('product') if service_elem is not None else None
                    extra_info = service_elem.get('extrainfo') if service_elem is not None else None
                    
                    ports.append(NmapPort(
                        port=port_num,
                        protocol=protocol,
                        state=port_state,
                        service=service,
                        version=version,
                        product=product,
                        extra_info=extra_info
                    ))
                
                if ip:
                    hosts.append(NmapHost(
                        ip=ip,
                        hostname=hostname,
                        state=state,
                        os=os,
                        ports=ports
                    ))
                    
        except ET.ParseError as e:
            print(f"Error parsing Nmap XML: {e}")
        except Exception as e:
            print(f"Error processing Nmap output: {e}")
        
        return hosts
    
    def scan_database_services(
        self,
        target: str,
        database_types: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Scan for database services.
        
        Args:
            target: Target IP or hostname
            database_types: List of database types to scan
            
        Returns:
            List of database service dictionaries
        """
        if database_types is None:
            database_types = list(self.DATABASE_SIGNATURES.keys())
        
        # Build port list
        ports = []
        for db_type in database_types:
            if db_type in self.DATABASE_SIGNATURES:
                ports.extend(self.DATABASE_SIGNATURES[db_type]['ports'])
        
        # Remove duplicates
        ports = list(set(ports))
        port_str = ','.join(str(p) for p in ports)
        
        # Scan ports
        scan_result = self.scan_ports(
            target=target,
            ports=port_str,
            service_detection=True
        )
        
        # Identify database services
        databases = []
        
        for host in scan_result.hosts:
            for port in host.ports:
                if port.state == 'open':
                    # Check if port matches database signature
                    for db_type, signature in self.DATABASE_SIGNATURES.items():
                        if port.port in signature['ports']:
                            databases.append({
                                'ip': host.ip,
                                'port': port.port,
                                'database_type': db_type,
                                'service': port.service,
                                'product': port.product,
                                'version': port.version,
                                'extra_info': port.extra_info,
                                'hostname': host.hostname,
                                'os': host.os,
                            })
                            break
        
        return databases
    
    def vulnerability_scan(
        self,
        target: str,
        ports: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Run vulnerability scan using Nmap scripts.
        
        Args:
            target: Target IP or hostname
            ports: Port range to scan
            
        Returns:
            List of vulnerability dictionaries
        """
        vulnerabilities = []
        
        # Run vulnerability scan
        cmd = [self.nmap_path, '--script', 'vuln']
        
        if ports:
            cmd.extend(['-p', ports])
        
        cmd.append(target)
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300
            )
            
            # Parse output for vulnerabilities
            vulnerabilities = self._parse_vulnerability_output(result.stdout)
            
        except subprocess.TimeoutExpired:
            print("Vulnerability scan timed out")
        except Exception as e:
            print(f"Error running vulnerability scan: {e}")
        
        return vulnerabilities
    
    def _parse_vulnerability_output(self, output: str) -> List[Dict[str, Any]]:
        """
        Parse vulnerability scan output.
        
        Args:
            output: Nmap script output
            
        Returns:
            List of vulnerability dictionaries
        """
        vulnerabilities = []
        
        lines = output.split('\n')
        current_vuln = None
        
        for line in lines:
            # Look for vulnerability indicators
            if 'VULNERABLE' in line or 'CVE-' in line:
                if current_vuln:
                    vulnerabilities.append(current_vuln)
                
                current_vuln = {
                    'name': line.strip(),
                    'description': '',
                    'severity': 'unknown',
                    'references': [],
                }
            
            elif current_vuln:
                # Add additional information
                if 'CVE-' in line:
                    cve_match = re.search(r'CVE-\d{4}-\d+', line)
                    if cve_match:
                        current_vuln['references'].append(cve_match.group())
                
                if 'State:' in line:
                    current_vuln['description'] = line.strip()
        
        if current_vuln:
            vulnerabilities.append(current_vuln)
        
        return vulnerabilities
    
    def script_scan(
        self,
        target: str,
        scripts: List[str],
        ports: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Run specific Nmap scripts.
        
        Args:
            target: Target IP or hostname
            scripts: List of scripts to run
            ports: Port range to scan
            
        Returns:
            Dictionary containing script results
        """
        results = {}
        
        for script in scripts:
            try:
                cmd = [self.nmap_path, '--script', script]
                
                if ports:
                    cmd.extend(['-p', ports])
                
                cmd.append(target)
                
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=60
                )
                
                results[script] = {
                    'output': result.stdout,
                    'error': result.stderr,
                    'returncode': result.returncode,
                }
                
            except subprocess.TimeoutExpired:
                results[script] = {
                    'output': '',
                    'error': 'Script timed out',
                    'returncode': -1,
                }
            except Exception as e:
                results[script] = {
                    'output': '',
                    'error': str(e),
                    'returncode': -1,
                }
        
        return results
    
    def detect_database_version(
        self,
        target: str,
        port: int,
        database_type: str
    ) -> Optional[Dict[str, Any]]:
        """
        Detect database version using Nmap.
        
        Args:
            target: Target IP or hostname
            port: Database port
            database_type: Database type
            
        Returns:
            Dictionary containing version information
        """
        # Run service detection on specific port
        scan_result = self.scan_ports(
            target=target,
            ports=str(port),
            service_detection=True
        )
        
        # Extract version information
        for host in scan_result.hosts:
            for port_info in host.ports:
                if port_info.port == port and port_info.state == 'open':
                    return {
                        'ip': host.ip,
                        'port': port,
                        'database_type': database_type,
                        'service': port_info.service,
                        'product': port_info.product,
                        'version': port_info.version,
                        'extra_info': port_info.extra_info,
                    }
        
        return None
    
    def enumerate_database(
        self,
        target: str,
        port: int,
        database_type: str
    ) -> Dict[str, Any]:
        """
        Enumerate database using Nmap scripts.
        
        Args:
            target: Target IP or hostname
            port: Database port
            database_type: Database type
            
        Returns:
            Dictionary containing enumeration results
        """
        # Select appropriate scripts based on database type
        scripts = []
        
        if database_type == 'mongodb':
            scripts = ['mongodb-info', 'mongodb-databases']
        elif database_type == 'elasticsearch':
            scripts = ['http-enum', 'http-title']
        elif database_type == 'redis':
            scripts = ['redis-info', 'redis-enum']
        elif database_type == 'mysql':
            scripts = ['mysql-info', 'mysql-enum', 'mysql-users']
        elif database_type == 'postgresql':
            scripts = ['pgsql-info', 'pgsql-enum']
        elif database_type == 'couchdb':
            scripts = ['http-enum', 'couchdb-databases']
        elif database_type == 'influxdb':
            scripts = ['http-enum', 'http-title']
        elif database_type == 'arangodb':
            scripts = ['http-enum', 'http-title']
        elif database_type == 'neo4j':
            scripts = ['http-enum', 'neo4j-enum']
        elif database_type == 'cassandra':
            scripts = ['cassandra-info', 'cassandra-enum']
        elif database_type == 'memcached':
            scripts = ['memcached-info', 'memcached-enum']
        elif database_type == 'rethinkdb':
            scripts = ['rethinkdb-info', 'rethinkdb-enum']
        
        if not scripts:
            return {}
        
        # Run scripts
        results = self.script_scan(
            target=target,
            scripts=scripts,
            ports=str(port)
        )
        
        return results
