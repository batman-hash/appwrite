"""
Elasticsearch Email Extractor Module

Extracts email addresses from Elasticsearch databases.
"""

import re
import socket
import json
from typing import List, Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class ElasticsearchExtractionResult:
    """Elasticsearch extraction result"""
    ip: str
    port: int
    index: str
    emails: List[str]
    total_documents: int
    documents_with_emails: int
    extraction_time: float


class ElasticsearchExtractor:
    """
    Extracts email addresses from Elasticsearch databases.
    
    Features:
    - Connect to Elasticsearch instances
    - Enumerate indices
    - Search for email patterns in documents
    - Extract emails from various field types
    - Handle authentication
    """
    
    # Email regex pattern
    EMAIL_PATTERN = re.compile(
        r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    )
    
    # Common email field names
    EMAIL_FIELDS = [
        'email', 'email_address', 'emailAddress', 'e_mail',
        'mail', 'user_email', 'userEmail', 'contact_email',
        'contactEmail', 'primary_email', 'primaryEmail',
        'secondary_email', 'secondaryEmail', 'work_email',
        'workEmail', 'personal_email', 'personalEmail',
    ]
    
    def __init__(self, timeout: float = 5.0):
        """
        Initialize Elasticsearch extractor.
        
        Args:
            timeout: Socket timeout in seconds
        """
        self.timeout = timeout
    
    def extract_emails(
        self,
        ip: str,
        port: int = 9200,
        index: Optional[str] = None,
        username: Optional[str] = None,
        password: Optional[str] = None
    ) -> List[ElasticsearchExtractionResult]:
        """
        Extract emails from Elasticsearch instance.
        
        Args:
            ip: IP address
            port: Port number
            index: Specific index to scan (None for all)
            username: Authentication username
            password: Authentication password
            
        Returns:
            List of ElasticsearchExtractionResult objects
        """
        import time
        start_time = time.time()
        
        results = []
        
        try:
            # Try to connect using elasticsearch-py if available
            try:
                from elasticsearch import Elasticsearch
                results = self._extract_with_library(
                    ip, port, index, username, password, start_time
                )
            except ImportError:
                # Fall back to raw socket extraction
                results = self._extract_with_socket(
                    ip, port, index, start_time
                )
            
        except Exception as e:
            print(f"Error extracting from Elasticsearch at {ip}:{port}: {e}")
        
        return results
    
    def _extract_with_library(
        self,
        ip: str,
        port: int,
        index: Optional[str],
        username: Optional[str],
        password: Optional[str],
        start_time: float
    ) -> List[ElasticsearchExtractionResult]:
        """
        Extract emails using elasticsearch-py library.
        
        Args:
            ip: IP address
            port: Port number
            index: Specific index
            username: Username
            password: Password
            start_time: Start time
            
        Returns:
            List of ElasticsearchExtractionResult objects
        """
        import time
        from elasticsearch import Elasticsearch
        
        results = []
        
        try:
            # Connect to Elasticsearch
            if username and password:
                es = Elasticsearch(
                    [f'http://{ip}:{port}'],
                    http_auth=(username, password),
                    timeout=self.timeout
                )
            else:
                es = Elasticsearch(
                    [f'http://{ip}:{port}'],
                    timeout=self.timeout
                )
            
            # Get list of indices
            if index:
                indices = [index]
            else:
                try:
                    indices = list(es.indices.get_alias().keys())
                    # Filter out system indices
                    indices = [i for i in indices if not i.startswith('.')]
                except Exception:
                    indices = []
            
            # Scan each index
            for index_name in indices:
                try:
                    # Search for documents with email fields
                    emails = []
                    total_docs = 0
                    docs_with_emails = 0
                    
                    # Search in common email fields
                    for field in self.EMAIL_FIELDS:
                        try:
                            query = {
                                "query": {
                                    "exists": {
                                        "field": field
                                    }
                                }
                            }
                            
                            response = es.search(
                                index=index_name,
                                body=query,
                                size=1000
                            )
                            
                            hits = response.get('hits', {}).get('hits', [])
                            total_docs += len(hits)
                            
                            for hit in hits:
                                source = hit.get('_source', {})
                                email_value = source.get(field)
                                
                                if email_value:
                                    if isinstance(email_value, str):
                                        extracted = self._extract_emails_from_string(email_value)
                                        if extracted:
                                            emails.extend(extracted)
                                            docs_with_emails += 1
                                    elif isinstance(email_value, list):
                                        for item in email_value:
                                            if isinstance(item, str):
                                                extracted = self._extract_emails_from_string(item)
                                                if extracted:
                                                    emails.extend(extracted)
                                                    docs_with_emails += 1
                        except Exception:
                            continue
                    
                    # Also search all fields for email patterns
                    try:
                        query = {
                            "query": {
                                "match_all": {}
                            }
                        }
                        
                        response = es.search(
                            index=index_name,
                            body=query,
                            size=1000
                        )
                        
                        hits = response.get('hits', {}).get('hits', [])
                        
                        for hit in hits:
                            source = hit.get('_source', {})
                            for key, value in source.items():
                                if isinstance(value, str):
                                    extracted = self._extract_emails_from_string(value)
                                    if extracted:
                                        emails.extend(extracted)
                                        docs_with_emails += 1
                    except Exception:
                        pass
                    
                    # Remove duplicates
                    emails = list(set(emails))
                    
                    if emails:
                        results.append(ElasticsearchExtractionResult(
                            ip=ip,
                            port=port,
                            index=index_name,
                            emails=emails,
                            total_documents=total_docs,
                            documents_with_emails=docs_with_emails,
                            extraction_time=time.time() - start_time
                        ))
                        
                except Exception:
                    continue
            
        except Exception as e:
            print(f"Error with elasticsearch-py: {e}")
        
        return results
    
    def _extract_with_socket(
        self,
        ip: str,
        port: int,
        index: Optional[str],
        start_time: float
    ) -> List[ElasticsearchExtractionResult]:
        """
        Extract emails using raw socket connection.
        
        Args:
            ip: IP address
            port: Port number
            index: Specific index
            start_time: Start time
            
        Returns:
            List of ElasticsearchExtractionResult objects
        """
        import time
        
        results = []
        
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(self.timeout)
            sock.connect((ip, port))
            
            # Get list of indices
            if index:
                indices = [index]
            else:
                request = b'GET /_cat/indices?format=json HTTP/1.1\r\n'
                request += f'Host: {ip}:{port}\r\n'.encode()
                request += b'Connection: close\r\n'
                request += b'\r\n'
                
                sock.send(request)
                response = sock.recv(65536).decode('utf-8', errors='ignore')
                
                indices = self._parse_elasticsearch_indices(response)
            
            # Scan each index
            for index_name in indices:
                try:
                    # Search for all documents in index
                    request = f'GET /{index_name}/_search?size=1000 HTTP/1.1\r\n'
                    request += f'Host: {ip}:{port}\r\n'
                    request += 'Connection: close\r\n'
                    request += '\r\n'
                    
                    sock.send(request.encode())
                    response = sock.recv(65536).decode('utf-8', errors='ignore')
                    
                    # Parse response
                    documents = self._parse_elasticsearch_documents(response)
                    
                    # Extract emails from documents
                    emails = []
                    docs_with_emails = 0
                    
                    for doc in documents:
                        doc_emails = self._extract_emails_from_document(doc)
                        if doc_emails:
                            emails.extend(doc_emails)
                            docs_with_emails += 1
                    
                    # Remove duplicates
                    emails = list(set(emails))
                    
                    if emails:
                        results.append(ElasticsearchExtractionResult(
                            ip=ip,
                            port=port,
                            index=index_name,
                            emails=emails,
                            total_documents=len(documents),
                            documents_with_emails=docs_with_emails,
                            extraction_time=time.time() - start_time
                        ))
                        
                except Exception:
                    continue
            
            sock.close()
            
        except Exception as e:
            print(f"Error with socket extraction: {e}")
        
        return results
    
    def _parse_elasticsearch_indices(self, response: str) -> List[str]:
        """
        Parse Elasticsearch indices response.
        
        Args:
            response: HTTP response string
            
        Returns:
            List of index names
        """
        indices = []
        
        try:
            # Extract JSON from response
            json_match = re.search(r'\[.*\]', response, re.DOTALL)
            if json_match:
                indices_data = json.loads(json_match.group())
                
                for index_info in indices_data:
                    index_name = index_info.get('index', '')
                    if index_name and not index_name.startswith('.'):
                        indices.append(index_name)
                        
        except Exception:
            pass
        
        return indices
    
    def _parse_elasticsearch_documents(self, response: str) -> List[Dict[str, Any]]:
        """
        Parse Elasticsearch search response.
        
        Args:
            response: HTTP response string
            
        Returns:
            List of documents
        """
        documents = []
        
        try:
            # Extract JSON from response
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                response_data = json.loads(json_match.group())
                
                hits = response_data.get('hits', {}).get('hits', [])
                for hit in hits:
                    source = hit.get('_source', {})
                    documents.append(source)
                    
        except Exception:
            pass
        
        return documents
    
    def _extract_emails_from_string(self, text: str) -> List[str]:
        """
        Extract email addresses from string.
        
        Args:
            text: Text to search
            
        Returns:
            List of email addresses
        """
        return self.EMAIL_PATTERN.findall(text)
    
    def _extract_emails_from_document(self, document: Dict[str, Any]) -> List[str]:
        """
        Extract emails from Elasticsearch document.
        
        Args:
            document: Elasticsearch document
            
        Returns:
            List of email addresses
        """
        emails = []
        
        # Check common email fields
        for field in self.EMAIL_FIELDS:
            if field in document:
                value = document[field]
                if isinstance(value, str):
                    emails.extend(self._extract_emails_from_string(value))
                elif isinstance(value, list):
                    for item in value:
                        if isinstance(item, str):
                            emails.extend(self._extract_emails_from_string(item))
        
        # Check all string fields
        for key, value in document.items():
            if isinstance(value, str):
                emails.extend(self._extract_emails_from_string(value))
        
        return list(set(emails))
