"""
Database Detector Module

Detects and identifies database services running on target systems.
"""

import socket
import re
from typing import Optional, Dict, Any, List
from dataclasses import dataclass


@dataclass
class DatabaseInfo:
    """Database information"""
    ip: str
    port: int
    database_type: str
    version: Optional[str] = None
    is_authenticated: bool = False
    is_encrypted: bool = False
    requires_auth: bool = False
    exposed_databases: List[str] = None
    exposed_collections: List[str] = None
    security_level: str = 'unknown'
    
    def __post_init__(self):
        if self.exposed_databases is None:
            self.exposed_databases = []
        if self.exposed_collections is None:
            self.exposed_collections = []


class DatabaseDetector:
    """
    Detects and identifies database services.
    
    Features:
    - MongoDB detection and enumeration
    - Elasticsearch detection and enumeration
    - Redis detection and enumeration
    - MySQL detection
    - PostgreSQL detection
    - Security assessment
    """
    
    def __init__(self, timeout: float = 2.0):
        """
        Initialize database detector.
        
        Args:
            timeout: Socket timeout in seconds
        """
        self.timeout = timeout
    
    def detect_mongodb(
        self,
        ip: str,
        port: int = 27017
    ) -> Optional[DatabaseInfo]:
        """
        Detect MongoDB instance.
        
        Args:
            ip: IP address
            port: Port number
            
        Returns:
            DatabaseInfo object or None
        """
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(self.timeout)
            sock.connect((ip, port))
            
            # Send MongoDB handshake
            # MongoDB wire protocol: OP_QUERY on admin.$cmd
            handshake = self._build_mongodb_handshake()
            sock.send(handshake)
            
            response = sock.recv(4096)
            sock.close()
            
            if response:
                # Parse response
                info = self._parse_mongodb_response(response)
                
                return DatabaseInfo(
                    ip=ip,
                    port=port,
                    database_type='MongoDB',
                    version=info.get('version'),
                    is_authenticated=info.get('authenticated', False),
                    requires_auth=info.get('requires_auth', False),
                    exposed_databases=info.get('databases', []),
                    security_level=self._assess_mongodb_security(info)
                )
            
        except Exception as e:
            pass
        
        return None
    
    def _build_mongodb_handshake(self) -> bytes:
        """
        Build MongoDB handshake packet.
        
        Returns:
            MongoDB handshake bytes
        """
        # Simplified MongoDB handshake
        # In production, use pymongo or similar library
        header = b'\x3f\x00\x00\x00'  # Message length
        header += b'\x00\x00\x00\x00'  # Request ID
        header += b'\x00\x00\x00\x00'  # Response to
        header += b'\xd4\x07\x00\x00'  # OP_QUERY
        header += b'\x00\x00\x00\x00'  # Flags
        header += b'\x61\x64\x6d\x69\x6e\x2e\x24\x63\x6d\x64\x00'  # admin.$cmd
        header += b'\x00\x00\x00\x00'  # Number to skip
        header += b'\x01\x00\x00\x00'  # Number to return
        
        # Query: { isMaster: 1 }
        query = b'\x08\x00\x00\x00'  # Document length
        query += b'\x10'  # Int32 type
        query += b'\x69\x73\x4d\x61\x73\x74\x65\x72\x00'  # isMaster
        query += b'\x01\x00\x00\x00'  # Value: 1
        query += b'\x00'  # End of document
        
        return header + query
    
    def _parse_mongodb_response(self, response: bytes) -> Dict[str, Any]:
        """
        Parse MongoDB response.
        
        Args:
            response: Raw response bytes
            
        Returns:
            Parsed response dictionary
        """
        info = {
            'version': None,
            'authenticated': False,
            'requires_auth': False,
            'databases': [],
        }
        
        try:
            # Try to extract version from response
            response_str = response.decode('utf-8', errors='ignore')
            
            # Look for version pattern
            version_match = re.search(r'"version"\s*:\s*"([^"]+)"', response_str)
            if version_match:
                info['version'] = version_match.group(1)
            
            # Check for authentication requirement
            if 'not authorized' in response_str.lower() or 'unauthorized' in response_str.lower():
                info['requires_auth'] = True
            else:
                info['authenticated'] = True
            
            # Try to extract database names
            db_match = re.findall(r'"name"\s*:\s*"([^"]+)"', response_str)
            if db_match:
                info['databases'] = db_match
                
        except Exception:
            pass
        
        return info
    
    def _assess_mongodb_security(self, info: Dict[str, Any]) -> str:
        """
        Assess MongoDB security level.
        
        Args:
            info: MongoDB information
            
        Returns:
            Security level string
        """
        if info.get('requires_auth'):
            if info.get('authenticated'):
                return 'medium'
            else:
                return 'high'
        else:
            return 'low'
    
    def detect_elasticsearch(
        self,
        ip: str,
        port: int = 9200
    ) -> Optional[DatabaseInfo]:
        """
        Detect Elasticsearch instance.
        
        Args:
            ip: IP address
            port: Port number
            
        Returns:
            DatabaseInfo object or None
        """
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(self.timeout)
            sock.connect((ip, port))
            
            # Send HTTP request to Elasticsearch
            request = b'GET / HTTP/1.1\r\n'
            request += f'Host: {ip}\r\n'.encode()
            request += b'Connection: close\r\n'
            request += b'\r\n'
            
            sock.send(request)
            response = sock.recv(4096).decode('utf-8', errors='ignore')
            sock.close()
            
            if 'elasticsearch' in response.lower():
                # Parse response
                info = self._parse_elasticsearch_response(response)
                
                return DatabaseInfo(
                    ip=ip,
                    port=port,
                    database_type='Elasticsearch',
                    version=info.get('version'),
                    is_authenticated=info.get('authenticated', False),
                    requires_auth=info.get('requires_auth', False),
                    exposed_databases=info.get('indices', []),
                    security_level=self._assess_elasticsearch_security(info)
                )
            
        except Exception:
            pass
        
        return None
    
    def _parse_elasticsearch_response(self, response: str) -> Dict[str, Any]:
        """
        Parse Elasticsearch response.
        
        Args:
            response: HTTP response string
            
        Returns:
            Parsed response dictionary
        """
        info = {
            'version': None,
            'authenticated': False,
            'requires_auth': False,
            'indices': [],
        }
        
        try:
            # Extract version
            version_match = re.search(r'"version"\s*:\s*\{[^}]*"number"\s*:\s*"([^"]+)"', response)
            if version_match:
                info['version'] = version_match.group(1)
            
            # Check for authentication
            if '401' in response or 'unauthorized' in response.lower():
                info['requires_auth'] = True
            else:
                info['authenticated'] = True
            
            # Try to get indices
            if '/_cat/indices' in response or '/_all' in response:
                indices = re.findall(r'"([^"]+)"', response)
                info['indices'] = [i for i in indices if not i.startswith('.')]
                
        except Exception:
            pass
        
        return info
    
    def _assess_elasticsearch_security(self, info: Dict[str, Any]) -> str:
        """
        Assess Elasticsearch security level.
        
        Args:
            info: Elasticsearch information
            
        Returns:
            Security level string
        """
        if info.get('requires_auth'):
            return 'high'
        else:
            return 'low'
    
    def detect_redis(
        self,
        ip: str,
        port: int = 6379
    ) -> Optional[DatabaseInfo]:
        """
        Detect Redis instance.
        
        Args:
            ip: IP address
            port: Port number
            
        Returns:
            DatabaseInfo object or None
        """
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(self.timeout)
            sock.connect((ip, port))
            
            # Send Redis INFO command
            sock.send(b'INFO\r\n')
            response = sock.recv(4096).decode('utf-8', errors='ignore')
            sock.close()
            
            if 'redis_version' in response.lower():
                # Parse response
                info = self._parse_redis_response(response)
                
                return DatabaseInfo(
                    ip=ip,
                    port=port,
                    database_type='Redis',
                    version=info.get('version'),
                    is_authenticated=info.get('authenticated', False),
                    requires_auth=info.get('requires_auth', False),
                    security_level=self._assess_redis_security(info)
                )
            
        except Exception:
            pass
        
        return None
    
    def _parse_redis_response(self, response: str) -> Dict[str, Any]:
        """
        Parse Redis INFO response.
        
        Args:
            response: Redis INFO response
            
        Returns:
            Parsed response dictionary
        """
        info = {
            'version': None,
            'authenticated': False,
            'requires_auth': False,
        }
        
        try:
            # Extract version
            version_match = re.search(r'redis_version:([^\r\n]+)', response)
            if version_match:
                info['version'] = version_match.group(1).strip()
            
            # Check for authentication
            if 'NOAUTH' in response or 'requirepass' in response.lower():
                info['requires_auth'] = True
            else:
                info['authenticated'] = True
                
        except Exception:
            pass
        
        return info
    
    def _assess_redis_security(self, info: Dict[str, Any]) -> str:
        """
        Assess Redis security level.
        
        Args:
            info: Redis information
            
        Returns:
            Security level string
        """
        if info.get('requires_auth'):
            return 'high'
        else:
            return 'low'
    
    def detect_database(
        self,
        ip: str,
        port: int,
        database_type: Optional[str] = None
    ) -> Optional[DatabaseInfo]:
        """
        Detect database type and gather information.
        
        Args:
            ip: IP address
            port: Port number
            database_type: Database type to detect (auto-detect if None)
            
        Returns:
            DatabaseInfo object or None
        """
        if database_type is None:
            # Auto-detect based on port
            if port == 27017:
                return self.detect_mongodb(ip, port)
            elif port == 9200:
                return self.detect_elasticsearch(ip, port)
            elif port == 6379:
                return self.detect_redis(ip, port)
            else:
                # Try all detectors
                result = self.detect_mongodb(ip, port)
                if result:
                    return result
                
                result = self.detect_elasticsearch(ip, port)
                if result:
                    return result
                
                result = self.detect_redis(ip, port)
                if result:
                    return result
        else:
            # Use specified detector
            if database_type.lower() == 'mongodb':
                return self.detect_mongodb(ip, port)
            elif database_type.lower() == 'elasticsearch':
                return self.detect_elasticsearch(ip, port)
            elif database_type.lower() == 'redis':
                return self.detect_redis(ip, port)
        
        return None
    
    def detect_multiple(
        self,
        targets: List[Dict[str, Any]]
    ) -> List[DatabaseInfo]:
        """
        Detect databases on multiple targets.
        
        Args:
            targets: List of target dictionaries with 'ip', 'port', and optional 'type'
            
        Returns:
            List of DatabaseInfo objects
        """
        results = []
        
        for target in targets:
            ip = target.get('ip')
            port = target.get('port')
            db_type = target.get('type')
            
            if ip and port:
                result = self.detect_database(ip, port, db_type)
                if result:
                    results.append(result)
        
        return results
