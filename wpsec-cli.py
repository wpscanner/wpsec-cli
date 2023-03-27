#!env python3
"""WPsec command-line client"""
# -*- coding: utf-8 -*-
##
# WPSec command-line client
##
# Updated 2023-03-27
# Author: Jonas Lejon <jlejon@wpsec.com>
# License: MIT
# Version: 0.1.1
##

from urllib.parse import urlparse
import argparse
import json
import time
import sys
import requests


CLI_VERSION = "0.1.1"
NAME = "WPSec"
CLI_NAME = f"{NAME} CLI"
API_VERSION = "v1"
API_BASE_URL = "https://api.wpsec.com"

GENERIC_ERROR = f"Error: {NAME} API is down. Please create a new support ticket at: https://support.wpsec.com/hc/en-us/requests/new&tf_subject=API%20Error"

# 31337 ASCII art
BANNER = """__ __ ___ __ ___ ___ __
\\ V  V / '_ (_-</ -_) _|
 \\_/\\_/| .__/__/\\___\\__|
       |_|"""

def is_url(url):
    """Check if the URL is valid"""
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except ValueError:
        return False


def get_token(client_id, client_secret):
    """Get a token from the API"""
    url = f"{API_BASE_URL}/oauth/token"
    payload = {
        "client_id": client_id,
        "client_secret": client_secret,
        "grant_type": "client_credentials"
    }
    try:
        response = requests.post(
            url, data=payload, headers={
                "User-Agent": f"{CLI_NAME}/{CLI_VERSION}"}, timeout=10)
    except requests.exceptions.ConnectionError:
        print(GENERIC_ERROR)
        sys.exit(1)
    if b'Client authentication failed' in response.content:
        print("Error: Client authentication failed, invalid client ID or client secret.")
        sys.exit(1)
    try:
        ret = response.json()['access_token']
    except json.decoder.JSONDecodeError:
        print(GENERIC_ERROR)
        sys.exit(1)
    except KeyError:
        print(GENERIC_ERROR)
        sys.exit(1)

    return ret


def pretty_print_sites(sites):
    """Print a list of sites in a pretty way"""
    print(f"{'ID':<10}{'Title':<30}{'URL':<40}")
    for site in sites:
        print(f"{site['id']:<10}{site['name']:<30}{site['title']:<40}")


def get_sites(token):
    """Get a list of sites from the API"""
    url = f"{API_BASE_URL}/{API_VERSION}/sites"
    headers = {"Authorization": f"Bearer {token}",
               "User-Agent": f"{CLI_NAME}/{CLI_VERSION}"
               }
    response = requests.get(url, headers=headers, timeout=10)
    if b'Error' in response.content or response.status_code != 200:
        print(f"Error: {response.content.decode('utf-8')}")
        sys.exit(1)

    sites = response.json()
    pretty_print_sites(sites)

def add_site(token, title, url):
    """Add a site to the account"""
    # Ugly fix due to api bug
    url = url.strip()
    title = title.strip()

    if not is_url(url):
        print(f"Invalid URL: {url}")
        sys.exit(1)

    api_url = f"{API_BASE_URL}/{API_VERSION}/sites"
    headers = {"Authorization": f"Bearer {token}",
               "User-Agent": f"{CLI_NAME}/{CLI_VERSION}"}
    payload = {"title": title, "url": url}
    response = requests.post(
        api_url,
        headers=headers,
        data=payload,
        timeout=10)

    if b'Error' in response.content:
        print(f"Error in response: {response.content.decode('utf-8')}")
        sys.exit(1)
    if b'"Site added"' in response.content:
        print(f"Site added: {title} ({url})")
        return
    if b'been taken' in response.content:
        print(f"Site already exists on your account: {title} ({url})")
        sys.exit(1)

    # Unknown response, print it
    print("Uknown response from server: {}" .format(
        response.content.decode("utf-8")))


def pretty_print_pagination(pagination, page):
    """Print pagination info in a pretty way"""
    print("")
    print(
        f"Page {pagination['current_page']} of {pagination['last_page']} ({pagination['total']} reports total)")
    if page == 1:
        print("Hint: Use --page to paginate results)")


def pretty_print_reports(reports, page):
    """Print a list of reports in a pretty way"""
    no_reports = len(reports['data'].values()) - 1
    if no_reports == 0:
        print(f"Error: No reports found on page {page}")
        return
    print(f"Listing {no_reports} reports below:")
    print()
    print(f"{'Report ID':<35}{'Created at':<25}{'URL':<50}")

    for report in reports['data'].values():
        if 'reportId' in report:
            print(
                f"{report['reportId']:<35}{report['createdAt']:<25}{report['url']:<50}")

    pretty_print_pagination(reports['data']['paginate'], page)


def list_reports(token, page=1):
    """List reports from the API"""
    url = f"{API_BASE_URL}/{API_VERSION}/reports?page={page}"
    headers = {"Authorization": f"Bearer {token}",
               "User-Agent": f"{CLI_NAME}/{CLI_VERSION}"}
    response = requests.get(url, headers=headers, timeout=10)
    if b'Error' in response.content or response.status_code != 200:
        print(response.content.decode("utf-8"))
        sys.exit(1)
    reports = response.json()
    pretty_print_reports(reports, page)


def get_report(token, report_id):
    """Get a report from the API"""
    url = f"{API_BASE_URL}/{API_VERSION}/report/{report_id}"
    headers = {"Authorization": f"Bearer {token}",
               "User-Agent": f"{CLI_NAME}/{CLI_VERSION}"}
    response = requests.get(url, headers=headers, timeout=10)
    if b'"No resource found' in response.content:
        print("Error: Report not found")
        sys.exit(1)
    if b'Error' in response.content or response.status_code != 200:
        print(response.content.decode("utf-8"))
        sys.exit(1)
    try:
        print(json.dumps(response.json(), indent=4))
    except json.decoder.JSONDecodeError:
        print("Error parsing JSON report")


def ping():
    """Ping the API to check if it's up"""
    # Calculate response time
    start = time.time()
    url = f"{API_BASE_URL}/{API_VERSION}/ping"
    response = requests.get(
        url,
        headers={
            "User-Agent": f"{CLI_NAME}/{CLI_VERSION}"},
        timeout=10)
    end_time = time.time() - start
    if b'Ping Pong' in response.content:
        if end_time > 1:  # Slow response times?
            print(
                f"{NAME} API is up, but response time is slow: {end_time:.2f} seconds!")
        else:
            print(
                f"{NAME} API is up and running \\o/. Response time: {end_time:.2f} seconds")
    else:
        print(GENERIC_ERROR)


def main():
    """Main function"""
    parser = argparse.ArgumentParser(description=f"{NAME} command-line client")
    parser.add_argument("client_id", help="Client ID")
    parser.add_argument("client_secret", help="Client Secret")
    parser.add_argument(
        '--version',
        action='version',
        version=f'{CLI_NAME} {CLI_VERSION}')
    subparsers = parser.add_subparsers(dest="action")

    subparsers.add_parser("ping", help="Ping the API")
    subparsers.add_parser("get_sites", help="Get all sites")

    add_site_parser = subparsers.add_parser("add_site", help="Add a new site")
    add_site_parser.add_argument("title", help="Site title")
    add_site_parser.add_argument("url", help="Site URL")

    list_reports_parser = subparsers.add_parser(
        "list_reports", help="List all reports")
    list_reports_parser.add_argument(
        "--page", type=int, default=1, help="Page number")

    get_report_parser = subparsers.add_parser(
        "get_report", help="Get a specific report")
    get_report_parser.add_argument("report_id", help="Report ID")

    args = parser.parse_args()

    token = get_token(args.client_id, args.client_secret)

    if args.action == "ping":
        ping()  # Token is not really required for ping
    elif args.action == "get_sites":
        get_sites(token)
    elif args.action == "add_site":
        add_site(token, args.title, args.url)
    elif args.action == "list_reports":
        list_reports(token, args.page)
    elif args.action == "get_report":
        get_report(token, args.report_id)
    else:
        print(BANNER)
        parser.print_help()


if __name__ == "__main__":
    main()
