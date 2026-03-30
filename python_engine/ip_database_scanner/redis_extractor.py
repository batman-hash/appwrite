"""
Redis Email Extractor Module

Extracts email addresses from Redis databases.
"""

import re
import socket
from typing import List, Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class RedisExtractionResult:
    """Redis extraction result"""
    ip: str
    port: int
    keys_scanned: int
    emails: List[str]
    keys_with_emails: List[str]
    extraction_time: float


class RedisExtractor:
    """
    Extracts email addresses from Redis databases.
    
    Features:
    - Connect to Redis instances
    - Scan keys for email patterns
    - Extract emails from various data types
    - Handle authentication
    - Support for Redis clusters
    """
    
    # Email regex pattern
    EMAIL_PATTERN = re.compile(
        r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    )
    
    # Common email-related key patterns
    EMAIL_KEY_PATTERNS = [
        '*email*', '*mail*', '*user*', '*contact*',
        '*account*', '*profile*', '*member*',
    ]
    
    def __init__(self, timeout: float = 5.0):
        """
        Initialize Redis extractor.
        
        Args:
            timeout: Socket timeout in seconds
        """
        self.timeout = timeout
    
    def extract_emails(
        self,
        ip: str,
        port: int = 6379,
        password: Optional[str] = None,
        pattern: str = '*',
        max_keys: int = 10000
    ) -> List[RedisExtractionResult]:
        """
        Extract emails from Redis instance.
        
        Args:
            ip: IP address
            port: Port number
            password: Authentication password
            pattern: Key pattern to scan
            max_keys: Maximum number of keys to scan
            
        Returns:
            List of RedisExtractionResult objects
        """
        import time
        start_time = time.time()
        
        results = []
        
        try:
            # Try to connect using redis-py if available
            try:
                import redis
                results = self._extract_with_library(
                    ip, port, password, pattern, max_keys, start_time
                )
            except ImportError:
                # Fall back to raw socket extraction
                results = self._extract_with_socket(
                    ip, port, password, pattern, max_keys, start_time
                )
            
        except Exception as e:
            print(f"Error extracting from Redis at {ip}:{port}: {e}")
        
        return results
    
    def _extract_with_library(
        self,
        ip: str,
        port: int,
        password: Optional[str],
        pattern: str,
        max_keys: int,
        start_time: float
    ) -> List[RedisExtractionResult]:
        """
        Extract emails using redis-py library.
        
        Args:
            ip: IP address
            port: Port number
            password: Password
            pattern: Key pattern
            max_keys: Maximum keys to scan
            start_time: Start time
            
        Returns:
            List of RedisExtractionResult objects
        """
        import time
        import redis
        
        results = []
        
        try:
            # Connect to Redis
            if password:
                r = redis.Redis(
                    host=ip,
                    port=port,
                    password=password,
                    socket_timeout=self.timeout,
                    decode_responses=True
                )
            else:
                r = redis.Redis(
                    host=ip,
                    port=port,
                    socket_timeout=self.timeout,
                    decode_responses=True
                )
            
            # Scan keys
            emails = []
            keys_with_emails = []
            keys_scanned = 0
            
            # Use SCAN to iterate through keys
            cursor = 0
            while True:
                cursor, keys = r.scan(cursor, match=pattern, count=100)
                
                for key in keys:
                    if keys_scanned >= max_keys:
                        break
                    
                    keys_scanned += 1
                    
                    try:
                        # Get key type
                        key_type = r.type(key)
                        
                        # Extract value based on type
                        value = None
                        if key_type == 'string':
                            value = r.get(key)
                        elif key_type == 'hash':
                            value = r.hgetall(key)
                        elif key_type == 'list':
                            value = r.lrange(key, 0, -1)
                        elif key_type == 'set':
                            value = r.smembers(key)
                        elif key_type == 'zset':
                            value = r.zrange(key, 0, -1)
                        
                        # Extract emails from value
                        if value:
                            extracted = self._extract_emails_from_value(value)
                            if extracted:
                                emails.extend(extracted)
                                keys_with_emails.append(key)
                                
                    except Exception:
                        continue
                
                if cursor == 0 or keys_scanned >= max_keys:
                    break
            
            # Remove duplicates
            emails = list(set(emails))
            
            if emails:
                results.append(RedisExtractionResult(
                    ip=ip,
                    port=port,
                    keys_scanned=keys_scanned,
                    emails=emails,
                    keys_with_emails=keys_with_emails,
                    extraction_time=time.time() - start_time
                ))
            
        except Exception as e:
            print(f"Error with redis-py: {e}")
        
        return results
    
    def _extract_with_socket(
        self,
        ip: str,
        port: int,
        password: Optional[str],
        pattern: str,
        max_keys: int,
        start_time: float
    ) -> List[RedisExtractionResult]:
        """
        Extract emails using raw socket connection.
        
        Args:
            ip: IP address
            port: Port number
            password: Password
            pattern: Key pattern
            max_keys: Maximum keys to scan
            start_time: Start time
            
        Returns:
            List of RedisExtractionResult objects
        """
        import time
        
        results = []
        
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(self.timeout)
            sock.connect((ip, port))
            
            # Authenticate if password provided
            if password:
                auth_cmd = f'AUTH {password}\r\n'.encode()
                sock.send(auth_cmd)
                response = sock.recv(1024)
            
            # Scan keys
            emails = []
            keys_with_emails = []
            keys_scanned = 0
            
            # Use SCAN command
            cursor = 0
            while True:
                scan_cmd = f'SCAN {cursor} MATCH {pattern} COUNT 100\r\n'.encode()
                sock.send(scan_cmd)
                
                response = sock.recv(65536).decode('utf-8', errors='ignore')
                
                # Parse SCAN response
                new_cursor, keys = self._parse_scan_response(response)
                
                for key in keys:
                    if keys_scanned >= max_keys:
                        break
                    
                    keys_scanned += 1
                    
                    try:
                        # Get key type
                        type_cmd = f'TYPE {key}\r\n'.encode()
                        sock.send(type_cmd)
                        type_response = sock.recv(1024).decode('utf-8', errors='ignore')
                        
                        key_type = self._parse_type_response(type_response)
                        
                        # Get value based on type
                        value = None
                        if key_type == 'string':
                            get_cmd = f'GET {key}\r\n'.encode()
                            sock.send(get_cmd)
                            value_response = sock.recv(65536).decode('utf-8', errors='ignore')
                            value = self._parse_get_response(value_response)
                        elif key_type == 'hash':
                            hgetall_cmd = f'HGETALL {key}\r\n'.encode()
                            sock.send(hgetall_cmd)
                            value_response = sock.recv(65536).decode('utf-8', errors='ignore')
                            value = self._parse_hgetall_response(value_response)
                        elif key_type == 'list':
                            lrange_cmd = f'LRANGE {key} 0 -1\r\n'.encode()
                            sock.send(lrange_cmd)
                            value_response = sock.recv(65536).decode('utf-8', errors='ignore')
                            value = self._parse_lrange_response(value_response)
                        
                        # Extract emails from value
                        if value:
                            extracted = self._extract_emails_from_value(value)
                            if extracted:
                                emails.extend(extracted)
                                keys_with_emails.append(key)
                                
                    except Exception:
                        continue
                
                cursor = int(new_cursor)
                if cursor == 0 or keys_scanned >= max_keys:
                    break
            
            # Remove duplicates
            emails = list(set(emails))
            
            if emails:
                results.append(RedisExtractionResult(
                    ip=ip,
                    port=port,
                    keys_scanned=keys_scanned,
                    emails=emails,
                    keys_with_emails=keys_with_emails,
                    extraction_time=time.time() - start_time
                ))
            
            sock.close()
            
        except Exception as e:
            print(f"Error with socket extraction: {e}")
        
        return results
    
    def _parse_scan_response(self, response: str) -> tuple:
        """
        Parse Redis SCAN response.
        
        Args:
            response: Redis response string
            
        Returns:
            Tuple of (cursor, keys)
        """
        cursor = 0
        keys = []
        
        try:
            lines = response.strip().split('\r\n')
            if len(lines) >= 2:
                cursor = int(lines[0].replace('*', '').replace('$', ''))
                
                # Parse keys
                for line in lines[1:]:
                    if line.startswith('$'):
                        continue
                    if line and not line.startswith('*'):
                        keys.append(line)
                        
        except Exception:
            pass
        
        return cursor, keys
    
    def _parse_type_response(self, response: str) -> str:
        """
        Parse Redis TYPE response.
        
        Args:
            response: Redis response string
            
        Returns:
            Key type string
        """
        try:
            lines = response.strip().split('\r\n')
            for line in lines:
                if line.startswith('+'):
                    return line[1:].strip()
        except Exception:
            pass
        
        return 'none'
    
    def _parse_get_response(self, response: str) -> Optional[str]:
        """
        Parse Redis GET response.
        
        Args:
            response: Redis response string
            
        Returns:
            Value string or None
        """
        try:
            lines = response.strip().split('\r\n')
            for line in lines:
                if line.startswith('$'):
                    continue
                if line and not line.startswith('*'):
                    return line
        except Exception:
            pass
        
        return None
    
    def _parse_hgetall_response(self, response: str) -> Optional[Dict[str, str]]:
        """
        Parse Redis HGETALL response.
        
        Args:
            response: Redis response string
            
        Returns:
            Dictionary of field-value pairs or None
        """
        try:
            result = {}
            lines = response.strip().split('\r\n')
            
            i = 0
            while i < len(lines):
                line = lines[i]
                if line.startswith('*'):
                    i += 1
                    continue
                if line.startswith('$'):
                    i += 1
                    continue
                
                if line and not line.startswith('*'):
                    field = line
                    i += 1
                    if i < len(lines):
                        value = lines[i]
                        result[field] = value
                i += 1
            
            return result if result else None
            
        except Exception:
            pass
        
        return None
    
    def _parse_lrange_response(self, response: str) -> Optional[List[str]]:
        """
        Parse Redis LRANGE response.
        
        Args:
            response: Redis response string
            
        Returns:
            List of values or None
        """
        try:
            result = []
            lines = response.strip().split('\r\n')
            
            for line in lines:
                if line.startswith('*'):
                    continue
                if line.startswith('$'):
                    continue
                if line and not line.startswith('*'):
                    result.append(line)
            
            return result if result else None
            
        except Exception:
            pass
        
        return None
    
    def _extract_emails_from_value(self, value: Any) -> List[str]:
        """
        Extract emails from Redis value.
        
        Args:
            value: Redis value (string, dict, list, set)
            
        Returns:
            List of email addresses
        """
        emails = []
        
        if isinstance(value, str):
            emails.extend(self._extract_emails_from_string(value))
        elif isinstance(value, dict):
            for key, val in value.items():
                if isinstance(val, str):
                    emails.extend(self._extract_emails_from_string(val))
        elif isinstance(value, (list, set)):
            for item in value:
                if isinstance(item, str):
                    emails.extend(self._extract_emails_from_string(item))
        
        return list(set(emails))
    
    def _extract_emails_from_string(self, text: str) -> List[str]:
        """
        Extract email addresses from string.
        
        Args:
            text: Text to search
            
        Returns:
            List of email addresses
        """
        return self.EMAIL_PATTERN.findall(text)
