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

You can provide the client_id and client_secret as command-line arguments or set them as environment variables:

```
export WPSEC_CLIENT_ID=your_client_id
export WPSEC_CLIENT_SECRET=your_client_secret
```
Replace your_client_id and your_client_secret with your actual client ID and secret. You need a premium WPSec account to list the client id and client secret.

## Usage
Check that the API is up and running
```
python wpsec_client.py CLIENT_ID CLIENT_SECRET ping
```

And the reponse should be something like:
```
WPSec API is up and running \o/. Response time: 0.17 seconds
```

Get all sites
```
python wpsec_client.py --client_id CLIENT_ID --client_secret CLIENT_SECRET get_sites
```
Add a new site
```
python wpsec_client.py --client_id CLIENT_ID --client_secret CLIENT_SECRET add_site "Site Title" "https://example.com"
```
List all reports with pagination
```
python wpsec_client.py --client_id CLIENT_ID --client_secret CLIENT_SECRET list_reports --page 1 --per_page 10
```
Get a specific report
```
python wpsec_client.py --client_id CLIENT_ID --client_secret CLIENT_SECRET get_report REPORT_ID
```
Replace CLIENT_ID, CLIENT_SECRET, and REPORT_ID with appropriate values.
