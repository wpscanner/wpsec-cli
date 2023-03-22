![Python](https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54)
# WPSec Command-Line Client
A simple command-line client for interacting with the WPSec API.

## Requirements
Python 3.6 or higher
### Installation
Save the Python script (wpsec_client.py) to your local machine.
Install the required packages with the following command:
```
pip install requests
```
## Configuration

You need to provide the client_id and client_secret as command-line arguments. The Rest JSON API keys can be fetched here: https://wpsec.com/account/api.php

## Usage
Check that the API is up and running
```
python wpsec-cli.py CLIENT_ID CLIENT_SECRET ping
```

And the reponse should be something like:
```
WPSec API is up and running \o/. Response time: 0.17 seconds
```

Get all sites
```
python wpsec-cli.py CLIENT_ID CLIENT_SECRET get_sites
```
Add a new site
```
python wpsec-cli.py CLIENT_ID CLIENT_SECRET add_site "Site Title" "https://example.com"
```
List all reports with pagination
```
python wpsec-cli.py CLIENT_ID  CLIENT_SECRET list_reports --page 2
```
Get a specific report
```
python wpsec-cli.py CLIENT_ID CLIENT_SECRET get_report REPORT_ID
```
Replace CLIENT_ID, CLIENT_SECRET, and REPORT_ID with appropriate values.
