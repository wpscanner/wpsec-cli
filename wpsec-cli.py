#!/usr/bin/env python3
# -*- coding: utf-8 -*-
##
# WPSec command-line client
##
# License: MIT
##

import argparse
import json
import logging
import sys
import time
import html
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional, Any
from urllib.parse import urlparse

import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

try:
    from colorama import init, Fore, Back, Style
    init(autoreset=True)  # Initialize colorama
    COLORAMA_AVAILABLE = True
except ImportError:
    # Fallback if colorama is not installed
    COLORAMA_AVAILABLE = False
    class Fore:
        RED = GREEN = YELLOW = BLUE = MAGENTA = CYAN = WHITE = RESET = ''
    class Back:
        RED = GREEN = YELLOW = BLUE = MAGENTA = CYAN = WHITE = RESET = ''
    class Style:
        BRIGHT = DIM = NORMAL = RESET_ALL = ''


# Configuration
@dataclass
class Config:
    """Application configuration"""
    CLI_VERSION: str = "0.5.0"
    NAME: str = "WPSec"
    CLI_NAME: str = "WPSec CLI"
    API_VERSION: str = "v1"
    API_BASE_URL: str = "https://api.wpsec.com"
    API_TIMEOUT: int = 30
    MAX_RETRIES: int = 3
    RETRY_BACKOFF: float = 0.3
    SUPPORT_URL: str = "support@wpsec.com"


class ErrorMessages(Enum):
    """Centralized error messages with emojis"""
    API_DOWN = f"❌ Error: {Config.NAME} API is down. Please create a new support ticket at: {Config.SUPPORT_URL}"
    AUTH_FAILED = "🔐 Error: Client authentication failed, invalid client ID or client secret."
    INVALID_JSON = "📄 Error: Response is not valid JSON"
    NO_ACCESS_TOKEN = "🔑 Error: No access_token in response"
    API_TIMEOUT = f"⏱️  Error: {Config.NAME} API timeout. Please try again later."
    INVALID_URL = "🌐 Error: Invalid URL format"
    REPORT_NOT_FOUND = "🔍 Error: Report not found"
    NO_REPORTS = "📊 Error: No reports found on page {}"
    SITE_EXISTS = "⚠️  Error: Site already exists on your account"
    HTTP_ERROR = "🚨 Error: HTTP {code} - {message}"
    UNEXPECTED_STATUS = "⚠️  Warning: Unexpected status code {code} for {url}"


# Emojis for different actions
class Emojis:
    SUCCESS = "✅"
    ERROR = "❌"
    WARNING = "⚠️"
    INFO = "ℹ️"
    SEARCH = "🔍"
    REPORT = "📊"
    SITE = "🌐"
    LOCK = "🔐"
    KEY = "🔑"
    CLOCK = "⏱️"
    ROCKET = "🚀"
    PING = "🏓"
    LIST = "📋"
    ADD = "➕"
    SPARKLE = "✨"


# ASCII art banner with color
BANNER = f"""{Fore.CYAN}__ __ ___ __ ___ ___ __
\\ V  V / '_ (_-</ -_) _|
 \\_/\\_/| .__/__/\\___\\__|
       |_|{Style.RESET_ALL}"""


class WPSecAPIError(Exception):
    """Custom exception for WPSec API errors"""
    pass


class WPSecClient:
    """WPSec API client with improved error handling and session management"""
    
    def __init__(self, config: Config):
        self.config = config
        self.session = self._create_session()
        self.token: Optional[str] = None
        self._setup_logging()
    
    def _setup_logging(self):
        """Configure logging"""
        logging.basicConfig(
            level=logging.WARNING,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
    
    def _create_session(self) -> requests.Session:
        """Create a requests session with retry logic"""
        session = requests.Session()
        retry_strategy = Retry(
            total=self.config.MAX_RETRIES,
            backoff_factor=self.config.RETRY_BACKOFF,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "POST", "PUT", "DELETE", "OPTIONS", "TRACE"]
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        session.headers.update({"User-Agent": f"{self.config.CLI_NAME}/{self.config.CLI_VERSION}"})
        return session
    
    def _check_response_status(self, response: requests.Response, expected_codes: List[int] = None) -> None:
        """Check HTTP response status code"""
        if expected_codes is None:
            expected_codes = [200, 201, 204]
        
        # Check content type for successful responses
        if response.status_code in expected_codes:
            content_type = response.headers.get('Content-Type', '').lower()
            # For API endpoints, we expect JSON responses
            if response.status_code == 200 and response.request.url.startswith(self.config.API_BASE_URL):
                if 'application/json' not in content_type and response.request.url != f"{self.config.API_BASE_URL}/{self.config.API_VERSION}/ping":
                    self.logger.warning(f"Unexpected content type '{content_type}' for API endpoint {response.request.url}")
            return
        
        # Handle specific error codes
        if response.status_code == 401:
            raise WPSecAPIError(ErrorMessages.AUTH_FAILED.value)
        elif response.status_code == 404:
            raise WPSecAPIError(ErrorMessages.REPORT_NOT_FOUND.value)
        elif response.status_code == 429:
            raise WPSecAPIError(f"{Emojis.WARNING} Rate limit exceeded. Please try again later.")
        elif response.status_code >= 500:
            raise WPSecAPIError(f"{Emojis.ERROR} Server error ({response.status_code}). Please try again later.")
        else:
            # Log unexpected status codes
            self.logger.warning(ErrorMessages.UNEXPECTED_STATUS.value.format(
                code=response.status_code, url=response.url
            ))
            # Try to get error message from response
            try:
                error_data = response.json()
                error_msg = error_data.get('message', response.text)
            except:
                error_msg = response.text or response.reason
            
            raise WPSecAPIError(ErrorMessages.HTTP_ERROR.value.format(
                code=response.status_code, message=error_msg
            ))
    
    def _make_request(self, method: str, url: str, expected_codes: List[int] = None, **kwargs) -> requests.Response:
        """Make HTTP request with error handling"""
        kwargs.setdefault('timeout', self.config.API_TIMEOUT)
        
        if self.token and 'headers' in kwargs:
            kwargs['headers']['Authorization'] = f"Bearer {self.token}"
        elif self.token:
            kwargs['headers'] = {'Authorization': f"Bearer {self.token}"}
        
        try:
            response = self.session.request(method, url, **kwargs)
            
            # Log response details for debugging
            self.logger.debug(f"{method} {url} - Status: {response.status_code}")
            self.logger.debug(f"Response headers: {response.headers}")
            
            # Check for empty response which might indicate an issue
            if response.status_code == 200 and not response.content:
                self.logger.warning(f"Empty 200 response from {url}")
            
            self._check_response_status(response, expected_codes)
            return response
        except requests.exceptions.ConnectionError:
            self.logger.error(f"Connection error: {url}")
            raise WPSecAPIError(ErrorMessages.API_DOWN.value)
        except requests.exceptions.Timeout:
            self.logger.error(f"Request timeout: {url}")
            raise WPSecAPIError(ErrorMessages.API_TIMEOUT.value)
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Request failed: {e}")
            raise WPSecAPIError(f"{Emojis.ERROR} Error: Request failed - {str(e)}")
    
    def authenticate(self, client_id: str, client_secret: str) -> None:
        """Authenticate and obtain access token"""
        url = f"{self.config.API_BASE_URL}/oauth/token"
        payload = {
            "client_id": client_id,
            "client_secret": client_secret,
            "grant_type": "client_credentials"
        }
        
        try:
            response = self._make_request("POST", url, data=payload, expected_codes=[200, 201])
        except WPSecAPIError:
            raise
        
        if b'Client authentication failed' in response.content:
            raise WPSecAPIError(ErrorMessages.AUTH_FAILED.value)
        
        try:
            data = response.json()
        except json.JSONDecodeError:
            raise WPSecAPIError(f"{ErrorMessages.INVALID_JSON.value}:\n{response.text}")
        
        if 'access_token' not in data:
            raise WPSecAPIError(f"{ErrorMessages.NO_ACCESS_TOKEN.value}:\n{data}")
        
        self.token = data['access_token']
    
    def ping(self) -> Dict[str, Any]:
        """Ping the API to check if it's up"""
        start_time = time.time()
        url = f"{self.config.API_BASE_URL}/{self.config.API_VERSION}/ping"
        
        try:
            response = self._make_request("GET", url)
            response_time = time.time() - start_time
            
            if b'Ping Pong' in response.content:
                return {
                    'status': 'up',
                    'response_time': response_time,
                    'slow': response_time > 1
                }
            else:
                return {'status': 'down', 'response_time': response_time}
        except WPSecAPIError:
            return {'status': 'error', 'response_time': time.time() - start_time}
    
    def get_sites(self) -> List[Dict[str, Any]]:
        """Get a list of sites from the API"""
        url = f"{self.config.API_BASE_URL}/{self.config.API_VERSION}/sites"
        
        response = self._make_request("GET", url)
        return response.json()
    
    def add_site(self, title: str, url: str) -> Dict[str, Any]:
        """Add a site to the account"""
        # Validate and clean inputs
        url = url.strip()
        title = title.strip()
        
        # Validate title
        if not title:
            raise WPSecAPIError(
                f"{Emojis.WARNING} Site title cannot be empty\n"
                f"{Emojis.INFO} Please provide a descriptive title for the site"
            )
        
        if len(title) > 255:  # Reasonable limit
            raise WPSecAPIError(
                f"{Emojis.WARNING} Site title is too long (max 255 characters)\n"
                f"{Emojis.INFO} Current length: {len(title)} characters"
            )
        
        # Convert HTML entities in title
        title = html.escape(title)
        
        # Validate URL
        if not url:
            raise WPSecAPIError(
                f"{Emojis.WARNING} Site URL cannot be empty\n"
                f"{Emojis.INFO} Please provide a valid URL starting with http:// or https://"
            )
        
        if not self._is_valid_url(url):
            raise WPSecAPIError(f"{ErrorMessages.INVALID_URL.value}: {url}")
        
        # Additional URL validation
        parsed_url = urlparse(url)
        
        # Check for empty path and add trailing slash if needed
        if not parsed_url.path:
            url = url + '/'
        
        # Check for common URL issues
        if not parsed_url.netloc or parsed_url.netloc == '':
            raise WPSecAPIError(
                f"{Emojis.WARNING} Invalid URL: Missing domain name\n"
                f"{Emojis.INFO} Example: https://example.com"
            )
        
        # Check for spaces in URL
        if ' ' in url:
            raise WPSecAPIError(
                f"{Emojis.WARNING} Invalid URL: Contains spaces\n"
                f"{Emojis.INFO} URLs cannot contain spaces"
            )
        
        # Check for common typos
        if parsed_url.scheme == 'htpp' or parsed_url.scheme == 'htpps':
            raise WPSecAPIError(
                f"{Emojis.WARNING} Invalid URL scheme: '{parsed_url.scheme}'\n"
                f"{Emojis.INFO} Did you mean 'http' or 'https'?"
            )
        
        # Warn about localhost/private IPs (but allow them)
        if parsed_url.netloc in ['localhost', '127.0.0.1', '0.0.0.0']:
            self.logger.warning(f"Adding site with local URL: {url}")
        
        # Check for port in URL
        if ':' in parsed_url.netloc and not parsed_url.netloc.endswith(':80') and not parsed_url.netloc.endswith(':443'):
            # Extract port
            try:
                host, port = parsed_url.netloc.rsplit(':', 1)
                port_num = int(port)
                if port_num < 1 or port_num > 65535:
                    raise ValueError("Invalid port number")
            except ValueError:
                raise WPSecAPIError(
                    f"{Emojis.WARNING} Invalid port in URL: {parsed_url.netloc}\n"
                    f"{Emojis.INFO} Port must be between 1 and 65535"
                )
        
        api_url = f"{self.config.API_BASE_URL}/{self.config.API_VERSION}/sites"
        payload = {"title": title, "url": url}
        
        response = self._make_request("POST", api_url, data=payload, expected_codes=[200, 201])
        
        if b'Error' in response.content:
            raise WPSecAPIError(f"{Emojis.ERROR} Error in response: {response.content.decode('utf-8')}")
        
        if b'"Site added"' in response.content:
            return {'status': 'added', 'title': title, 'url': url}
        
        if b'been taken' in response.content:
            raise WPSecAPIError(f"{ErrorMessages.SITE_EXISTS.value}: {title} ({url})")
        
        # Unknown response
        raise WPSecAPIError(f"{Emojis.WARNING} Unknown response from server: {response.content.decode('utf-8')}")
    
    def list_reports(self, page: int = 1) -> Dict[str, Any]:
        """List reports from the API"""
        url = f"{self.config.API_BASE_URL}/{self.config.API_VERSION}/reports?page={page}"
        
        response = self._make_request("GET", url)
        return response.json()
    
    def get_report(self, report_id: str) -> Dict[str, Any]:
        """Get a report from the API"""
        # Validate report ID format (assuming it should be a 32-char hex string)
        report_id = report_id.strip()
        if len(report_id) != 32 or not all(c in '0123456789abcdefABCDEF' for c in report_id):
            self.logger.warning(f"Report ID '{report_id}' doesn't look like a valid format")
            raise WPSecAPIError(
                f"{Emojis.WARNING} Invalid report ID format: '{report_id}'\n"
                f"{Emojis.INFO} Report IDs should be 32 character hexadecimal strings."
            )
        
        url = f"{self.config.API_BASE_URL}/{self.config.API_VERSION}/report/{report_id}"
        
        response = self._make_request("GET", url)
        
        # Check content type
        content_type = response.headers.get('Content-Type', '')
        if 'text/html' in content_type:
            # Try to extract meaningful error from HTML
            html_text = response.text.strip()
            
            # Common error patterns in HTML responses
            error_patterns = [
                (r'Error\s+(\d+):\s*([^<\n]+)', 'Error {0}: {1}'),  # "Error 1: Report not found"
                (r'<title>([^<]+)</title>', '{0}'),  # Title tag
                (r'<h1>([^<]+)</h1>', '{0}'),  # H1 tag
                (r'<p class="error">([^<]+)</p>', '{0}'),  # Error paragraph
            ]
            
            error_msg = None
            for pattern, format_str in error_patterns:
                import re
                match = re.search(pattern, html_text, re.IGNORECASE)
                if match:
                    error_msg = format_str.format(*match.groups())
                    break
            
            if not error_msg:
                # If no pattern matched, try to get first 100 chars of text content
                text_only = re.sub(r'<[^>]+>', ' ', html_text)  # Remove HTML tags
                text_only = ' '.join(text_only.split())  # Normalize whitespace
                error_msg = text_only[:100] + '...' if len(text_only) > 100 else text_only
            
            self.logger.error(f"Got HTML response: {html_text[:500]}")
            
            # Provide specific error based on the message
            if 'not found' in error_msg.lower():
                raise WPSecAPIError(
                    f"{Emojis.SEARCH} {error_msg}\n"
                    f"{Emojis.INFO} Please check the report ID is correct."
                )
            elif 'permission' in error_msg.lower() or 'access' in error_msg.lower():
                raise WPSecAPIError(
                    f"{Emojis.LOCK} {error_msg}\n"
                    f"{Emojis.INFO} You may not have permission to access this report."
                )
            else:
                raise WPSecAPIError(
                    f"{Emojis.ERROR} API returned HTML instead of JSON: {error_msg}"
                )
        
        # Check for empty response
        if not response.content:
            raise WPSecAPIError(f"{Emojis.ERROR} Empty response from server")
        
        if b'"No resource found' in response.content:
            raise WPSecAPIError(ErrorMessages.REPORT_NOT_FOUND.value)
        
        try:
            return response.json()
        except json.JSONDecodeError as e:
            # Log the actual response for debugging
            self.logger.error(f"JSON decode error: {e}")
            self.logger.error(f"Response content: {response.content[:200]}...")  # First 200 chars
            
            # Try to provide helpful error message
            content_preview = response.content[:100].decode('utf-8', errors='ignore')
            raise WPSecAPIError(
                f"{Emojis.ERROR} Error parsing JSON response. "
                f"Response started with: {repr(content_preview)}"
            )
    
    @staticmethod
    def _is_valid_url(url: str) -> bool:
        """Check if the URL is valid"""
        try:
            result = urlparse(url)
            # More comprehensive validation
            return all([
                result.scheme in ['http', 'https'],
                result.netloc,
                # Check for valid characters in domain
                not any(char in result.netloc for char in [' ', '<', '>', '"', '{', '}', '|', '\\', '^', '`']),
                # Basic domain format check
                '.' in result.netloc or result.netloc in ['localhost', '127.0.0.1', '0.0.0.0']
            ])
        except (ValueError, AttributeError):
            return False


class WPSecCLI:
    """Command-line interface for WPSec"""
    
    def __init__(self):
        self.config = Config()
        self.client = WPSecClient(self.config)
    
    def run(self):
        """Main CLI entry point"""
        parser = self._create_parser()
        args = parser.parse_args()
        
        # Handle command aliases
        action_aliases = {
            'p': 'ping',
            'gs': 'get_sites',
            'sites': 'get_sites',
            'as': 'add_site',
            'add': 'add_site',
            'lr': 'list_reports',
            'reports': 'list_reports',
            'gr': 'get_report',
            'report': 'get_report'
        }
        
        if args.action in action_aliases:
            args.action = action_aliases[args.action]
        
        # Always show banner unless in quiet mode
        self.quiet_mode = hasattr(args, 'quiet') and args.quiet
        if not self.quiet_mode:
            print(BANNER)
            print(f"{Fore.CYAN}Version {self.config.CLI_VERSION}{Style.RESET_ALL}\n")
        
        # Enable debug mode if requested
        if hasattr(args, 'debug') and args.debug:
            logging.getLogger().setLevel(logging.DEBUG)
            if not self.quiet_mode:
                print(f"{Fore.YELLOW}{Emojis.INFO} Debug mode enabled{Style.RESET_ALL}")
        
        # Handle stage flag
        if hasattr(args, 'stage') and args.stage:
            self.config.API_BASE_URL = "https://api-stage.wpsec.com"
            self.client.config.API_BASE_URL = "https://api-stage.wpsec.com"
            if not self.quiet_mode:
                print(f"{Fore.YELLOW}{Emojis.INFO} Using staging API: https://api-stage.wpsec.com{Style.RESET_ALL}")
        
        # Override API URL if provided (takes precedence over --stage)
        if hasattr(args, 'api_url') and args.api_url:
            self.config.API_BASE_URL = args.api_url
            self.client.config.API_BASE_URL = args.api_url
            if not self.quiet_mode:
                print(f"{Fore.YELLOW}{Emojis.INFO} Using API URL: {args.api_url}{Style.RESET_ALL}")
        
        if not args.action:
            parser.print_help()
            return
        
        try:
            # Authenticate if not pinging
            if args.action != "ping":
                if not self.quiet_mode:
                    print(f"{Fore.YELLOW}{Emojis.LOCK} Authenticating...{Style.RESET_ALL}")
                self.client.authenticate(args.client_id, args.client_secret)
                if not self.quiet_mode:
                    print(f"{Fore.GREEN}{Emojis.SUCCESS} Authentication successful!{Style.RESET_ALL}\n")
            
            # Execute action
            action_method = getattr(self, f"_action_{args.action}")
            action_method(args)
            
        except WPSecAPIError as e:
            print(f"{Fore.RED}{str(e)}{Style.RESET_ALL}", file=sys.stderr)
            if not (hasattr(args, 'debug') and args.debug) and not self.quiet_mode:
                print(f"{Fore.YELLOW}{Emojis.INFO} Run with --debug flag for more details{Style.RESET_ALL}")
            sys.exit(1)
        except KeyboardInterrupt:
            if not self.quiet_mode:
                print(f"\n{Fore.YELLOW}{Emojis.WARNING} Operation cancelled by user{Style.RESET_ALL}", file=sys.stderr)
            sys.exit(130)
        except Exception as e:
            print(f"{Fore.RED}{Emojis.ERROR} Unexpected error: {e}{Style.RESET_ALL}", file=sys.stderr)
            if hasattr(args, 'debug') and args.debug:
                import traceback
                print(f"{Fore.YELLOW}\nDebug traceback:{Style.RESET_ALL}")
                traceback.print_exc()
            sys.exit(1)
    
    def _create_parser(self) -> argparse.ArgumentParser:
        """Create argument parser"""
        parser = argparse.ArgumentParser(
            description=f"{self.config.NAME} command-line client {Emojis.ROCKET}",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog=f"{Fore.CYAN}For more information, visit: https://wpsec.com{Style.RESET_ALL}"
        )
        
        parser.add_argument("client_id", help="Client ID")
        parser.add_argument("client_secret", help="Client Secret")
        parser.add_argument(
            '-v', '--version',
            action='version',
            version=f'{self.config.CLI_NAME} {self.config.CLI_VERSION} {Emojis.SPARKLE}'
        )
        
        # Add debug flag with short option
        parser.add_argument('-d', '--debug', action='store_true', help='Enable debug output')
        
        # Add stage flag
        parser.add_argument('--stage', action='store_true', help='Use staging API (https://api-stage.wpsec.com)')
        
        # Add API URL override with short option
        parser.add_argument('-u', '--api-url', help='Override API base URL (default: https://api.wpsec.com)')
        
        # Add quiet mode
        parser.add_argument('-q', '--quiet', action='store_true', help='Quiet mode - minimal output')
        
        subparsers = parser.add_subparsers(dest="action", help="Available actions")
        
        # Ping command
        subparsers.add_parser("ping", help=f"{Emojis.PING} Ping the API", aliases=['p'])
        
        # Get sites command
        subparsers.add_parser("get_sites", help=f"{Emojis.SITE} Get all sites", aliases=['gs', 'sites'])
        
        # Add site command
        add_site_parser = subparsers.add_parser("add_site", help=f"{Emojis.ADD} Add a new site", aliases=['as', 'add'])
        add_site_parser.add_argument("title", help="Site title")
        add_site_parser.add_argument("url", help="Site URL (must include http:// or https://)")
        
        # List reports command
        list_reports_parser = subparsers.add_parser("list_reports", help=f"{Emojis.LIST} List all reports", aliases=['lr', 'reports'])
        list_reports_parser.add_argument(
            "-p", "--page", type=int, default=1, help="Page number (default: 1)"
        )
        
        # Get report command
        get_report_parser = subparsers.add_parser("get_report", help=f"{Emojis.REPORT} Get a specific report", aliases=['gr', 'report'])
        get_report_parser.add_argument("report_id", help="Report ID (32 character hex string)")
        get_report_parser.add_argument('-o', '--output', help='Output to file instead of stdout')
        
        return parser
    
    def _action_ping(self, args):
        """Handle ping action"""
        if not self.quiet_mode:
            print(f"{Fore.CYAN}{Emojis.PING} Pinging {self.config.NAME} API...{Style.RESET_ALL}")
        result = self.client.ping()
        
        if result['status'] == 'up':
            if result['slow']:
                print(f"{Fore.YELLOW}{Emojis.WARNING} {self.config.NAME} API is up, but response time is slow: "
                      f"{result['response_time']:.2f} seconds!{Style.RESET_ALL}")
            else:
                if self.quiet_mode:
                    print(f"up ({result['response_time']:.2f}s)")
                else:
                    print(f"{Fore.GREEN}{Emojis.SUCCESS} {self.config.NAME} API is up and running \\o/. "
                          f"Response time: {result['response_time']:.2f} seconds{Style.RESET_ALL}")
        else:
            print(f"{Fore.RED}{ErrorMessages.API_DOWN.value}{Style.RESET_ALL}")
    
    def _action_get_sites(self, args):
        """Handle get_sites action"""
        if not self.quiet_mode:
            print(f"{Fore.CYAN}{Emojis.SEARCH} Fetching sites...{Style.RESET_ALL}\n")
        sites = self.client.get_sites()
        self._pretty_print_sites(sites)
    
    def _action_add_site(self, args):
        """Handle add_site action"""
        if not self.quiet_mode:
            print(f"{Fore.CYAN}{Emojis.ADD} Adding new site...{Style.RESET_ALL}")
        result = self.client.add_site(args.title, args.url)
        if self.quiet_mode:
            print(f"{result['title']} ({result['url']})")
        else:
            print(f"{Fore.GREEN}{Emojis.SUCCESS} Site added: {result['title']} ({result['url']}){Style.RESET_ALL}")
    
    def _action_list_reports(self, args):
        """Handle list_reports action"""
        # First, get the first page to find total pages
        if not self.quiet_mode:
            print(f"{Fore.CYAN}{Emojis.LIST} Fetching reports information...{Style.RESET_ALL}")
        
        # Get first page to get pagination info
        first_page_data = self.client.list_reports(page=1)
        
        if 'data' not in first_page_data or 'paginate' not in first_page_data['data']:
            print(f"{Fore.RED}{Emojis.ERROR} Error: Invalid response format{Style.RESET_ALL}")
            return
        
        pagination_info = first_page_data['data']['paginate']
        total_pages = pagination_info.get('last_page', 1)
        total_reports = pagination_info.get('total', 0)
        per_page = pagination_info.get('per_page', 50)
        
        # Calculate the actual page to fetch (reverse the page number)
        # If user wants page 1, we fetch the last page
        # If user wants page 2, we fetch the second-to-last page, etc.
        actual_page = total_pages - args.page + 1
        
        if actual_page < 1 or actual_page > total_pages:
            print(f"{Fore.RED}{Emojis.ERROR} Error: Page {args.page} is out of range. "
                  f"Valid range is 1 to {total_pages}{Style.RESET_ALL}")
            return
        
        # Fetch the reports
        if not self.quiet_mode and actual_page != 1:
            print(f"{Fore.CYAN}{Emojis.LIST} Fetching reports (page {args.page} of {total_pages})...{Style.RESET_ALL}\n")
        
        # If we already have the data (when actual_page is 1), use it
        if actual_page == 1:
            reports = first_page_data
        else:
            reports = self.client.list_reports(page=actual_page)
        
        # Check if we need to fetch additional reports to fill the page
        # This happens when showing "page 1" (which is the last API page) and it has fewer than 50 reports
        if 'data' in reports:
            report_data = reports['data']
            report_list = [r for r in report_data.values() if isinstance(r, dict) and 'reportId' in r]
            
            # If we're on user's page 1 and have less than full page, fetch previous API page too
            if args.page == 1 and len(report_list) < per_page and actual_page > 1:
                if not self.quiet_mode:
                    print(f"{Fore.CYAN}{Emojis.LIST} Fetching additional reports...{Style.RESET_ALL}\n")
                
                # Fetch the previous API page
                prev_page_data = self.client.list_reports(page=actual_page - 1)
                if 'data' in prev_page_data:
                    prev_report_list = [r for r in prev_page_data['data'].values() 
                                      if isinstance(r, dict) and 'reportId' in r]
                    
                    # Combine the reports: newest (from last page) + some from previous page
                    needed = per_page - len(report_list)
                    # Take the newest reports from the previous page
                    additional_reports = prev_report_list[-needed:] if needed < len(prev_report_list) else prev_report_list
                    
                    # Combine: current page reports + additional reports
                    combined_reports = report_list + additional_reports
                    
                    # Reverse to show newest first
                    combined_reports.reverse()
                    
                    # Update the report data
                    report_data.clear()
                    for i, report in enumerate(combined_reports[:per_page]):  # Limit to per_page
                        report_data[str(i)] = report
            else:
                # Just reverse the current page
                report_list.reverse()
                report_data.clear()
                for i, report in enumerate(report_list):
                    report_data[str(i)] = report
        
        # Print with the user's page number (not the actual fetched page)
        self._pretty_print_reports(reports, args.page, total_pages)
    
    def _action_get_report(self, args):
        """Handle get_report action"""
        if not self.quiet_mode:
            print(f"{Fore.CYAN}{Emojis.REPORT} Fetching report {args.report_id}...{Style.RESET_ALL}\n")
        report = self.client.get_report(args.report_id)
        
        # Pretty print JSON with syntax highlighting if possible
        json_str = json.dumps(report, indent=4)
        
        # Handle output to file if requested
        if hasattr(args, 'output') and args.output:
            try:
                with open(args.output, 'w') as f:
                    f.write(json_str)
                if not self.quiet_mode:
                    print(f"{Fore.GREEN}{Emojis.SUCCESS} Report saved to: {args.output}{Style.RESET_ALL}")
                return
            except IOError as e:
                print(f"{Fore.RED}{Emojis.ERROR} Error writing to file: {e}{Style.RESET_ALL}", file=sys.stderr)
                sys.exit(1)
        
        # Print to stdout
        if COLORAMA_AVAILABLE and not self.quiet_mode:
            # Simple JSON syntax highlighting
            json_str = json_str.replace(': true', f': {Fore.CYAN}true{Style.RESET_ALL}')
            json_str = json_str.replace(': false', f': {Fore.CYAN}false{Style.RESET_ALL}')
            json_str = json_str.replace(': null', f': {Fore.MAGENTA}null{Style.RESET_ALL}')
        print(json_str)
    
    def _pretty_print_sites(self, sites: List[Dict[str, Any]]):
        """Print a list of sites in a pretty way"""
        if not sites:
            if self.quiet_mode:
                return
            print(f"{Fore.YELLOW}{Emojis.WARNING} No sites found.{Style.RESET_ALL}")
            return
        
        # Calculate column widths dynamically
        id_width = max(len(str(site.get('id', ''))) for site in sites)
        id_width = max(id_width, 2) + 2  # Minimum width of 2 for "ID" + padding
        
        # Unescape HTML entities for display
        for site in sites:
            if 'name' in site:
                site['name'] = html.unescape(site['name'])
            if 'title' in site:
                site['title'] = html.unescape(site['title'])
        
        name_width = max(len(site.get('name', '')) for site in sites)
        name_width = max(name_width, 5) + 2  # Minimum width of 5 for "Title" + padding
        
        # In quiet mode, just print basic info
        if self.quiet_mode:
            for site in sites:
                print(f"{site.get('id', 'N/A')}\t{site.get('name', 'N/A')}\t{site.get('title', site.get('url', 'N/A'))}")
            return
        
        # Print header
        print(f"{Fore.CYAN}{Style.BRIGHT}{'ID':<{id_width}}{'Title':<{name_width}}{'URL'}{Style.RESET_ALL}")
        print(f"{Fore.BLUE}{'-' * id_width}{'-' * name_width}{'-' * 40}{Style.RESET_ALL}")
        
        # Print sites
        for i, site in enumerate(sites):
            site_id = str(site.get('id', 'N/A'))
            site_name = site.get('name', 'N/A')
            site_url = site.get('title', site.get('url', 'N/A'))
            
            # Alternate row colors
            if i % 2 == 0:
                print(f"{site_id:<{id_width}}{site_name:<{name_width}}{site_url}")
            else:
                print(f"{Style.DIM}{site_id:<{id_width}}{site_name:<{name_width}}{site_url}{Style.RESET_ALL}")
        
        print(f"\n{Fore.GREEN}{Emojis.SUCCESS} Total sites: {len(sites)}{Style.RESET_ALL}")
    
    def _pretty_print_reports(self, reports: Dict[str, Any], page: int, total_pages: int = None):
        """Print a list of reports in a pretty way"""
        if 'data' not in reports:
            if not self.quiet_mode:
                print(f"{Fore.RED}{Emojis.ERROR} Error: Invalid response format{Style.RESET_ALL}")
            return
        
        report_data = reports['data']
        report_list = [r for r in report_data.values() if isinstance(r, dict) and 'reportId' in r]
        
        if not report_list:
            if not self.quiet_mode:
                print(f"{Fore.YELLOW}{ErrorMessages.NO_REPORTS.value.format(page)}{Style.RESET_ALL}")
            return
        
        # In quiet mode, just print basic info
        if self.quiet_mode:
            for report in report_list:
                print(f"{report.get('reportId', 'N/A')}\t{report.get('createdAt', 'N/A')}\t{report.get('url', 'N/A')}")
            return
        
        print(f"{Fore.GREEN}{Emojis.REPORT} Listing {len(report_list)} reports below (newest first):{Style.RESET_ALL}\n")
        
        # Print header
        print(f"{Fore.CYAN}{Style.BRIGHT}{'Report ID':<35}{'Created at':<25}{'URL':<50}{Style.RESET_ALL}")
        print(f"{Fore.BLUE}{'-' * 35}{'-' * 25}{'-' * 50}{Style.RESET_ALL}")
        
        # Print reports
        for i, report in enumerate(report_list):
            report_id = report.get('reportId', 'N/A')
            created_at = report.get('createdAt', 'N/A')
            url = report.get('url', 'N/A')
            
            # Alternate row colors
            if i % 2 == 0:
                print(f"{report_id:<35}{created_at:<25}{url:<50}")
            else:
                print(f"{Style.DIM}{report_id:<35}{created_at:<25}{url:<50}{Style.RESET_ALL}")
        
        # Print pagination info
        if 'paginate' in report_data:
            pagination = report_data['paginate']
            if total_pages is None:
                total_pages = pagination.get('last_page', '?')
            total_reports = pagination.get('total', '?')
            
            print(f"\n{Fore.CYAN}{Emojis.INFO} Page {page} of {total_pages} "
                  f"({total_reports} reports total){Style.RESET_ALL}")
            
            if page == 1 and total_pages != '?' and isinstance(total_pages, int) and total_pages > 1:
                print(f"{Fore.YELLOW}{Emojis.INFO} Hint: Use -p/--page to paginate results{Style.RESET_ALL}")


def main():
    """Main entry point"""
    # Add debug mode via environment variable
    import os
    if os.environ.get('WPSEC_DEBUG'):
        logging.getLogger().setLevel(logging.DEBUG)
        print(f"{Emojis.INFO} Debug mode enabled")
    
    if not COLORAMA_AVAILABLE:
        print(f"{Emojis.WARNING} Install colorama for colored output: pip install colorama")
    
    cli = WPSecCLI()
    cli.run()


if __name__ == "__main__":
    main()