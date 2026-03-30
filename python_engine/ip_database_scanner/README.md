# IP Database Scanner Module

A comprehensive IP database scanner for discovering exposed databases and extracting email addresses. Provides security assessment capabilities for MongoDB, Elasticsearch, and Redis databases.

## Features

- **IP Range Scanning**: Scan IP ranges for exposed database ports
- **Database Detection**: Identify MongoDB, Elasticsearch, Redis instances
- **Email Extraction**: Extract emails from discovered databases
- **Security Assessment**: Assess security vulnerabilities in databases
- **Multi-threaded Scanning**: Fast concurrent scanning
- **CLI Interface**: Command-line tool for scanning operations

## Installation

### Basic Installation

```bash
pip install -r requirements.txt
```

### Full Installation (All Features)

```bash
# Core dependencies
pip install scapy netifaces

# Database drivers (optional)
pip install pymongo elasticsearch redis

# For network scanning
pip install python-nmap
```

## Quick Start

### Python API

```python
from python_engine.ip_database_scanner import (
    IPScanner,
    DatabaseDetector,
    MongoDBExtractor,
    ElasticsearchExtractor,
    RedisExtractor,
    SecurityAssessor
)

# Initialize scanner
scanner = IPScanner()

# Scan IP range for databases
results = scanner.scan_ip_range('192.168.1.0/24')

# Get database services
db_services = scanner.get_database_services()

# Extract emails from MongoDB
mongodb_extractor = MongoDBExtractor()
emails = mongodb_extractor.extract_emails(
    ip='192.168.1.100',
    port=27017
)

# Assess security
assessor = SecurityAssessor()
assessment = assessor.assess_mongodb(
    ip='192.168.1.100',
    port=27017
)
print(f"Security Score: {assessment.security_score}/100")
```

### Command-Line Interface

```bash
# Scan IP range for databases
python -m python_engine.ip_database_scanner.scanner_cli scan --range 192.168.1.0/24

# Scan specific IP
python -m python_engine.ip_database_scanner.scanner_cli scan --ip 192.168.1.100

# Extract emails from MongoDB
python -m python_engine.ip_database_scanner.scanner_cli extract --type mongodb --ip 192.168.1.100

# Extract emails from Elasticsearch
python -m python_engine.ip_database_scanner.scanner_cli extract --type elasticsearch --ip 192.168.1.100

# Extract emails from Redis
python -m python_engine.ip_database_scanner.scanner_cli extract --type redis --ip 192.168.1.100

# Assess security
python -m python_engine.ip_database_scanner.scanner_cli assess --type mongodb --ip 192.168.1.100

# Full scan (discover, extract, assess)
python -m python_engine.ip_database_scanner.scanner_cli full-scan --range 192.168.1.0/24
```

## Scanning Methods

### 1. IP Range Scanning

Scan IP ranges for exposed database ports:

```python
from python_engine.ip_database_scanner import IPScanner

scanner = IPScanner(timeout=1.0, max_workers=100)

# Scan IP range
results = scanner.scan_ip_range(
    ip_range='192.168.1.0/24',
    ports=[27017, 9200, 6379],  # MongoDB, Elasticsearch, Redis
    grab_banner=True
)

# Print results
for result in results:
    if result.is_open:
        print(f"IP: {result.ip}, Port: {result.port}, Service: {result.service}")
```

### 2. Database Detection

Detect and identify database services:

```python
from python_engine.ip_database_scanner import DatabaseDetector

detector = DatabaseDetector(timeout=2.0)

# Detect MongoDB
mongodb_info = detector.detect_mongodb('192.168.1.100', 27017)
if mongodb_info:
    print(f"MongoDB {mongodb_info.version}")
    print(f"Security Level: {mongodb_info.security_level}")

# Detect Elasticsearch
es_info = detector.detect_elasticsearch('192.168.1.100', 9200)
if es_info:
    print(f"Elasticsearch {es_info.version}")

# Detect Redis
redis_info = detector.detect_redis('192.168.1.100', 6379)
if redis_info:
    print(f"Redis {redis_info.version}")
```

### 3. Email Extraction

Extract emails from discovered databases:

#### MongoDB

```python
from python_engine.ip_database_scanner import MongoDBExtractor

extractor = MongoDBExtractor(timeout=5.0)

# Extract emails from all databases
results = extractor.extract_emails(
    ip='192.168.1.100',
    port=27017
)

# Extract from specific database
results = extractor.extract_emails(
    ip='192.168.1.100',
    port=27017,
    database='users',
    collection='profiles'
)

# With authentication
results = extractor.extract_emails(
    ip='192.168.1.100',
    port=27017,
    username='admin',
    password='password'
)

# Print results
for result in results:
    print(f"Database: {result.database}")
    print(f"Collection: {result.collection}")
    print(f"Emails found: {len(result.emails)}")
```

#### Elasticsearch

```python
from python_engine.ip_database_scanner import ElasticsearchExtractor

extractor = ElasticsearchExtractor(timeout=5.0)

# Extract emails from all indices
results = extractor.extract_emails(
    ip='192.168.1.100',
    port=9200
)

# Extract from specific index
results = extractor.extract_emails(
    ip='192.168.1.100',
    port=9200,
    index='users'
)

# Print results
for result in results:
    print(f"Index: {result.index}")
    print(f"Emails found: {len(result.emails)}")
```

#### Redis

```python
from python_engine.ip_database_scanner import RedisExtractor

extractor = RedisExtractor(timeout=5.0)

# Extract emails from Redis
results = extractor.extract_emails(
    ip='192.168.1.100',
    port=6379
)

# With authentication
results = extractor.extract_emails(
    ip='192.168.1.100',
    port=6379,
    password='redis_password'
)

# Print results
for result in results:
    print(f"Keys scanned: {result.keys_scanned}")
    print(f"Emails found: {len(result.emails)}")
    print(f"Keys with emails: {result.keys_with_emails}")
```

### 4. Security Assessment

Assess security vulnerabilities in databases:

#### MongoDB Security

```python
from python_engine.ip_database_scanner import SecurityAssessor

assessor = SecurityAssessor(timeout=5.0)

# Assess MongoDB security
assessment = assessor.assess_mongodb('192.168.1.100', 27017)

print(f"Security Score: {assessment.security_score}/100")
print(f"Risk Level: {assessment.risk_level}")

for vuln in assessment.vulnerabilities:
    print(f"[{vuln.level.value.upper()}] {vuln.name}")
    print(f"  Description: {vuln.description}")
    print(f"  Recommendation: {vuln.recommendation}")
```

#### Elasticsearch Security

```python
# Assess Elasticsearch security
assessment = assessor.assess_elasticsearch('192.168.1.100', 9200)

print(f"Security Score: {assessment.security_score}/100")
print(f"Risk Level: {assessment.risk_level}")
```

#### Redis Security

```python
# Assess Redis security
assessment = assessor.assess_redis('192.168.1.100', 6379)

print(f"Security Score: {assessment.security_score}/100")
print(f"Risk Level: {assessment.risk_level}")
```

## Common Database Ports

| Port | Service | Description |
|------|---------|-------------|
| 27017 | MongoDB | Default MongoDB port |
| 27018 | MongoDB (Shard) | MongoDB shard port |
| 27019 | MongoDB (Config) | MongoDB config server |
| 9200 | Elasticsearch | Elasticsearch HTTP |
| 9300 | Elasticsearch (Transport) | Elasticsearch transport |
| 6379 | Redis | Default Redis port |
| 6380 | Redis (Sentinel) | Redis sentinel |
| 3306 | MySQL | MySQL database |
| 5432 | PostgreSQL | PostgreSQL database |
| 1433 | Microsoft SQL Server | MS SQL Server |
| 5000 | CouchDB | CouchDB HTTP |
| 5984 | CouchDB (HTTP) | CouchDB HTTP |
| 8086 | InfluxDB | InfluxDB HTTP |
| 8529 | ArangoDB | ArangoDB HTTP |
| 7474 | Neo4j | Neo4j HTTP |
| 9042 | Cassandra | Cassandra native |
| 11211 | Memcached | Memcached |
| 28015 | RethinkDB | RethinkDB HTTP |

## Security Assessment

### Vulnerability Levels

- **CRITICAL**: Immediate security risk (e.g., no authentication)
- **HIGH**: Significant security risk (e.g., exposed databases)
- **MEDIUM**: Moderate security risk (e.g., weak configuration)
- **LOW**: Minor security risk (e.g., information disclosure)
- **INFO**: Informational finding

### Common Vulnerabilities

#### MongoDB
- No authentication required
- Exposed databases
- Unrestricted network binding
- Weak configuration

#### Elasticsearch
- No authentication required
- Exposed indices
- Sensitive endpoints accessible
- Weak security settings

#### Redis
- No authentication required
- Exposed dangerous commands
- Sensitive data exposure
- Weak configuration

## Exporting Results

### Export to JSON

```python
# Export scan results
scanner.export_results('scan_results.json')

# Export extraction results
import json

export_data = []
for result in results:
    export_data.append({
        'ip': result.ip,
        'port': result.port,
        'database': result.database,
        'emails': result.emails,
        'total_documents': result.total_documents,
    })

with open('extraction_results.json', 'w') as f:
    json.dump(export_data, f, indent=2)
```

### Export via CLI

```bash
# Export scan results
python -m python_engine.ip_database_scanner.scanner_cli scan \
    --range 192.168.1.0/24 \
    --output scan_results.json

# Export extraction results
python -m python_engine.ip_database_scanner.scanner_cli extract \
    --type mongodb \
    --ip 192.168.1.100 \
    --output extraction_results.json

# Export security assessment
python -m python_engine.ip_database_scanner.scanner_cli assess \
    --type mongodb \
    --ip 192.168.1.100 \
    --output assessment_results.json
```

## Performance Considerations

### Scanning Speed

- **Single IP**: ~1-2 seconds per port
- **IP Range (/24)**: ~10-30 seconds (254 IPs)
- **IP Range (/16)**: ~30-60 minutes (65,534 IPs)

### Optimization Tips

1. **Adjust timeout**: Lower timeout for faster scanning
2. **Increase workers**: More workers for parallel scanning
3. **Limit ports**: Scan only necessary ports
4. **Use filters**: Filter results to reduce processing

```python
# Fast scanning configuration
scanner = IPScanner(
    timeout=0.5,  # Lower timeout
    max_workers=200  # More workers
)

# Scan only database ports
results = scanner.scan_ip_range(
    ip_range='192.168.1.0/24',
    ports=[27017, 9200, 6379]  # Only database ports
)
```

## Troubleshooting

### Permission Denied

```bash
# Some operations require root privileges
sudo python -m python_engine.ip_database_scanner.scanner_cli scan --range 192.168.1.0/24
```

### Connection Timeout

```python
# Increase timeout for slow networks
scanner = IPScanner(timeout=5.0)
detector = DatabaseDetector(timeout=10.0)
```

### Module Not Found

```bash
# Install missing dependencies
pip install pymongo elasticsearch redis
```

### No Results Found

```python
# Check if ports are correct
scanner = IPScanner()
results = scanner.scan_single_ip(
    ip='192.168.1.100',
    ports=[27017, 9200, 6379],
    grab_banner=True  # Enable banner grabbing
)
```

## Examples

### Example 1: Scan Local Network

```python
from python_engine.ip_database_scanner import IPScanner

scanner = IPScanner()

# Scan local network
results = scanner.scan_ip_range('192.168.1.0/24')

# Print database services
db_services = scanner.get_database_services()
for service in db_services:
    print(f"{service.service} at {service.ip}:{service.port}")
```

### Example 2: Extract All Emails

```python
from python_engine.ip_database_scanner import (
    IPScanner,
    MongoDBExtractor,
    ElasticsearchExtractor,
    RedisExtractor
)

# Scan for databases
scanner = IPScanner()
results = scanner.scan_ip_range('192.168.1.0/24')
db_services = scanner.get_database_services()

# Extract emails from each database
all_emails = []

for service in db_services:
    if service.service == 'MongoDB':
        extractor = MongoDBExtractor()
        results = extractor.extract_emails(service.ip, service.port)
        for result in results:
            all_emails.extend(result.emails)
    
    elif service.service == 'Elasticsearch':
        extractor = ElasticsearchExtractor()
        results = extractor.extract_emails(service.ip, service.port)
        for result in results:
            all_emails.extend(result.emails)
    
    elif service.service == 'Redis':
        extractor = RedisExtractor()
        results = extractor.extract_emails(service.ip, service.port)
        for result in results:
            all_emails.extend(result.emails)

# Remove duplicates
all_emails = list(set(all_emails))
print(f"Total unique emails: {len(all_emails)}")
```

### Example 3: Security Audit

```python
from python_engine.ip_database_scanner import (
    IPScanner,
    SecurityAssessor
)

# Scan for databases
scanner = IPScanner()
results = scanner.scan_ip_range('192.168.1.0/24')
db_services = scanner.get_database_services()

# Assess security of each database
assessor = SecurityAssessor()

for service in db_services:
    if service.service == 'MongoDB':
        assessment = assessor.assess_mongodb(service.ip, service.port)
    elif service.service == 'Elasticsearch':
        assessment = assessor.assess_elasticsearch(service.ip, service.port)
    elif service.service == 'Redis':
        assessment = assessor.assess_redis(service.ip, service.port)
    else:
        continue
    
    print(f"\n{service.service} at {service.ip}:{service.port}")
    print(f"Security Score: {assessment.security_score}/100")
    print(f"Risk Level: {assessment.risk_level}")
    
    for vuln in assessment.vulnerabilities:
        print(f"  [{vuln.level.value.upper()}] {vuln.name}")
```

## License

Part of DevNavigator project. See main project LICENSE for details.

## Support

For issues and questions, please refer to the main DevNavigator documentation.
