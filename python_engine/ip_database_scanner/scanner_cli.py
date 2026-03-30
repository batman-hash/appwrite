"""
Scanner CLI Interface

Command-line interface for IP database scanning and email extraction.
"""

import argparse
import sys
import json
from typing import Optional, List
from datetime import datetime

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


class ScannerCLI:
    """
    Command-line interface for IP database scanning.
    
    Features:
    - Scan IP ranges for exposed databases
    - Extract emails from discovered databases
    - Assess security vulnerabilities
    - Export results to JSON
    """
    
    def __init__(self):
        """Initialize scanner CLI"""
        self.scanner = IPScanner()
        self.detector = DatabaseDetector()
        self.mongodb_extractor = MongoDBExtractor()
        self.elasticsearch_extractor = ElasticsearchExtractor()
        self.redis_extractor = RedisExtractor()
        self.security_assessor = SecurityAssessor()
        self.metasploit = MetasploitIntegration()
        self.nmap = NmapIntegration()
        self.tshark = TSharkIntegration()
        self.exploiter = VulnerabilityExploiter()
    
    def create_parser(self) -> argparse.ArgumentParser:
        """
        Create command-line argument parser.
        
        Returns:
            Configured argument parser
        """
        parser = argparse.ArgumentParser(
            prog='ip-scanner',
            description='IP Database Scanner - Discover and extract emails from exposed databases',
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Examples:
  # Scan IP range for databases
  ip-scanner scan --range 192.168.1.0/24
  
  # Scan specific IP
  ip-scanner scan --ip 192.168.1.100
  
  # Extract emails from MongoDB
  ip-scanner extract --type mongodb --ip 192.168.1.100
  
  # Extract emails from Elasticsearch
  ip-scanner extract --type elasticsearch --ip 192.168.1.100
  
  # Extract emails from Redis
  ip-scanner extract --type redis --ip 192.168.1.100
  
  # Assess security
  ip-scanner assess --type mongodb --ip 192.168.1.100
  
  # Full scan and extract
  ip-scanner full-scan --range 192.168.1.0/24
  
  # Exploit vulnerable database
  ip-scanner exploit --type mongodb --ip 192.168.1.100
  
  # Scan with Nmap
  ip-scanner nmap-scan --ip 192.168.1.100
  
  # Capture packets with TShark
  ip-scanner tshark-capture --interface eth0 --count 100
            """
        )
        
        subparsers = parser.add_subparsers(dest='command', help='Command to execute')
        
        # Scan command
        scan_parser = subparsers.add_parser(
            'scan',
            help='Scan IP range for exposed databases'
        )
        scan_parser.add_argument(
            '--range', '-r',
            help='IP range in CIDR notation (e.g., 192.168.1.0/24)'
        )
        scan_parser.add_argument(
            '--ip', '-i',
            help='Single IP address to scan'
        )
        scan_parser.add_argument(
            '--ports', '-p',
            help='Comma-separated list of ports to scan'
        )
        scan_parser.add_argument(
            '--timeout', '-t',
            type=float,
            default=1.0,
            help='Scan timeout in seconds (default: 1.0)'
        )
        scan_parser.add_argument(
            '--workers', '-w',
            type=int,
            default=100,
            help='Maximum concurrent workers (default: 100)'
        )
        scan_parser.add_argument(
            '--output', '-o',
            help='Output JSON filename'
        )
        scan_parser.add_argument(
            '--verbose', '-v',
            action='store_true',
            help='Verbose output'
        )
        
        # Extract command
        extract_parser = subparsers.add_parser(
            'extract',
            help='Extract emails from discovered databases'
        )
        extract_parser.add_argument(
            '--type', '-T',
            choices=['mongodb', 'elasticsearch', 'redis'],
            required=True,
            help='Database type'
        )
        extract_parser.add_argument(
            '--ip', '-i',
            required=True,
            help='Database IP address'
        )
        extract_parser.add_argument(
            '--port', '-p',
            type=int,
            help='Database port (default: auto-detect)'
        )
        extract_parser.add_argument(
            '--username', '-u',
            help='Authentication username'
        )
        extract_parser.add_argument(
            '--password', '-P',
            help='Authentication password'
        )
        extract_parser.add_argument(
            '--database', '-d',
            help='Specific database to scan'
        )
        extract_parser.add_argument(
            '--collection', '-c',
            help='Specific collection/index to scan'
        )
        extract_parser.add_argument(
            '--output', '-o',
            help='Output JSON filename'
        )
        extract_parser.add_argument(
            '--verbose', '-v',
            action='store_true',
            help='Verbose output'
        )
        
        # Assess command
        assess_parser = subparsers.add_parser(
            'assess',
            help='Assess security of discovered databases'
        )
        assess_parser.add_argument(
            '--type', '-T',
            choices=['mongodb', 'elasticsearch', 'redis'],
            required=True,
            help='Database type'
        )
        assess_parser.add_argument(
            '--ip', '-i',
            required=True,
            help='Database IP address'
        )
        assess_parser.add_argument(
            '--port', '-p',
            type=int,
            help='Database port (default: auto-detect)'
        )
        assess_parser.add_argument(
            '--output', '-o',
            help='Output JSON filename'
        )
        assess_parser.add_argument(
            '--verbose', '-v',
            action='store_true',
            help='Verbose output'
        )
        
        # Full scan command
        full_scan_parser = subparsers.add_parser(
            'full-scan',
            help='Full scan: discover databases, extract emails, assess security'
        )
        full_scan_parser.add_argument(
            '--range', '-r',
            help='IP range in CIDR notation (e.g., 192.168.1.0/24)'
        )
        full_scan_parser.add_argument(
            '--ip', '-i',
            help='Single IP address to scan'
        )
        full_scan_parser.add_argument(
            '--ports', '-p',
            help='Comma-separated list of ports to scan'
        )
        full_scan_parser.add_argument(
            '--timeout', '-t',
            type=float,
            default=1.0,
            help='Scan timeout in seconds (default: 1.0)'
        )
        full_scan_parser.add_argument(
            '--output', '-o',
            help='Output JSON filename'
        )
        full_scan_parser.add_argument(
            '--verbose', '-v',
            action='store_true',
            help='Verbose output'
        )
        
        # Exploit command
        exploit_parser = subparsers.add_parser(
            'exploit',
            help='Exploit vulnerable databases to extract emails'
        )
        exploit_parser.add_argument(
            '--type', '-T',
            choices=['mongodb', 'elasticsearch', 'redis', 'mysql', 'postgresql'],
            required=True,
            help='Database type'
        )
        exploit_parser.add_argument(
            '--ip', '-i',
            required=True,
            help='Database IP address'
        )
        exploit_parser.add_argument(
            '--port', '-p',
            type=int,
            help='Database port (default: auto-detect)'
        )
        exploit_parser.add_argument(
            '--output', '-o',
            help='Output JSON filename'
        )
        exploit_parser.add_argument(
            '--verbose', '-v',
            action='store_true',
            help='Verbose output'
        )
        
        # Nmap scan command
        nmap_parser = subparsers.add_parser(
            'nmap-scan',
            help='Scan with Nmap for advanced service detection'
        )
        nmap_parser.add_argument(
            '--ip', '-i',
            required=True,
            help='Target IP address'
        )
        nmap_parser.add_argument(
            '--ports', '-p',
            help='Port range (e.g., 1-1000)'
        )
        nmap_parser.add_argument(
            '--scan-type', '-s',
            choices=['sS', 'sT', 'sU', 'sV', 'O', 'A'],
            default='sS',
            help='Scan type (default: sS)'
        )
        nmap_parser.add_argument(
            '--output', '-o',
            help='Output JSON filename'
        )
        nmap_parser.add_argument(
            '--verbose', '-v',
            action='store_true',
            help='Verbose output'
        )
        
        # TShark capture command
        tshark_parser = subparsers.add_parser(
            'tshark-capture',
            help='Capture packets with TShark'
        )
        tshark_parser.add_argument(
            '--interface', '-I',
            default='any',
            help='Network interface (default: any)'
        )
        tshark_parser.add_argument(
            '--count', '-c',
            type=int,
            default=100,
            help='Number of packets to capture (default: 100)'
        )
        tshark_parser.add_argument(
            '--filter', '-f',
            help='Display filter'
        )
        tshark_parser.add_argument(
            '--timeout', '-t',
            type=int,
            default=30,
            help='Capture timeout in seconds (default: 30)'
        )
        tshark_parser.add_argument(
            '--output', '-o',
            help='Output JSON filename'
        )
        tshark_parser.add_argument(
            '--verbose', '-v',
            action='store_true',
            help='Verbose output'
        )
        
        return parser
    
    def cmd_scan(self, args):
        """
        Execute scan command.
        
        Args:
            Parsed command-line arguments
        """
        try:
            print(f"Starting IP scan...")
            
            # Parse ports
            ports = None
            if args.ports:
                ports = [int(p.strip()) for p in args.ports.split(',')]
            
            # Scan IP range or single IP
            if args.range:
                print(f"Scanning IP range: {args.range}")
                results = self.scanner.scan_ip_range(
                    ip_range=args.range,
                    ports=ports,
                    grab_banner=args.verbose
                )
            elif args.ip:
                print(f"Scanning IP: {args.ip}")
                results = self.scanner.scan_single_ip(
                    ip=args.ip,
                    ports=ports,
                    grab_banner=args.verbose
                )
            else:
                print("Error: Either --range or --ip must be specified")
                sys.exit(1)
            
            # Print results
            print(f"\n{'='*60}")
            print("Scan Results")
            print(f"{'='*60}")
            
            for result in results:
                if result.is_open:
                    print(f"\nIP: {result.ip}")
                    print(f"Port: {result.port}")
                    print(f"Service: {result.service}")
                    if result.response_time:
                        print(f"Response Time: {result.response_time:.3f}s")
                    if result.banner and args.verbose:
                        print(f"Banner: {result.banner[:100]}...")
            
            # Print statistics
            stats = self.scanner.get_stats()
            print(f"\n{'='*60}")
            print("Statistics")
            print(f"{'='*60}")
            print(f"Total scanned: {stats['total_scanned']}")
            print(f"Open ports: {stats['open_ports']}")
            print(f"Closed ports: {stats['closed_ports']}")
            
            if stats['services']:
                print(f"\nServices found:")
                for service, count in stats['services'].items():
                    print(f"  {service}: {count}")
            
            # Export results
            if args.output:
                self.scanner.export_results(args.output)
                print(f"\nResults exported to: {args.output}")
            
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)
    
    def cmd_extract(self, args):
        """
        Execute extract command.
        
        Args:
            Parsed command-line arguments
        """
        try:
            print(f"Extracting emails from {args.type.upper()} at {args.ip}...")
            
            # Set default port if not specified
            port = args.port
            if port is None:
                if args.type == 'mongodb':
                    port = 27017
                elif args.type == 'elasticsearch':
                    port = 9200
                elif args.type == 'redis':
                    port = 6379
            
            # Extract emails based on database type
            results = []
            
            if args.type == 'mongodb':
                results = self.mongodb_extractor.extract_emails(
                    ip=args.ip,
                    port=port,
                    database=args.database,
                    collection=args.collection,
                    username=args.username,
                    password=args.password
                )
            elif args.type == 'elasticsearch':
                results = self.elasticsearch_extractor.extract_emails(
                    ip=args.ip,
                    port=port,
                    index=args.collection,
                    username=args.username,
                    password=args.password
                )
            elif args.type == 'redis':
                results = self.redis_extractor.extract_emails(
                    ip=args.ip,
                    port=port,
                    password=args.password
                )
            
            # Print results
            print(f"\n{'='*60}")
            print("Extraction Results")
            print(f"{'='*60}")
            
            all_emails = []
            
            for result in results:
                print(f"\nDatabase: {getattr(result, 'database', getattr(result, 'index', 'N/A'))}")
                if hasattr(result, 'collection'):
                    print(f"Collection: {result.collection}")
                print(f"Emails found: {len(result.emails)}")
                print(f"Documents scanned: {result.total_documents}")
                print(f"Documents with emails: {result.documents_with_emails}")
                print(f"Extraction time: {result.extraction_time:.2f}s")
                
                if args.verbose and result.emails:
                    print(f"\nEmails:")
                    for email in result.emails[:10]:  # Show first 10
                        print(f"  {email}")
                    if len(result.emails) > 10:
                        print(f"  ... and {len(result.emails) - 10} more")
                
                all_emails.extend(result.emails)
            
            # Remove duplicates
            all_emails = list(set(all_emails))
            
            print(f"\n{'='*60}")
            print(f"Total unique emails found: {len(all_emails)}")
            
            # Export results
            if args.output:
                export_data = []
                for result in results:
                    export_data.append({
                        'ip': result.ip,
                        'port': result.port,
                        'database': getattr(result, 'database', getattr(result, 'index', 'N/A')),
                        'collection': getattr(result, 'collection', 'N/A'),
                        'emails': result.emails,
                        'total_documents': result.total_documents,
                        'documents_with_emails': result.documents_with_emails,
                        'extraction_time': result.extraction_time,
                    })
                
                with open(args.output, 'w') as f:
                    json.dump(export_data, f, indent=2)
                
                print(f"\nResults exported to: {args.output}")
            
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)
    
    def cmd_assess(self, args):
        """
        Execute assess command.
        
        Args:
            Parsed command-line arguments
        """
        try:
            print(f"Assessing security of {args.type.upper()} at {args.ip}...")
            
            # Set default port if not specified
            port = args.port
            if port is None:
                if args.type == 'mongodb':
                    port = 27017
                elif args.type == 'elasticsearch':
                    port = 9200
                elif args.type == 'redis':
                    port = 6379
            
            # Assess security based on database type
            assessment = None
            
            if args.type == 'mongodb':
                assessment = self.security_assessor.assess_mongodb(
                    ip=args.ip,
                    port=port
                )
            elif args.type == 'elasticsearch':
                assessment = self.security_assessor.assess_elasticsearch(
                    ip=args.ip,
                    port=port
                )
            elif args.type == 'redis':
                assessment = self.security_assessor.assess_redis(
                    ip=args.ip,
                    port=port
                )
            
            # Print results
            print(f"\n{'='*60}")
            print("Security Assessment")
            print(f"{'='*60}")
            print(f"IP: {assessment.ip}")
            print(f"Port: {assessment.port}")
            print(f"Database: {assessment.database_type}")
            print(f"Security Score: {assessment.security_score}/100")
            print(f"Risk Level: {assessment.risk_level}")
            print(f"Assessment Time: {assessment.assessment_time:.2f}s")
            
            if assessment.vulnerabilities:
                print(f"\nVulnerabilities found: {len(assessment.vulnerabilities)}")
                
                for vuln in assessment.vulnerabilities:
                    print(f"\n  [{vuln.level.value.upper()}] {vuln.name}")
                    print(f"    Description: {vuln.description}")
                    print(f"    Recommendation: {vuln.recommendation}")
                    if vuln.evidence and args.verbose:
                        print(f"    Evidence: {vuln.evidence}")
            else:
                print("\nNo vulnerabilities found.")
            
            # Export results
            if args.output:
                export_data = {
                    'ip': assessment.ip,
                    'port': assessment.port,
                    'database_type': assessment.database_type,
                    'security_score': assessment.security_score,
                    'risk_level': assessment.risk_level,
                    'assessment_time': assessment.assessment_time,
                    'vulnerabilities': [
                        {
                            'name': v.name,
                            'description': v.description,
                            'level': v.level.value,
                            'recommendation': v.recommendation,
                            'evidence': v.evidence,
                        }
                        for v in assessment.vulnerabilities
                    ],
                }
                
                with open(args.output, 'w') as f:
                    json.dump(export_data, f, indent=2)
                
                print(f"\nResults exported to: {args.output}")
            
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)
    
    def cmd_full_scan(self, args):
        """
        Execute full scan command.
        
        Args:
            Parsed command-line arguments
        """
        try:
            print("Starting full scan...")
            
            # Parse ports
            ports = None
            if args.ports:
                ports = [int(p.strip()) for p in args.ports.split(',')]
            
            # Scan for databases
            print("\n[1/3] Scanning for exposed databases...")
            
            if args.range:
                scan_results = self.scanner.scan_ip_range(
                    ip_range=args.range,
                    ports=ports,
                    grab_banner=False
                )
            elif args.ip:
                scan_results = self.scanner.scan_single_ip(
                    ip=args.ip,
                    ports=ports,
                    grab_banner=False
                )
            else:
                print("Error: Either --range or --ip must be specified")
                sys.exit(1)
            
            # Get database services
            db_services = self.scanner.get_database_services()
            
            print(f"Found {len(db_services)} database services")
            
            # Extract emails from each database
            print("\n[2/3] Extracting emails from databases...")
            
            all_emails = []
            extraction_results = []
            
            for service in db_services:
                print(f"\nExtracting from {service.service} at {service.ip}:{service.port}...")
                
                try:
                    if service.service == 'MongoDB':
                        results = self.mongodb_extractor.extract_emails(
                            ip=service.ip,
                            port=service.port
                        )
                    elif service.service == 'Elasticsearch':
                        results = self.elasticsearch_extractor.extract_emails(
                            ip=service.ip,
                            port=service.port
                        )
                    elif service.service == 'Redis':
                        results = self.redis_extractor.extract_emails(
                            ip=service.ip,
                            port=service.port
                        )
                    else:
                        continue
                    
                    extraction_results.extend(results)
                    
                    for result in results:
                        all_emails.extend(result.emails)
                        
                except Exception as e:
                    print(f"  Error: {e}")
                    continue
            
            # Remove duplicates
            all_emails = list(set(all_emails))
            
            # Assess security
            print("\n[3/3] Assessing security...")
            
            assessments = []
            
            for service in db_services:
                print(f"\nAssessing {service.service} at {service.ip}:{service.port}...")
                
                try:
                    if service.service == 'MongoDB':
                        assessment = self.security_assessor.assess_mongodb(
                            ip=service.ip,
                            port=service.port
                        )
                    elif service.service == 'Elasticsearch':
                        assessment = self.security_assessor.assess_elasticsearch(
                            ip=service.ip,
                            port=service.port
                        )
                    elif service.service == 'Redis':
                        assessment = self.security_assessor.assess_redis(
                            ip=service.ip,
                            port=service.port
                        )
                    else:
                        continue
                    
                    assessments.append(assessment)
                    
                except Exception as e:
                    print(f"  Error: {e}")
                    continue
            
            # Print summary
            print(f"\n{'='*60}")
            print("Full Scan Summary")
            print(f"{'='*60}")
            print(f"Databases found: {len(db_services)}")
            print(f"Total unique emails: {len(all_emails)}")
            print(f"Security assessments: {len(assessments)}")
            
            if assessments:
                avg_score = sum(a.security_score for a in assessments) / len(assessments)
                print(f"Average security score: {avg_score:.1f}/100")
            
            # Export results
            if args.output:
                export_data = {
                    'scan_time': datetime.now().isoformat(),
                    'databases_found': len(db_services),
                    'total_emails': len(all_emails),
                    'emails': all_emails,
                    'extraction_results': [
                        {
                            'ip': r.ip,
                            'port': r.port,
                            'database': getattr(r, 'database', getattr(r, 'index', 'N/A')),
                            'collection': getattr(r, 'collection', 'N/A'),
                            'emails': r.emails,
                            'total_documents': r.total_documents,
                            'documents_with_emails': r.documents_with_emails,
                            'extraction_time': r.extraction_time,
                        }
                        for r in extraction_results
                    ],
                    'security_assessments': [
                        {
                            'ip': a.ip,
                            'port': a.port,
                            'database_type': a.database_type,
                            'security_score': a.security_score,
                            'risk_level': a.risk_level,
                            'vulnerabilities': [
                                {
                                    'name': v.name,
                                    'description': v.description,
                                    'level': v.level.value,
                                    'recommendation': v.recommendation,
                                }
                                for v in a.vulnerabilities
                            ],
                        }
                        for a in assessments
                    ],
                }
                
                with open(args.output, 'w') as f:
                    json.dump(export_data, f, indent=2)
                
                print(f"\nResults exported to: {args.output}")
            
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)
    
    def main(self):
        """Main CLI entry point"""
        parser = self.create_parser()
        args = parser.parse_args()
        
        if not args.command:
            parser.print_help()
            sys.exit(0)
        
        # Execute command
        if args.command == 'scan':
            self.cmd_scan(args)
        elif args.command == 'extract':
            self.cmd_extract(args)
        elif args.command == 'assess':
            self.cmd_assess(args)
        elif args.command == 'full-scan':
            self.cmd_full_scan(args)
        else:
            parser.print_help()
            sys.exit(1)


def main():
    """CLI entry point"""
    cli = ScannerCLI()
    cli.main()


if __name__ == '__main__':
    main()
