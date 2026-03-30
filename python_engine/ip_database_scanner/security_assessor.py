"""
Security Assessor Module

Assesses security vulnerabilities in discovered databases.
"""

import re
import socket
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum


class VulnerabilityLevel(Enum):
    """Vulnerability severity levels"""
    CRITICAL = 'critical'
    HIGH = 'high'
    MEDIUM = 'medium'
    LOW = 'low'
    INFO = 'info'


@dataclass
class Vulnerability:
    """Security vulnerability"""
    name: str
    description: str
    level: VulnerabilityLevel
    recommendation: str
    evidence: Optional[str] = None


@dataclass
class SecurityAssessment:
    """Security assessment result"""
    ip: str
    port: int
    database_type: str
    vulnerabilities: List[Vulnerability]
    security_score: int  # 0-100
    risk_level: str
    assessment_time: float


class SecurityAssessor:
    """
    Assesses security vulnerabilities in databases.
    
    Features:
    - Check for authentication bypass
    - Detect exposed databases
    - Identify weak configurations
    - Assess encryption status
    - Check for known vulnerabilities
    """
    
    def __init__(self, timeout: float = 5.0):
        """
        Initialize security assessor.
        
        Args:
            timeout: Socket timeout in seconds
        """
        self.timeout = timeout
    
    def assess_mongodb(
        self,
        ip: str,
        port: int = 27017
    ) -> SecurityAssessment:
        """
        Assess MongoDB security.
        
        Args:
            ip: IP address
            port: Port number
            
        Returns:
            SecurityAssessment object
        """
        import time
        start_time = time.time()
        
        vulnerabilities = []
        
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(self.timeout)
            sock.connect((ip, port))
            
            # Check if authentication is required
            auth_required = self._check_mongodb_auth_required(sock)
            
            if not auth_required:
                vulnerabilities.append(Vulnerability(
                    name='No Authentication Required',
                    description='MongoDB instance does not require authentication',
                    level=VulnerabilityLevel.CRITICAL,
                    recommendation='Enable authentication in MongoDB configuration',
                    evidence='Successfully connected without credentials'
                ))
            
            # Check for exposed databases
            exposed_dbs = self._check_mongodb_exposed_databases(sock)
            if exposed_dbs:
                vulnerabilities.append(Vulnerability(
                    name='Exposed Databases',
                    description=f'Found {len(exposed_dbs)} exposed databases',
                    level=VulnerabilityLevel.HIGH,
                    recommendation='Restrict database access using network ACLs',
                    evidence=f'Databases: {", ".join(exposed_dbs)}'
                ))
            
            # Check for weak configuration
            config_issues = self._check_mongodb_configuration(sock)
            vulnerabilities.extend(config_issues)
            
            sock.close()
            
        except Exception as e:
            pass
        
        # Calculate security score
        security_score = self._calculate_security_score(vulnerabilities)
        risk_level = self._determine_risk_level(security_score)
        
        return SecurityAssessment(
            ip=ip,
            port=port,
            database_type='MongoDB',
            vulnerabilities=vulnerabilities,
            security_score=security_score,
            risk_level=risk_level,
            assessment_time=time.time() - start_time
        )
    
    def _check_mongodb_auth_required(self, sock: socket.socket) -> bool:
        """
        Check if MongoDB requires authentication.
        
        Args:
            sock: Socket connection
            
        Returns:
            True if authentication is required
        """
        try:
            # Send listDatabases command
            cmd = self._build_mongodb_command('listDatabases')
            sock.send(cmd)
            
            response = sock.recv(4096).decode('utf-8', errors='ignore')
            
            # Check for authentication error
            if 'not authorized' in response.lower() or 'unauthorized' in response.lower():
                return True
            
            return False
            
        except Exception:
            return True
    
    def _check_mongodb_exposed_databases(self, sock: socket.socket) -> List[str]:
        """
        Check for exposed MongoDB databases.
        
        Args:
            sock: Socket connection
            
        Returns:
            List of exposed database names
        """
        exposed_dbs = []
        
        try:
            # Send listDatabases command
            cmd = self._build_mongodb_command('listDatabases')
            sock.send(cmd)
            
            response = sock.recv(4096).decode('utf-8', errors='ignore')
            
            # Parse database names
            db_matches = re.findall(r'"name"\s*:\s*"([^"]+)"', response)
            exposed_dbs = [db for db in db_matches if db not in ['admin', 'local', 'config']]
            
        except Exception:
            pass
        
        return exposed_dbs
    
    def _check_mongodb_configuration(self, sock: socket.socket) -> List[Vulnerability]:
        """
        Check MongoDB configuration for security issues.
        
        Args:
            sock: Socket connection
            
        Returns:
            List of vulnerabilities
        """
        vulnerabilities = []
        
        try:
            # Send getCmdLineOpts command
            cmd = self._build_mongodb_command('getCmdLineOpts')
            sock.send(cmd)
            
            response = sock.recv(4096).decode('utf-8', errors='ignore')
            
            # Check for insecure options
            if '--noauth' in response.lower():
                vulnerabilities.append(Vulnerability(
                    name='Authentication Disabled',
                    description='MongoDB started with --noauth option',
                    level=VulnerabilityLevel.CRITICAL,
                    recommendation='Remove --noauth option from MongoDB configuration',
                    evidence='--noauth flag detected in command line options'
                ))
            
            if '--bind_ip' not in response.lower():
                vulnerabilities.append(Vulnerability(
                    name='Unrestricted Network Binding',
                    description='MongoDB may be listening on all network interfaces',
                    level=VulnerabilityLevel.MEDIUM,
                    recommendation='Configure MongoDB to bind only to specific IP addresses',
                    evidence='No --bind_ip option detected'
                ))
            
        except Exception:
            pass
        
        return vulnerabilities
    
    def assess_elasticsearch(
        self,
        ip: str,
        port: int = 9200
    ) -> SecurityAssessment:
        """
        Assess Elasticsearch security.
        
        Args:
            ip: IP address
            port: Port number
            
        Returns:
            SecurityAssessment object
        """
        import time
        start_time = time.time()
        
        vulnerabilities = []
        
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(self.timeout)
            sock.connect((ip, port))
            
            # Check if authentication is required
            auth_required = self._check_elasticsearch_auth_required(sock)
            
            if not auth_required:
                vulnerabilities.append(Vulnerability(
                    name='No Authentication Required',
                    description='Elasticsearch instance does not require authentication',
                    level=VulnerabilityLevel.CRITICAL,
                    recommendation='Enable X-Pack security or use reverse proxy with authentication',
                    evidence='Successfully accessed without credentials'
                ))
            
            # Check for exposed indices
            exposed_indices = self._check_elasticsearch_exposed_indices(sock)
            if exposed_indices:
                vulnerabilities.append(Vulnerability(
                    name='Exposed Indices',
                    description=f'Found {len(exposed_indices)} exposed indices',
                    level=VulnerabilityLevel.HIGH,
                    recommendation='Restrict index access using security policies',
                    evidence=f'Indices: {", ".join(exposed_indices)}'
                ))
            
            # Check for sensitive endpoints
            sensitive_endpoints = self._check_elasticsearch_sensitive_endpoints(sock)
            vulnerabilities.extend(sensitive_endpoints)
            
            sock.close()
            
        except Exception as e:
            pass
        
        # Calculate security score
        security_score = self._calculate_security_score(vulnerabilities)
        risk_level = self._determine_risk_level(security_score)
        
        return SecurityAssessment(
            ip=ip,
            port=port,
            database_type='Elasticsearch',
            vulnerabilities=vulnerabilities,
            security_score=security_score,
            risk_level=risk_level,
            assessment_time=time.time() - start_time
        )
    
    def _check_elasticsearch_auth_required(self, sock: socket.socket) -> bool:
        """
        Check if Elasticsearch requires authentication.
        
        Args:
            sock: Socket connection
            
        Returns:
            True if authentication is required
        """
        try:
            # Send HTTP request to root endpoint
            request = b'GET / HTTP/1.1\r\n'
            request += f'Host: {sock.getpeername()[0]}\r\n'.encode()
            request += b'Connection: close\r\n'
            request += b'\r\n'
            
            sock.send(request)
            response = sock.recv(4096).decode('utf-8', errors='ignore')
            
            # Check for 401 Unauthorized
            if '401' in response or 'unauthorized' in response.lower():
                return True
            
            return False
            
        except Exception:
            return True
    
    def _check_elasticsearch_exposed_indices(self, sock: socket.socket) -> List[str]:
        """
        Check for exposed Elasticsearch indices.
        
        Args:
            sock: Socket connection
            
        Returns:
            List of exposed index names
        """
        exposed_indices = []
        
        try:
            # Send HTTP request to _cat/indices endpoint
            request = b'GET /_cat/indices?format=json HTTP/1.1\r\n'
            request += f'Host: {sock.getpeername()[0]}\r\n'.encode()
            request += b'Connection: close\r\n'
            request += b'\r\n'
            
            sock.send(request)
            response = sock.recv(65536).decode('utf-8', errors='ignore')
            
            # Parse index names
            index_matches = re.findall(r'"index"\s*:\s*"([^"]+)"', response)
            exposed_indices = [idx for idx in index_matches if not idx.startswith('.')]
            
        except Exception:
            pass
        
        return exposed_indices
    
    def _check_elasticsearch_sensitive_endpoints(self, sock: socket.socket) -> List[Vulnerability]:
        """
        Check for exposed sensitive Elasticsearch endpoints.
        
        Args:
            sock: Socket connection
            
        Returns:
            List of vulnerabilities
        """
        vulnerabilities = []
        
        sensitive_endpoints = [
            ('/_cat/indices', 'Index listing'),
            ('/_cat/nodes', 'Node information'),
            ('/_cluster/health', 'Cluster health'),
            ('/_cluster/settings', 'Cluster settings'),
            ('/_nodes', 'Node details'),
            ('/_search', 'Search endpoint'),
        ]
        
        for endpoint, description in sensitive_endpoints:
            try:
                request = f'GET {endpoint} HTTP/1.1\r\n'
                request += f'Host: {sock.getpeername()[0]}\r\n'
                request += 'Connection: close\r\n'
                request += '\r\n'
                
                sock.send(request.encode())
                response = sock.recv(4096).decode('utf-8', errors='ignore')
                
                if '200' in response:
                    vulnerabilities.append(Vulnerability(
                        name=f'Exposed {description}',
                        description=f'{description} endpoint is accessible',
                        level=VulnerabilityLevel.MEDIUM,
                        recommendation=f'Restrict access to {endpoint} endpoint',
                        evidence=f'Endpoint {endpoint} returned 200 OK'
                    ))
                    
            except Exception:
                continue
        
        return vulnerabilities
    
    def assess_redis(
        self,
        ip: str,
        port: int = 6379
    ) -> SecurityAssessment:
        """
        Assess Redis security.
        
        Args:
            ip: IP address
            port: Port number
            
        Returns:
            SecurityAssessment object
        """
        import time
        start_time = time.time()
        
        vulnerabilities = []
        
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(self.timeout)
            sock.connect((ip, port))
            
            # Check if authentication is required
            auth_required = self._check_redis_auth_required(sock)
            
            if not auth_required:
                vulnerabilities.append(Vulnerability(
                    name='No Authentication Required',
                    description='Redis instance does not require authentication',
                    level=VulnerabilityLevel.CRITICAL,
                    recommendation='Enable Redis AUTH in configuration',
                    evidence='Successfully connected without password'
                ))
            
            # Check for exposed commands
            exposed_commands = self._check_redis_exposed_commands(sock)
            vulnerabilities.extend(exposed_commands)
            
            # Check for sensitive data
            sensitive_data = self._check_redis_sensitive_data(sock)
            vulnerabilities.extend(sensitive_data)
            
            sock.close()
            
        except Exception as e:
            pass
        
        # Calculate security score
        security_score = self._calculate_security_score(vulnerabilities)
        risk_level = self._determine_risk_level(security_score)
        
        return SecurityAssessment(
            ip=ip,
            port=port,
            database_type='Redis',
            vulnerabilities=vulnerabilities,
            security_score=security_score,
            risk_level=risk_level,
            assessment_time=time.time() - start_time
        )
    
    def _check_redis_auth_required(self, sock: socket.socket) -> bool:
        """
        Check if Redis requires authentication.
        
        Args:
            sock: Socket connection
            
        Returns:
            True if authentication is required
        """
        try:
            # Send INFO command
            sock.send(b'INFO\r\n')
            response = sock.recv(4096).decode('utf-8', errors='ignore')
            
            # Check for NOAUTH error
            if 'NOAUTH' in response or 'requirepass' in response.lower():
                return True
            
            return False
            
        except Exception:
            return True
    
    def _check_redis_exposed_commands(self, sock: socket.socket) -> List[Vulnerability]:
        """
        Check for exposed Redis commands.
        
        Args:
            sock: Socket connection
            
        Returns:
            List of vulnerabilities
        """
        vulnerabilities = []
        
        dangerous_commands = [
            ('CONFIG', 'Configuration access'),
            ('FLUSHALL', 'Database flush'),
            ('FLUSHDB', 'Database flush'),
            ('DEBUG', 'Debug commands'),
            ('EVAL', 'Lua script execution'),
            ('SCRIPT', 'Script management'),
        ]
        
        for command, description in dangerous_commands:
            try:
                # Try to execute command
                cmd = f'{command}\r\n'.encode()
                sock.send(cmd)
                response = sock.recv(1024).decode('utf-8', errors='ignore')
                
                if 'ERR' not in response and 'NOAUTH' not in response:
                    vulnerabilities.append(Vulnerability(
                        name=f'Exposed {command} Command',
                        description=f'{description} command is accessible',
                        level=VulnerabilityLevel.HIGH,
                        recommendation=f'Disable {command} command using rename-command',
                        evidence=f'Command {command} executed successfully'
                    ))
                    
            except Exception:
                continue
        
        return vulnerabilities
    
    def _check_redis_sensitive_data(self, sock: socket.socket) -> List[Vulnerability]:
        """
        Check for sensitive data in Redis.
        
        Args:
            sock: Socket connection
            
        Returns:
            List of vulnerabilities
        """
        vulnerabilities = []
        
        try:
            # Send KEYS command to find sensitive keys
            sock.send(b'KEYS *\r\n')
            response = sock.recv(65536).decode('utf-8', errors='ignore')
            
            # Look for sensitive key patterns
            sensitive_patterns = [
                '*password*', '*secret*', '*token*', '*key*',
                '*credential*', '*auth*', '*session*',
            ]
            
            for pattern in sensitive_patterns:
                if pattern.replace('*', '') in response.lower():
                    vulnerabilities.append(Vulnerability(
                        name='Sensitive Data Exposure',
                        description=f'Found keys matching pattern: {pattern}',
                        level=VulnerabilityLevel.HIGH,
                        recommendation='Review and secure sensitive data in Redis',
                        evidence=f'Keys matching {pattern} found'
                    ))
                    
        except Exception:
            pass
        
        return vulnerabilities
    
    def _build_mongodb_command(self, command: str) -> bytes:
        """
        Build MongoDB command packet.
        
        Args:
            command: Command name
            
        Returns:
            MongoDB command bytes
        """
        # Simplified MongoDB command builder
        cmd = b'\x3f\x00\x00\x00'  # Length
        cmd += b'\x00\x00\x00\x00'  # Request ID
        cmd += b'\x00\x00\x00\x00'  # Response to
        cmd += b'\xd4\x07\x00\x00'  # OP_QUERY
        cmd += b'\x00\x00\x00\x00'  # Flags
        cmd += b'\x61\x64\x6d\x69\x6e\x2e\x24\x63\x6d\x64\x00'  # admin.$cmd
        cmd += b'\x00\x00\x00\x00'  # Skip
        cmd += b'\x01\x00\x00\x00'  # Return
        cmd += b'\x08\x00\x00\x00'  # Doc length
        cmd += b'\x10'  # Int32
        cmd += f'{command}\x00'.encode()
        cmd += b'\x01\x00\x00\x00'  # Value: 1
        cmd += b'\x00'  # End
        return cmd
    
    def _calculate_security_score(self, vulnerabilities: List[Vulnerability]) -> int:
        """
        Calculate security score based on vulnerabilities.
        
        Args:
            vulnerabilities: List of vulnerabilities
            
        Returns:
            Security score (0-100)
        """
        score = 100
        
        for vuln in vulnerabilities:
            if vuln.level == VulnerabilityLevel.CRITICAL:
                score -= 30
            elif vuln.level == VulnerabilityLevel.HIGH:
                score -= 20
            elif vuln.level == VulnerabilityLevel.MEDIUM:
                score -= 10
            elif vuln.level == VulnerabilityLevel.LOW:
                score -= 5
            elif vuln.level == VulnerabilityLevel.INFO:
                score -= 1
        
        return max(0, score)
    
    def _determine_risk_level(self, security_score: int) -> str:
        """
        Determine risk level based on security score.
        
        Args:
            security_score: Security score (0-100)
            
        Returns:
            Risk level string
        """
        if security_score >= 80:
            return 'Low'
        elif security_score >= 60:
            return 'Medium'
        elif security_score >= 40:
            return 'High'
        else:
            return 'Critical'
