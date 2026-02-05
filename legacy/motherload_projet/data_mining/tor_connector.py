import requests
import socket
import socks
import time
from typing import Optional

# Default Tor SOCKS proxy on macOS (standard install)
# Or usage with 'tor' command line
TOR_PROXY_HOST = '127.0.0.1'
TOR_PROXY_PORT = 9050 # Standard Tor port

def get_tor_session() -> requests.Session:
    """Create a valid requests session routed through Tor."""
    session = requests.Session()
    session.proxies = {
        'http': f'socks5h://{TOR_PROXY_HOST}:{TOR_PROXY_PORT}',
        'https': f'socks5h://{TOR_PROXY_HOST}:{TOR_PROXY_PORT}'
    }
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; rv:102.0) Gecko/20100101 Firefox/102.0'
    })
    return session

def check_tor_connection() -> dict:
    """Check if Tor is running and accessible."""
    try:
        # Check IP via Tor
        session = get_tor_session()
        # This URL returns your public IP. If Tor is working, it's not your ISP IP.
        resp = session.get('https://check.torproject.org/api/ip', timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            return {
                "status": "connected",
                "is_tor": data.get("IsTor", False),
                "ip": data.get("IP", "unknown")
            }
        return {"status": "error", "message": f"HTTP {resp.status_code}"}
    except Exception as e:
        return {"status": "failed", "message": str(e), "tip": "Is Tor Browser or 'brew services start tor' running?"}

def fetch_zclient_onion(onion_url: str) -> dict:
    """Attempt to reach the Z-Library onion address."""
    try:
        session = get_tor_session()
        start = time.time()
        resp = session.get(onion_url, timeout=30)
        elapsed = time.time() - start
        
        status = "online" if resp.status_code == 200 else "offline"
        title = "unknown"
        
        if status == "online":
            # Simple title extract
            from html.parser import HTMLParser
            class TitleParser(HTMLParser):
                def __init__(self):
                    super().__init__()
                    self.title = ""
                    self.in_title = False
                def handle_starttag(self, tag, attrs):
                    if tag == "title": self.in_title = True
                def handle_endtag(self, tag):
                    if tag == "title": self.in_title = False
                def handle_data(self, data):
                    if self.in_title: self.title = data
            
            parser = TitleParser()
            parser.feed(resp.text)
            title = parser.title
            
        return {
            "status": status,
            "http_code": resp.status_code,
            "latency_ms": int(elapsed * 1000),
            "page_title": title
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}
