#!/usr/bin/env python3
"""
Flask Web Application for Render Network Toolkit
Provides web interface and API for network functions
"""

import os
import sys
import json
import logging
from pathlib import Path
from flask import Flask, render_template, jsonify, request, send_from_directory
from flask_cors import CORS
from flask_debugtoolbar import DebugToolbarExtension

# Add parent directory to path to import render_network_toolkit
sys.path.insert(0, str(Path(__file__).parent.parent))

from render_network_toolkit import NetworkToolkit

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('render_network_toolkit.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_SSL_CERT_FILE = PROJECT_ROOT / 'certs' / 'server.crt'
DEFAULT_SSL_KEY_FILE = PROJECT_ROOT / 'certs' / 'server.key'


def _resolve_ssl_path(env_name: str, default_path: Path) -> Path | None:
    """Resolve an SSL path from the environment or the repo defaults."""
    raw_value = os.environ.get(env_name, "").strip()
    candidates = []

    if raw_value:
        raw_path = Path(raw_value).expanduser()
        candidates.append(raw_path)
        if not raw_path.is_absolute():
            candidates.append(Path.cwd() / raw_path)
            candidates.append(PROJECT_ROOT / raw_path)

    candidates.append(default_path)

    for candidate in candidates:
        try:
            if candidate.is_file():
                return candidate
        except OSError:
            continue

    return None


def _get_ssl_context() -> tuple[str, str] | None:
    """Build an ssl_context tuple when both certificate files are available."""
    cert_file = _resolve_ssl_path('SSL_CERT_FILE', DEFAULT_SSL_CERT_FILE)
    key_file = _resolve_ssl_path('SSL_KEY_FILE', DEFAULT_SSL_KEY_FILE)

    if cert_file and key_file:
        return str(cert_file), str(key_file)

    return None

# Initialize Flask app
app = Flask(__name__, 
            static_folder='../frontend',
            template_folder='../frontend')

# Load configuration from environment
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
app.config['DEBUG'] = os.environ.get('DEBUG', 'false').lower() == 'true'

# Enable CORS
CORS(app, origins=os.environ.get('CORS_ORIGINS', 'http://localhost:8011,http://127.0.0.1:8011').split(','))

# Enable debug toolbar if configured
if os.environ.get('ENABLE_DEBUG_TOOLBAR', 'false').lower() == 'true':
    toolbar = DebugToolbarExtension(app)

# Initialize network toolkit
toolkit = NetworkToolkit()

@app.route('/')
def index():
    """Serve the main index page"""
    return send_from_directory('../frontend', 'index.html')

@app.route('/<path:filename>')
def serve_static(filename):
    """Serve static files from frontend directory"""
    return send_from_directory('../frontend', filename)

@app.route('/api/health')
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'cyberghost-webapp',
        'version': '1.0.0'
    })

@app.route('/api/network/info')
def network_info():
    """Get network information"""
    try:
        info = toolkit.get_network_info()
        return jsonify({
            'success': True,
            'data': info
        })
    except Exception as e:
        logger.error(f"Error getting network info: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/network/scan', methods=['POST'])
def scan_network():
    """Scan network for devices"""
    try:
        data = request.get_json() or {}
        method = data.get('method', 'arp')
        devices = toolkit.scan_network(method=method)
        
        # Convert devices to serializable format
        devices_list = []
        for ip, device in devices.items():
            devices_list.append({
                'ip': device.ip,
                'mac': device.mac,
                'hostname': device.hostname,
                'vendor': device.vendor,
                'open_ports': device.open_ports,
                'last_seen': device.last_seen
            })
        
        return jsonify({
            'success': True,
            'data': {
                'devices': devices_list,
                'count': len(devices_list)
            }
        })
    except Exception as e:
        logger.error(f"Error scanning network: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/network/scan-ports', methods=['POST'])
def scan_ports():
    """Scan ports on a target IP"""
    try:
        data = request.get_json()
        if not data or 'target' not in data:
            return jsonify({
                'success': False,
                'error': 'Target IP is required'
            }), 400
        
        target = data['target']
        ports = data.get('ports', None)
        open_ports = toolkit.scan_ports(target, ports)
        
        return jsonify({
            'success': True,
            'data': {
                'target': target,
                'open_ports': open_ports
            }
        })
    except Exception as e:
        logger.error(f"Error scanning ports: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/network/monitor', methods=['POST'])
def monitor_connection():
    """Monitor network connection"""
    try:
        data = request.get_json()
        if not data or 'target' not in data:
            return jsonify({
                'success': False,
                'error': 'Target IP is required'
            }), 400
        
        target = data['target']
        target_size_mb = data.get('target_size_mb', 10.0)
        duration = data.get('duration', 60)
        
        stats = toolkit.monitor_connection(
            target_ip=target,
            target_size_mb=target_size_mb,
            duration=duration
        )
        
        return jsonify({
            'success': True,
            'data': stats
        })
    except Exception as e:
        logger.error(f"Error monitoring connection: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/network/dns/setup', methods=['POST'])
def setup_dns():
    """Setup DNS configuration"""
    try:
        data = request.get_json() or {}
        mode = data.get('mode', 'default')
        
        # Import DNS setup functionality
        from dns_setup import DNSSetup
        dns = DNSSetup()
        result = dns.setup(mode)
        
        return jsonify({
            'success': True,
            'data': result
        })
    except Exception as e:
        logger.error(f"Error setting up DNS: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/network/connection/test', methods=['POST'])
def test_connection():
    """Test network connection stability"""
    try:
        data = request.get_json() or {}
        target = data.get('target', '8.8.8.8')
        count = data.get('count', 10)
        
        from connection_stability import ConnectionTester
        tester = ConnectionTester()
        result = tester.test_stability(target, count)
        
        return jsonify({
            'success': True,
            'data': result
        })
    except Exception as e:
        logger.error(f"Error testing connection: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/firewall/setup', methods=['POST'])
def setup_firewall():
    """Setup firewall rules"""
    try:
        toolkit.run_firewall_setup()
        return jsonify({
            'success': True,
            'message': 'Firewall setup completed'
        })
    except Exception as e:
        logger.error(f"Error setting up firewall: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/devices/save', methods=['POST'])
def save_devices():
    """Save discovered devices"""
    try:
        data = request.get_json() or {}
        filename = data.get('filename', 'devices.json')
        toolkit.save_devices(filename)
        
        return jsonify({
            'success': True,
            'message': f'Devices saved to {filename}'
        })
    except Exception as e:
        logger.error(f"Error saving devices: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/devices/load', methods=['POST'])
def load_devices():
    """Load devices from file"""
    try:
        data = request.get_json()
        if not data or 'filename' not in data:
            return jsonify({
                'success': False,
                'error': 'Filename is required'
            }), 400
        
        filename = data['filename']
        toolkit.load_devices(filename)
        
        return jsonify({
            'success': True,
            'message': f'Devices loaded from {filename}'
        })
    except Exception as e:
        logger.error(f"Error loading devices: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

if __name__ == '__main__':
    host = os.environ.get('HOST', '0.0.0.0')
    port = int(os.environ.get('PORT', 8011))
    debug = os.environ.get('DEBUG', 'false').lower() == 'true'
    ssl_context = _get_ssl_context()
    
    logger.info(f"Starting CyberGhost Web App on {host}:{port}")
    if ssl_context:
        logger.info(
            "HTTPS enabled using cert file %s and key file %s",
            ssl_context[0],
            ssl_context[1],
        )
    else:
        logger.info("HTTPS disabled or certificates not found; starting over HTTP")

    app.run(host=host, port=port, debug=debug, ssl_context=ssl_context)
