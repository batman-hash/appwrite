"""
MongoDB Email Extractor Module

Extracts email addresses from MongoDB databases.
"""

import re
import socket
from typing import List, Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class MongoDBExtractionResult:
    """MongoDB extraction result"""
    ip: str
    port: int
    database: str
    collection: str
    emails: List[str]
    total_documents: int
    documents_with_emails: int
    extraction_time: float


class MongoDBExtractor:
    """
    Extracts email addresses from MongoDB databases.
    
    Features:
    - Connect to MongoDB instances
    - Enumerate databases and collections
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
        Initialize MongoDB extractor.
        
        Args:
            timeout: Socket timeout in seconds
        """
        self.timeout = timeout
    
    def extract_emails(
        self,
        ip: str,
        port: int = 27017,
        database: Optional[str] = None,
        collection: Optional[str] = None,
        username: Optional[str] = None,
        password: Optional[str] = None
    ) -> List[MongoDBExtractionResult]:
        """
        Extract emails from MongoDB instance.
        
        Args:
            ip: IP address
            port: Port number
            database: Specific database to scan (None for all)
            collection: Specific collection to scan (None for all)
            username: Authentication username
            password: Authentication password
            
        Returns:
            List of MongoDBExtractionResult objects
        """
        import time
        start_time = time.time()
        
        results = []
        
        try:
            # Try to connect using pymongo if available
            try:
                import pymongo
                results = self._extract_with_pymongo(
                    ip, port, database, collection,
                    username, password, start_time
                )
            except ImportError:
                # Fall back to raw socket extraction
                results = self._extract_with_socket(
                    ip, port, database, collection, start_time
                )
            
        except Exception as e:
            print(f"Error extracting from MongoDB at {ip}:{port}: {e}")
        
        return results
    
    def _extract_with_pymongo(
        self,
        ip: str,
        port: int,
        database: Optional[str],
        collection: Optional[str],
        username: Optional[str],
        password: Optional[str],
        start_time: float
    ) -> List[MongoDBExtractionResult]:
        """
        Extract emails using pymongo.
        
        Args:
            ip: IP address
            port: Port number
            database: Specific database
            collection: Specific collection
            username: Username
            password: Password
            start_time: Start time
            
        Returns:
            List of MongoDBExtractionResult objects
        """
        import time
        import pymongo
        
        results = []
        
        try:
            # Connect to MongoDB
            if username and password:
                uri = f"mongodb://{username}:{password}@{ip}:{port}/"
                client = pymongo.MongoClient(uri, serverSelectionTimeoutMS=self.timeout * 1000)
            else:
                client = pymongo.MongoClient(ip, port, serverSelectionTimeoutMS=self.timeout * 1000)
            
            # Get list of databases
            if database:
                databases = [database]
            else:
                try:
                    databases = client.list_database_names()
                except Exception:
                    databases = []
            
            # Scan each database
            for db_name in databases:
                if db_name in ['admin', 'local', 'config']:
                    continue
                
                db = client[db_name]
                
                # Get list of collections
                if collection:
                    collections = [collection]
                else:
                    try:
                        collections = db.list_collection_names()
                    except Exception:
                        collections = []
                
                # Scan each collection
                for coll_name in collections:
                    try:
                        coll = db[coll_name]
                        
                        # Search for documents with email fields
                        emails = []
                        total_docs = 0
                        docs_with_emails = 0
                        
                        # Search in common email fields
                        for field in self.EMAIL_FIELDS:
                            try:
                                cursor = coll.find({field: {'$exists': True}})
                                for doc in cursor:
                                    total_docs += 1
                                    email_value = doc.get(field)
                                    
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
                        
                        # Also search all string fields for email patterns
                        try:
                            cursor = coll.find({})
                            for doc in cursor:
                                for key, value in doc.items():
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
                            results.append(MongoDBExtractionResult(
                                ip=ip,
                                port=port,
                                database=db_name,
                                collection=coll_name,
                                emails=emails,
                                total_documents=total_docs,
                                documents_with_emails=docs_with_emails,
                                extraction_time=time.time() - start_time
                            ))
                            
                    except Exception:
                        continue
            
            client.close()
            
        except Exception as e:
            print(f"Error with pymongo: {e}")
        
        return results
    
    def _extract_with_socket(
        self,
        ip: str,
        port: int,
        database: Optional[str],
        collection: Optional[str],
        start_time: float
    ) -> List[MongoDBExtractionResult]:
        """
        Extract emails using raw socket connection.
        
        Args:
            ip: IP address
            port: Port number
            database: Specific database
            collection: Specific collection
            start_time: Start time
            
        Returns:
            List of MongoDBExtractionResult objects
        """
        import time
        
        results = []
        
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(self.timeout)
            sock.connect((ip, port))
            
            # Send listDatabases command
            cmd = self._build_mongodb_command('listDatabases')
            sock.send(cmd)
            
            response = sock.recv(4096)
            
            # Parse response to get databases
            databases = self._parse_mongodb_databases(response)
            
            # Scan each database
            for db_name in databases:
                if db_name in ['admin', 'local', 'config']:
                    continue
                
                # Send listCollections command
                cmd = self._build_mongodb_command('listCollections', db_name)
                sock.send(cmd)
                
                response = sock.recv(4096)
                
                # Parse response to get collections
                collections = self._parse_mongodb_collections(response)
                
                # Scan each collection
                for coll_name in collections:
                    # Send find command
                    cmd = self._build_mongodb_command('find', db_name, coll_name)
                    sock.send(cmd)
                    
                    response = sock.recv(65536)
                    
                    # Parse response to get documents
                    documents = self._parse_mongodb_documents(response)
                    
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
                        results.append(MongoDBExtractionResult(
                            ip=ip,
                            port=port,
                            database=db_name,
                            collection=coll_name,
                            emails=emails,
                            total_documents=len(documents),
                            documents_with_emails=docs_with_emails,
                            extraction_time=time.time() - start_time
                        ))
            
            sock.close()
            
        except Exception as e:
            print(f"Error with socket extraction: {e}")
        
        return results
    
    def _build_mongodb_command(
        self,
        command: str,
        database: str = 'admin',
        collection: str = None
    ) -> bytes:
        """
        Build MongoDB command packet.
        
        Args:
            command: Command name
            database: Database name
            collection: Collection name
            
        Returns:
            MongoDB command bytes
        """
        # Simplified MongoDB command builder
        # In production, use proper MongoDB wire protocol
        
        if command == 'listDatabases':
            # { listDatabases: 1 }
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
            cmd += b'\x6c\x69\x73\x74\x44\x61\x74\x61\x62\x61\x73\x65\x73\x00'  # listDatabases
            cmd += b'\x01\x00\x00\x00'  # Value: 1
            cmd += b'\x00'  # End
            return cmd
        
        elif command == 'listCollections':
            # { listCollections: 1 }
            cmd = b'\x3f\x00\x00\x00'
            cmd += b'\x00\x00\x00\x00'
            cmd += b'\x00\x00\x00\x00'
            cmd += b'\xd4\x07\x00\x00'
            cmd += b'\x00\x00\x00\x00'
            cmd += f'{database}.$cmd\x00'.encode()
            cmd += b'\x00\x00\x00\x00'
            cmd += b'\x01\x00\x00\x00'
            cmd += b'\x08\x00\x00\x00'
            cmd += b'\x10'
            cmd += b'\x6c\x69\x73\x74\x43\x6f\x6c\x6c\x65\x63\x74\x69\x6f\x6e\x73\x00'
            cmd += b'\x01\x00\x00\x00'
            cmd += b'\x00'
            return cmd
        
        elif command == 'find':
            # { find: "<collection>" }
            cmd = b'\x3f\x00\x00\x00'
            cmd += b'\x00\x00\x00\x00'
            cmd += b'\x00\x00\x00\x00'
            cmd += b'\xd4\x07\x00\x00'
            cmd += b'\x00\x00\x00\x00'
            cmd += f'{database}.$cmd\x00'.encode()
            cmd += b'\x00\x00\x00\x00'
            cmd += b'\x01\x00\x00\x00'
            cmd += b'\x08\x00\x00\x00'
            cmd += b'\x02'  # String
            cmd += b'\x66\x69\x6e\x64\x00'  # find
            cmd += f'{len(collection) + 1}\x00\x00\x00'.encode()
            cmd += f'{collection}\x00'.encode()
            cmd += b'\x00'
            return cmd
        
        return b''
    
    def _parse_mongodb_databases(self, response: bytes) -> List[str]:
        """
        Parse MongoDB listDatabases response.
        
        Args:
            response: Raw response bytes
            
        Returns:
            List of database names
        """
        databases = []
        
        try:
            response_str = response.decode('utf-8', errors='ignore')
            
            # Extract database names
            db_matches = re.findall(r'"name"\s*:\s*"([^"]+)"', response_str)
            databases = [db for db in db_matches if db not in ['admin', 'local', 'config']]
            
        except Exception:
            pass
        
        return databases
    
    def _parse_mongodb_collections(self, response: bytes) -> List[str]:
        """
        Parse MongoDB listCollections response.
        
        Args:
            response: Raw response bytes
            
        Returns:
            List of collection names
        """
        collections = []
        
        try:
            response_str = response.decode('utf-8', errors='ignore')
            
            # Extract collection names
            coll_matches = re.findall(r'"name"\s*:\s*"([^"]+)"', response_str)
            collections = [coll for coll in coll_matches if not coll.startswith('system.')]
            
        except Exception:
            pass
        
        return collections
    
    def _parse_mongodb_documents(self, response: bytes) -> List[Dict[str, Any]]:
        """
        Parse MongoDB find response.
        
        Args:
            response: Raw response bytes
            
        Returns:
            List of documents
        """
        documents = []
        
        try:
            response_str = response.decode('utf-8', errors='ignore')
            
            # Try to extract JSON-like documents
            # This is simplified - in production use proper BSON parser
            doc_pattern = r'\{[^}]+\}'
            matches = re.findall(doc_pattern, response_str)
            
            for match in matches:
                try:
                    # Try to parse as JSON
                    import json
                    doc = json.loads(match)
                    documents.append(doc)
                except:
                    # If not valid JSON, create simple dict
                    doc = {'raw': match}
                    documents.append(doc)
                    
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
        Extract emails from MongoDB document.
        
        Args:
            document: MongoDB document
            
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
