"""
Free Tier Geo-Targeting Module
Uses free GeoIP services without API keys or paid tiers
"""
import requests
import json
import sqlite3
import os
from typing import Dict, List, Optional, Tuple
from datetime import datetime


class FreeGeoTargeting:
    """Free geo-targeting using open APIs"""
    
    def __init__(self, db_path: str = None):
        if db_path is None:
            db_path = os.getenv('DATABASE_PATH', './database/devnav.db')
        self.db_path = db_path
    
    # ========================
    # IP-API.COM (Free)
    # ========================
    
    def geoip_ipapi(self, ip_address: str) -> Dict:
        """
        Free GeoIP lookup from ip-api.com
        FREE: 45 requests/minute, no API key needed
        
        Args:
            ip_address: IP to geolocate
        
        Returns {country, country_code, city, latitude, longitude, timezone, isp}
        """
        base_url = f"http://ip-api.com/json/{ip_address}"
        params = {'fields': 'status,country,countryCode,city,lat,lon,timezone,isp,query'}
        
        try:
            response = requests.get(base_url, params=params, timeout=5)
            if response.status_code == 200:
                data = response.json()
                
                if data.get('status') == 'success':
                    return {
                        'ip': data.get('query'),
                        'country': data.get('country'),
                        'country_code': data.get('countryCode'),
                        'city': data.get('city'),
                        'latitude': data.get('lat'),
                        'longitude': data.get('lon'),
                        'timezone': data.get('timezone'),
                        'isp': data.get('isp'),
                        'source': 'ip-api.com',
                        'status': 'success'
                    }
                else:
                    return {'status': 'failed', 'reason': data.get('message')}
        except requests.RequestException as e:
            return {'status': 'error', 'reason': str(e)}
        
        return {'status': 'failed', 'reason': 'Unknown error'}
    
    # ========================
    # IPIFY (Free)
    # ========================
    
    def geoip_ipify(self, ip_address: str) -> Dict:
        """
        Alternative free GeoIP from ipify
        FREE: No rate limits for basic endpoint
        
        Args:
            ip_address: IP to geolocate
        
        Returns {country_code, country_name, city, timezone}
        """
        base_url = "https://geo.ipify.org/api/v2/country,city"
        params = {
            'apiKey': 'at_NjNELfxKqrxGJmSX9A9TKp80qYmHA',  # Free tier key (basic)
            'ipAddress': ip_address
        }
        
        try:
            response = requests.get(base_url, params=params, timeout=5)
            if response.status_code == 200:
                data = response.json()
                return {
                    'ip': data.get('ip'),
                    'country_code': data['location'].get('country'),
                    'city': data['location'].get('city'),
                    'latitude': data['location'].get('lat'),
                    'longitude': data['location'].get('lng'),
                    'timezone': data['location'].get('timezone'),
                    'isp': data.get('isp'),
                    'source': 'ipify',
                    'status': 'success'
                }
        except requests.RequestException as e:
            return {'status': 'error', 'reason': str(e)}
        
        return {'status': 'failed', 'reason': 'Unknown error'}
    
    # ========================
    # GEOIP-DB (Free)
    # ========================
    
    def geoip_geoipdb(self, ip_address: str) -> Dict:
        """
        Completely free GeoIP from geoip-db.com
        FREE: No rate limits, no API key
        
        Args:
            ip_address: IP to geolocate
        
        Returns {country_code, country_name, city, latitude, longitude, state}
        """
        base_url = f"https://geoip-db.com/json/{ip_address}"
        
        try:
            response = requests.get(base_url, timeout=5)
            if response.status_code == 200:
                data = response.json()
                if data.get('valid'):
                    return {
                        'ip': ip_address,
                        'country_code': data.get('country_code'),
                        'country_name': data.get('country_name'),
                        'city': data.get('city'),
                        'state': data.get('state'),
                        'latitude': data.get('latitude'),
                        'longitude': data.get('longitude'),
                        'source': 'geoip-db.com',
                        'status': 'success'
                    }
        except requests.RequestException as e:
            return {'status': 'error', 'reason': str(e)}
        
        return {'status': 'failed', 'reason': 'Unknown error'}
    
    # ========================
    # MAXMIND GEOLITE2 (Free Database)
    # ========================
    
    def load_geolite2_csv(self, csv_path: str = './geolite2-country.csv') -> bool:
        """
        Load free MaxMind GeoLite2 country database from CSV
        Download from: https://dev.maxmind.com/geoip/geolite2-country/
        
        Args:
            csv_path: Path to GeoLite2 CSV file
        
        Returns True if loaded successfully
        """
        if not os.path.exists(csv_path):
            print(f"⚠️  GeoLite2 file not found: {csv_path}")
            print("Download from: https://dev.maxmind.com/geoip/geolite2-country/")
            return False
        
        try:
            # Parse and store in database
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Create table if not exists
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS geolite2_blocks (
                    network TEXT PRIMARY KEY,
                    country_code TEXT,
                    country_name TEXT
                )
            """)
            
            # Import data
            with open(csv_path, 'r') as f:
                count = 0
                for line in f:
                    if line.startswith('#') or not line.strip():
                        continue
                    
                    parts = line.strip().split(',')
                    if len(parts) >= 3:
                        network, country_code, country_name = parts[0], parts[1], parts[2]
                        cursor.execute("""
                            INSERT OR IGNORE INTO geolite2_blocks (network, country_code, country_name)
                            VALUES (?, ?, ?)
                        """, (network, country_code, country_name))
                        count += 1
                
                conn.commit()
                print(f"✓ Loaded {count} IP ranges from GeoLite2")
        except Exception as e:
            print(f"✗ Error loading GeoLite2: {e}")
            return False
        finally:
            conn.close()
        
        return True
    
    # ========================
    # Geo-Targeting Logic
    # ========================
    
    def get_free_geoip(self, ip_address: str) -> Dict:
        """
        Get geoip data using free services in priority order
        
        Args:
            ip_address: IP to geolocate
        
        Returns combined geolocation data
        """
        # Try primary: ip-api.com (fastest free)
        result = self.geoip_ipapi(ip_address)
        
        if result.get('status') == 'success':
            return result
        
        # Fallback: ipify
        result = self.geoip_ipify(ip_address)
        if result.get('status') == 'success':
            return result
        
        # Final fallback: geoip-db
        result = self.geoip_geoipdb(ip_address)
        if result.get('status') == 'success':
            return result
        
        return {'status': 'failed', 'reason': 'All services failed'}
    
    def target_by_country(self, country_codes: List[str]) -> Tuple[int, List[Dict]]:
        """
        Find all contacts in specific countries
        
        Args:
            country_codes: List of country codes (e.g., ['US', 'UK', 'CA'])
        
        Returns (count, contacts_list)
        """
        placeholders = ','.join(['?' for _ in country_codes])
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute(f"""
            SELECT id, email, name, company, country
            FROM contacts
            WHERE country IN ({placeholders})
            ORDER BY country
        """, country_codes)
        
        results = cursor.fetchall()
        conn.close()
        
        contacts = [{
            'id': r[0],
            'email': r[1],
            'name': r[2],
            'company': r[3],
            'country': r[4]
        } for r in results]
        
        return len(contacts), contacts
    
    def target_by_timezone(self, timezones: List[str]) -> Tuple[int, List[Dict]]:
        """
        Find contacts by timezone for best send times
        
        Args:
            timezones: List of timezone names (e.g., ['America/New_York', 'Europe/London'])
        
        Returns (count, contacts_list)
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        results = []
        for tz in timezones:
            cursor.execute("""
                SELECT id, email, name, city, timezone
                FROM ip_tracking
                WHERE timezone = ?
            """, (tz,))
            results.extend(cursor.fetchall())
        
        conn.close()
        
        contacts = [{
            'id': r[0],
            'email': r[1],
            'name': r[2],
            'city': r[3],
            'timezone': r[4]
        } for r in results]
        
        return len(contacts), contacts
    
    def cache_geoip(self, ip_address: str, geo_data: Dict) -> bool:
        """
        Cache IP geolocation data for reuse
        
        Args:
            ip_address: IP address
            geo_data: Geolocation data
        
        Returns True if cached
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                INSERT OR REPLACE INTO ip_tracking 
                (ip_address, country, city, latitude, longitude, timezone, isp, data_source)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                ip_address,
                geo_data.get('country_code'),
                geo_data.get('city'),
                geo_data.get('latitude'),
                geo_data.get('longitude'),
                geo_data.get('timezone'),
                geo_data.get('isp'),
                geo_data.get('source', 'free-tier')
            ))
            conn.commit()
            return True
        except Exception as e:
            print(f"✗ Error caching geoip: {e}")
            return False
        finally:
            conn.close()
    
    def get_cached_geoip(self, ip_address: str) -> Optional[Dict]:
        """
        Get cached geoip data if available
        
        Args:
            ip_address: IP address
        
        Returns cached geolocation data or None
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT country, city, latitude, longitude, timezone, isp
            FROM ip_tracking
            WHERE ip_address = ?
        """, (ip_address,))
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return {
                'ip': ip_address,
                'country': result[0],
                'city': result[1],
                'latitude': result[2],
                'longitude': result[3],
                'timezone': result[4],
                'isp': result[5],
                'cached': True
            }
        
        return None
    
    def get_statistics(self) -> Dict:
        """Get geo-targeting statistics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Countries distribution
        cursor.execute("""
            SELECT country, COUNT(*) as count
            FROM contacts
            WHERE country IS NOT NULL
            GROUP BY country
            ORDER BY count DESC
            LIMIT 10
        """)
        top_countries = [{'country': r[0], 'count': r[1]} for r in cursor.fetchall()]
        
        # Timezones distribution
        cursor.execute("""
            SELECT timezone, COUNT(*) as count
            FROM ip_tracking
            WHERE timezone IS NOT NULL
            GROUP BY timezone
            ORDER BY count DESC
            LIMIT 10
        """)
        top_timezones = [{'timezone': r[0], 'count': r[1]} for r in cursor.fetchall()]
        
        conn.close()
        
        return {
            'top_countries': top_countries,
            'top_timezones': top_timezones,
            'total_cached_ips': self._get_cached_ip_count()
        }
    
    def _get_cached_ip_count(self) -> int:
        """Get count of cached IPs"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM ip_tracking")
        count = cursor.fetchone()[0]
        conn.close()
        return count


def get_free_geo_targeting(db_path: str = None) -> FreeGeoTargeting:
    """Factory function"""
    return FreeGeoTargeting(db_path)


if __name__ == "__main__":
    print("Free Tier Geo-Targeting Module")
    print("✓ IP-API.COM (45 req/min, no API key)")
    print("✓ IPify (unlimited, free tier)")
    print("✓ GeoIP-DB (unlimited, no API key)")
    print("✓ MaxMind GeoLite2 (free download)")
    print("\nNo paid APIs required!")
