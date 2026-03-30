"""
Metasploit Integration Module

Provides integration with Metasploit Framework for vulnerability scanning ONLY.
This module does NOT exploit vulnerabilities.

WARNING: This module is for authorized security assessment only.
Unauthorized access to computer systems is illegal under the CFAA and similar laws.
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
class VulnerabilityCheckResult:
    """Vulnerability check result"""
    target_ip: str
    target_port: int
    module_name: str
    vulnerable: bool
    output: str
    check_time: float = 0.0


class MetasploitIntegration:
    """
    Integration with Metasploit Framework for vulnerability scanning ONLY.

    Features:
    - Search for database vulnerabilities
    - Run vulnerability scans
    - Check if exploits are applicable

    WARNING: This module is for authorized security assessment only.
    Unauthorized access to computer systems is illegal under the CFAA and similar laws.
    """

    # Common database vulnerability modules (scanner modules only, no exploits)
    DATABASE_SCANNERS = {
        'mongodb': [
            'auxiliary/scanner/mongodb/mongodb_login',
            'auxiliary/scanner/mongodb/mongodb_enum',
        ],
        'elasticsearch': [
            'auxiliary/scanner/elasticsearch/elasticsearch_enum',
        ],
        'redis': [
            'auxiliary/scanner/redis/redis_login',
            'auxiliary/scanner/redis/redis_server',
        ],
        'mysql': [
            'auxiliary/scanner/mysql/mysql_login',
            'auxiliary/scanner/mysql/mysql_enum',
        ],
        'postgresql': [
            'auxiliary/scanner/postgres/postgres_login',
            'auxiliary/scanner/postgres/postgres_enum',
        ],
    }

    def __init__(self, msf_path: str = 'msfconsole'):
        """
        Initialize Metasploit integration.

        Args:
            msf_path: Path to msfconsole executable
        """
        self.msf_path = msf_path

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

    def search_vulnerabilities(
        self,
        database_type: str,
        version: Optional[str] = None
    ) -> List[MetasploitModule]:
        """
        Search for vulnerabilities for a specific database type.

        Args:
            database_type: Database type (mongodb, elasticsearch, redis, etc.)
            version: Specific version to search for

        Returns:
            List of MetasploitModule objects
        """
        modules = []

        # Get known scanners for database type
        db_type_lower = database_type.lower()
        if db_type_lower in self.DATABASE_SCANNERS:
            for module_path in self.DATABASE_SCANNERS[db_type_lower]:
                modules.append(MetasploitModule(
                    name=module_path.split('/')[-1],
                    path=module_path,
                    description=f'{database_type} scanner module',
                    rank='normal',
                    references=[]
                ))

        # Search Metasploit for additional vulnerabilities
        try:
            search_cmd = f'search type:auxiliary name:{database_type}'
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

                # Only include auxiliary modules (scanners), not exploits
                if module_type == 'auxiliary':
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

        # Get scanners for database type
        scanners = self.search_vulnerabilities(database_type)

        for scanner in scanners:
            try:
                # Check if scanner is applicable
                vuln = self._check_scanner_applicability(
                    target_ip, target_port, scanner
                )

                if vuln:
                    vulnerabilities.append(vuln)

            except Exception as e:
                print(f"Error checking scanner {scanner.name}: {e}")
                continue

        return vulnerabilities

    def _check_scanner_applicability(
        self,
        target_ip: str,
        target_port: int,
        scanner: MetasploitModule
    ) -> Optional[Dict[str, Any]]:
        """
        Check if scanner is applicable to target.

        Args:
            target_ip: Target IP address
            target_port: Target port
            scanner: Metasploit module

        Returns:
            Vulnerability dictionary or None
        """
        try:
            # Run scanner check
            check_cmd = f'use {scanner.path}\nset RHOSTS {target_ip}\nset RPORT {target_port}\ncheck'
            result = self._run_msf_command(check_cmd)

            # Parse check result
            if 'vulnerable' in result.lower() or 'success' in result.lower():
                return {
                    'name': scanner.name,
                    'path': scanner.path,
                    'description': scanner.description,
                    'rank': scanner.rank,
                    'target_ip': target_ip,
                    'target_port': target_port,
                    'vulnerable': True,
                }

        except Exception as e:
            pass

        return None

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
