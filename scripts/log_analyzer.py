#!/usr/bin/env python

"""
Log File Analyzer
Analyzes web server logs for common patterns:
- Number of 404 errors
- Most requested pages
- IP addresses with most requests
- HTTP status code distribution
- Busiest hours
"""

import re
import sys
import argparse
from collections import Counter, defaultdict
from datetime import datetime
import os
from pathlib import Path

class LogAnalyzer:
    def __init__(self, log_file):
        self.log_file = log_file
        self.log_entries = []
        self.stats = {
            'total_requests': 0,
            'status_codes': Counter(),
            'top_pages': Counter(),
            'top_ips': Counter(),
            'hourly_activity': Counter(),
            'user_agents': Counter(),
            'referrers': Counter()
        }
        
        # Common log format regex (Nginx/Apache)
        self.log_pattern = re.compile(
            r'(?P<ip>\S+) - - \[(?P<timestamp>[^\]]+)\] '
            r'"(?P<method>\w+) (?P<url>\S+) (?P<protocol>[\w/\.]+)" '
            r'(?P<status>\d+) (?P<size>\d+) "(?P<referrer>[^"]*)" '
            r'"(?P<user_agent>[^"]*)"'
        )

    def parse_log_file(self):
        """Parse the log file and extract relevant information"""
        if not os.path.exists(self.log_file):
            print(f"❌ Error: Log file '{self.log_file}' not found!")
            return False
            
        print(f"📖 Reading log file: {self.log_file}")
        
        try:
            with open(self.log_file, 'r', encoding='utf-8', errors='ignore') as file:
                for line_num, line in enumerate(file, 1):
                    line = line.strip()
                    if not line:
                        continue
                        
                    match = self.log_pattern.match(line)
                    if match:
                        self._process_log_entry(match.groupdict(), line_num)
                    else:
                        # Try to parse with simpler pattern for different formats
                        self._parse_fallback(line, line_num)
                        
            return True
            
        except Exception as e:
            print(f"❌ Error reading log file: {e}")
            return False

    def _process_log_entry(self, entry, line_num):
        """Process a single log entry"""
        self.stats['total_requests'] += 1
        
        # Status codes
        status = entry['status']
        self.stats['status_codes'][status] += 1
        
        # Top pages (URLs)
        url = entry['url']
        self.stats['top_pages'][url] += 1
        
        # Top IPs
        ip = entry['ip']
        self.stats['top_ips'][ip] += 1
        
        # Hourly activity
        try:
            timestamp_str = entry['timestamp'].split()[0]  # Get date part
            dt = datetime.strptime(timestamp_str, '%d/%b/%Y:%H:%M:%S')
            hour = dt.strftime('%H:00')
            self.stats['hourly_activity'][hour] += 1
        except:
            pass
        
        # User agents (simplified)
        if entry['user_agent'] and entry['user_agent'] != '-':
            # Extract browser name from user agent
            ua = entry['user_agent'].lower()
            if 'chrome' in ua:
                browser = 'Chrome'
            elif 'firefox' in ua:
                browser = 'Firefox'
            elif 'safari' in ua and 'chrome' not in ua:
                browser = 'Safari'
            elif 'edge' in ua:
                browser = 'Edge'
            elif 'bot' in ua or 'crawler' in ua:
                browser = 'Bot/Crawler'
            else:
                browser = 'Other'
            self.stats['user_agents'][browser] += 1
        
        # Referrers
        if entry['referrer'] and entry['referrer'] != '-':
            self.stats['referrers'][entry['referrer']] += 1

    def _parse_fallback(self, line, line_num):
        """Fallback parsing for different log formats"""
        parts = line.split()
        if len(parts) >= 7:
            # Simple IP detection (first part that looks like IP)
            for part in parts:
                if re.match(r'\d+\.\d+\.\d+\.\d+', part):
                    self.stats['top_ips'][part] += 1
                    break
            
            # Look for status codes (3-digit numbers)
            for part in parts:
                if re.match(r'^\d{3}$', part):
                    self.stats['status_codes'][part] += 1
                    break
            
            # Look for URLs (containing /)
            for part in parts:
                if '/' in part and 'HTTP' not in part:
                    self.stats['top_pages'][part] += 1
                    break
            
            self.stats['total_requests'] += 1

    def generate_report(self):
        """Generate comprehensive analysis report"""
        if self.stats['total_requests'] == 0:
            print("❌ No valid log entries found!")
            return
            
        print("\n" + "="*60)
        print("📊 LOG ANALYSIS REPORT")
        print("="*60)
        
        # Basic Statistics
        print(f"\n📈 BASIC STATISTICS:")
        print(f"   Total Requests: {self.stats['total_requests']:,}")
        
        # Status Code Distribution
        print(f"\n🔴 STATUS CODE DISTRIBUTION:")
        for code, count in self.stats['status_codes'].most_common():
            percentage = (count / self.stats['total_requests']) * 100
            status_name = self._get_status_name(code)
            print(f"   {code} {status_name}: {count:,} ({percentage:.1f}%)")
        
        # 404 Errors specifically
        not_found_count = self.stats['status_codes'].get('404', 0)
        if not_found_count > 0:
            print(f"\n❌ 404 NOT FOUND ERRORS: {not_found_count}")
            print("   Top missing pages:")
            for url, count in self.stats['top_pages'].most_common(10):
                if any(ext in url for ext in ['.php', '.html', '.js', '.css', '.jpg', '.png']):
                    print(f"     {url}: {count}")
        
        # Top Pages
        print(f"\n🌐 TOP REQUESTED PAGES:")
        for url, count in self.stats['top_pages'].most_common(10):
            percentage = (count / self.stats['total_requests']) * 100
            print(f"   {url}: {count:,} ({percentage:.1f}%)")
        
        # Top IP Addresses
        print(f"\n🖥️  TOP IP ADDRESSES:")
        for ip, count in self.stats['top_ips'].most_common(10):
            percentage = (count / self.stats['total_requests']) * 100
            print(f"   {ip}: {count:,} ({percentage:.1f}%)")
        
        # Hourly Activity
        print(f"\n🕒 HOURLY ACTIVITY:")
        for hour, count in self.stats['hourly_activity'].most_common(24):
            percentage = (count / self.stats['total_requests']) * 100
            print(f"   {hour}: {count:,} requests ({percentage:.1f}%)")
        
        # User Agents
        print(f"\n🌍 BROWSER DISTRIBUTION:")
        for browser, count in self.stats['user_agents'].most_common():
            percentage = (count / self.stats['total_requests']) * 100
            print(f"   {browser}: {count:,} ({percentage:.1f}%)")
        
        # Security Alerts
        self._check_security_issues()

    def _get_status_name(self, code):
        """Get human-readable name for HTTP status codes"""
        status_names = {
            '200': 'OK', '301': 'Moved Permanently', '302': 'Found',
            '304': 'Not Modified', '400': 'Bad Request', '401': 'Unauthorized',
            '403': 'Forbidden', '404': 'Not Found', '500': 'Internal Server Error',
            '502': 'Bad Gateway', '503': 'Service Unavailable'
        }
        return status_names.get(code, 'Unknown')

    def _check_security_issues(self):
        """Check for potential security issues"""
        print(f"\n🚨 SECURITY CHECKS:")
        
        # Check for suspicious user agents
        suspicious_agents = ['sqlmap', 'nikto', 'metasploit', 'nmap', 'havij']
        for agent in suspicious_agents:
            for ua in self.stats['user_agents']:
                if agent in ua.lower():
                    print(f"   ⚠️  Suspicious user agent detected: {ua}")
        
        # Check for common attack patterns in URLs
        attack_patterns = [
            ('SQL Injection', ['union select', 'or 1=1', 'drop table', 'insert into']),
            ('XSS', ['<script>', 'javascript:', 'onload=', 'onerror=']),
            ('Path Traversal', ['../', '..\\', '/etc/passwd']),
            ('Command Injection', [';ls', '|cat', '`id`', '$(whoami)'])
        ]
        
        for pattern_name, patterns in attack_patterns:
            for url in self.stats['top_pages']:
                url_lower = url.lower()
                for pattern in patterns:
                    if pattern in url_lower:
                        print(f"   ⚠️  Possible {pattern_name} attempt: {url}")

    def save_report(self, output_file):
        """Save report to file"""
        try:
            original_stdout = sys.stdout
            with open(output_file, 'w', encoding='utf-8') as f:
                sys.stdout = f
                self.generate_report()
                sys.stdout = original_stdout
            print(f"\n💾 Report saved to: {output_file}")
        except Exception as e:
            print(f"❌ Error saving report: {e}")

def create_sample_log():
    """Create a sample log file for testing"""
    sample_log = """192.168.1.100 - - [25/Dec/2023:10:15:32 +0000] "GET /index.html HTTP/1.1" 200 1524 "https://example.com" "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
192.168.1.101 - - [25/Dec/2023:10:15:33 +0000] "GET /about.html HTTP/1.1" 200 2341 "https://example.com" "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
192.168.1.102 - - [25/Dec/2023:10:15:34 +0000] "GET /contact.php HTTP/1.1" 200 1876 "-" "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"
192.168.1.103 - - [25/Dec/2023:10:15:35 +0000] "GET /old-page.html HTTP/1.1" 404 342 "-" "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/91.0.4472.124"
192.168.1.104 - - [25/Dec/2023:10:15:36 +0000] "GET /admin/login HTTP/1.1" 403 512 "-" "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Firefox/89.0"
192.168.1.105 - - [25/Dec/2023:10:15:37 +0000] "GET /api/users HTTP/1.1" 200 876 "https://app.example.com" "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) Safari/537.36"
192.168.1.100 - - [25/Dec/2023:10:15:38 +0000] "GET /products/item123 HTTP/1.1" 200 1543 "https://example.com" "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Edge/91.0.864.59"
192.168.1.106 - - [25/Dec/2023:10:15:39 +0000] "GET /wp-admin HTTP/1.1" 404 321 "-" "sqlmap/1.4.2"
192.168.1.107 - - [25/Dec/2023:10:15:40 +0000] "GET /search?q=<script>alert('xss')</script> HTTP/1.1" 200 765 "-" "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
192.168.1.108 - - [25/Dec/2023:10:15:41 +0000] "GET /../../../etc/passwd HTTP/1.1" 403 498 "-" "Mozilla/5.0 (X11; Linux x86_64)"
192.168.1.109 - - [25/Dec/2023:10:15:42 +0000] "POST /login HTTP/1.1" 200 432 "https://example.com" "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/91.0.4472.124"
192.168.1.110 - - [25/Dec/2023:10:15:43 +0000] "GET /images/logo.png HTTP/1.1" 200 2345 "https://example.com" "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
"""
    
    sample_file = "sample_access.log"
    with open(sample_file, 'w') as f:
        f.write(sample_log)
    return sample_file

def main():
    parser = argparse.ArgumentParser(description='Web Server Log Analyzer')
    parser.add_argument('log_file', nargs='?', help='Path to the log file to analyze')
    parser.add_argument('--output', '-o', help='Save report to file')
    parser.add_argument('--sample', action='store_true', help='Generate and analyze sample log')
    
    args = parser.parse_args()
    
    if args.sample:
        print("🛠️  Generating sample log file...")
        log_file = create_sample_log()
        print(f"📁 Sample log created: {log_file}")
    elif not args.log_file:
        print("❌ Please provide a log file or use --sample")
        parser.print_help()
        return
    
    if args.sample or args.log_file:
        log_file = args.log_file if not args.sample else create_sample_log()
        
        analyzer = LogAnalyzer(log_file)
        
        if analyzer.parse_log_file():
            if args.output:
                analyzer.save_report(args.output)
            else:
                analyzer.generate_report()
        
        if args.sample:
            # Clean up sample file
            try:
                os.remove(log_file)
                print(f"🧹 Sample file cleaned up: {log_file}")
            except:
                pass

if __name__ == "__main__":
    main()

    






