![Python](https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54) ![Docker](https://img.shields.io/badge/docker-%230db7ed.svg?style=for-the-badge&logo=docker&logoColor=white)
# WPSec.com Command-Line Client
A simple command-line client for interacting with the WPSec API. API Documentation can be found [here](https://api.wpsec.com/api/documentation).

## Requirements
Python 3.6 or higher
### Installation 
Save the Python script [wpsec-cli.py](wpsec-cli.py) above to your local machine.
Install the required packages with the following command:
```
pip install requests
```
### Installation docker
You can also use the docker version of the command line tool. Like this:

```
docker pull docker.io/jonaslejon/wpsec-cli:latest
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
Example output:
```
Listing 9 reports below:

Report ID                          Created at               URL
45f8fa215fd3d38XXXXXXXXXXXXXXXXX   2023-03-20 02:10:19      https://modernminds.nl/
acb8a076cfc4891XXXXXXXXXXXXXXXXX   2023-03-20 02:52:18      https://isoc.se/blogg/
ef84ac5258a4483XXXXXXXXXXXXXXXXX   2023-03-20 03:16:52      https://medicin24.se
b032e6d8a1ee91bXXXXXXXXXXXXXXXXX   2023-03-20 03:32:18      https://sunchargers.eu/
ff3ed663bc4e119XXXXXXXXXXXXXXXXX   2023-03-20 03:42:50      https://biljetterna.se
4818763651aefa4XXXXXXXXXXXXXXXXX   2023-03-20 13:20:41      https://scanme2.wpsec.com/
cd4d1428b664f33XXXXXXXXXXXXXXXXX   2023-03-20 19:24:54      https://travelgadgets.eu/
6b150dfa2cc49d8XXXXXXXXXXXXXXXXX   2023-03-20 20:01:33      https://irland.se
ba9f8b33a012530XXXXXXXXXXXXXXXXX   2023-03-20 21:40:08      https://modernminds.nl/


Page 184 of 184 (9176 reports total)
```
Get a specific report
```
python wpsec-cli.py CLIENT_ID CLIENT_SECRET get_report REPORT_ID
```
Replace CLIENT_ID, CLIENT_SECRET, and REPORT_ID with appropriate values.

## Usage docker

Read more here: https://hub.docker.com/r/jonaslejon/wpsec-cli

# Building docker 
Just run
```
docker build -t jonaslejon/wpsec-cli:0.1.0 -t jonaslejon/wpsec-cli:latest .
```
