![Python](https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54) ![Docker](https://img.shields.io/badge/docker-%230db7ed.svg?style=for-the-badge&logo=docker&logoColor=white)

# WPSec.com Command-Line Client

A powerful command-line interface for the WPSec WordPress security scanning service. Manage your sites, run security reports, and monitor your WordPress installations from the terminal. API Documentation can be found [here](https://api.wpsec.com/api/documentation), a Premium account is needed at WPSec.com.

```
__ __ ___ __ ___ ___ __
\ V  V / '_ (_-</ -_) _|
 \_/\_/| .__/__/\___\__|
       |_|
```

## ✨ Features

- 🚀 **Fast API Integration** - Direct connection to WPSec's security scanning API
- 🌐 **Site Management** - Add and list WordPress sites for monitoring
- 📊 **Report Management** - View detailed security reports with JSON output
- 🏓 **Health Monitoring** - Ping API endpoints to check service status
- 🎨 **Colorized Output** - Beautiful terminal output with emojis and colors
- 🔄 **Retry Logic** - Robust error handling with automatic retries
- 🐛 **Debug Mode** - Detailed logging for troubleshooting
- 📁 **File Output** - Save reports to files for further analysis

## 📋 Requirements

- Python 3.6 or higher
- `requests` library
- `colorama` (optional, for colored output)

### Installation

```bash
# Clone the repository
git clone https://github.com/wpscanner/wpsec-cli.git
cd wpsec-cli

# Install dependencies
pip install -r requirements.txt
```

**Alternative: Download single file**
```bash
# Download just the Python script
wget https://raw.githubusercontent.com/wpscanner/wpsec-cli/main/wpsec-cli.py

# Install dependencies manually
pip install requests colorama
```

### Installation with Docker

You can also use the docker version of the command line tool:

```bash
docker pull docker.io/jonaslejon/wpsec-cli:latest
```

### Basic Usage

```bash
# Check API status
python wpsec-cli.py CLIENT_ID CLIENT_SECRET ping

# List all your sites
python wpsec-cli.py CLIENT_ID CLIENT_SECRET get_sites

# Add a new site
python wpsec-cli.py CLIENT_ID CLIENT_SECRET add_site "My WordPress Site" "https://example.com"

# List security reports
python wpsec-cli.py CLIENT_ID CLIENT_SECRET list_reports

# Get a specific report
python wpsec-cli.py CLIENT_ID CLIENT_SECRET get_report REPORT_ID
```

### Usage with Docker

Read more here: https://hub.docker.com/r/jonaslejon/wpsec-cli

```bash
# Using docker
docker run --rm jonaslejon/wpsec-cli:latest CLIENT_ID CLIENT_SECRET ping
```

## 📋 Requirements

- Python 3.6 or higher
- `requests` library
- `colorama` (optional, for colored output)

Install dependencies:

```bash
pip install requests colorama
```

## 🔧 Command Reference

### Global Options

| Option | Short | Description |
|--------|-------|-------------|
| `--debug` | `-d` | Enable debug output |
| `--quiet` | `-q` | Minimal output mode |
| `--stage` | | Use staging API environment |
| `--api-url` | `-u` | Override API base URL |
| `--version` | `-v` | Show version information |

### Commands

#### `ping` (alias: `p`)
Check if the WPSec API is responding.

```bash
python wpsec-cli.py CLIENT_ID CLIENT_SECRET ping
```

#### `get_sites` (aliases: `gs`, `sites`)
List all WordPress sites in your account.

```bash
python wpsec-cli.py CLIENT_ID CLIENT_SECRET get_sites
```

#### `add_site` (aliases: `as`, `add`)
Add a new WordPress site for monitoring.

```bash
python wpsec-cli.py CLIENT_ID CLIENT_SECRET add_site "Site Title" "https://example.com"
```

**Arguments:**
- `title` - Descriptive name for the site
- `url` - Full URL including http:// or https://

#### `list_reports` (aliases: `lr`, `reports`)
List security reports with pagination.

```bash
python wpsec-cli.py CLIENT_ID CLIENT_SECRET list_reports --page 1
```

**Options:**
- `--page`, `-p` - Page number (default: 1)

#### `get_report` (aliases: `gr`, `report`)
Retrieve a specific security report.

```bash
python wpsec-cli.py CLIENT_ID CLIENT_SECRET get_report REPORT_ID
```

**Options:**
- `--output`, `-o` - Save to file instead of stdout

**Arguments:**
- `report_id` - 32-character hexadecimal report identifier

Replace CLIENT_ID, CLIENT_SECRET, and REPORT_ID with appropriate values.

## 🔐 Configuration

You need to provide the client_id and client_secret as command-line arguments. The Rest JSON API keys (CLIENT_ID and CLIENT_SECRET) can be fetched here: https://wpsec.com/account/api.php

You'll need API credentials from your WPSec account:

1. Log into your WPSec dashboard
2. Navigate to API settings: https://wpsec.com/account/api.php
3. Generate a new Client ID and Client Secret
4. Use these credentials with every command

### Environment Variables (Optional)

Set debug mode via environment variable:

```bash
export WPSEC_DEBUG=1
python wpsec.py CLIENT_ID CLIENT_SECRET ping
```

## 📊 Output Formats

### Standard Output
Beautiful formatted tables with colors and emojis:

```
✅ WPSec API is up and running \o/. Response time: 0.23 seconds

🌐 Listing 3 sites below:

ID    Title              URL
--    -----              ---
123   My WordPress Site  https://example.com
124   Blog Site          https://blog.example.com
125   Shop Site          https://shop.example.com

✅ Total sites: 3
```

### Quiet Mode
Tab-separated values for scripting:

```bash
python wpsec-cli.py CLIENT_ID CLIENT_SECRET get_sites --quiet
123	My WordPress Site	https://example.com
124	Blog Site	https://blog.example.com
125	Shop Site	https://shop.example.com
```

### JSON Output
Reports are output as formatted JSON:

```bash
python wpsec-cli.py CLIENT_ID CLIENT_SECRET get_report REPORT_ID --output report.json
```

## 🐳 Building Docker Image

Just run:

```bash
docker build -t jonaslejon/wpsec-cli:0.5.0 -t jonaslejon/wpsec-cli:latest .
```

Build with SBOM:

```bash
DOCKER_BUILDKIT=1 docker build --attest type=sbom --attest type=provenance -t jonaslejon/wpsec-cli:0.5.0 -t jonaslejon/wpsec-cli:latest .
```

## 🛠️ Advanced Usage

### Using with Scripts

```bash
#!/bin/bash
CLIENT_ID="your_client_id"
CLIENT_SECRET="your_client_secret"

# Check if API is available
if python wpsec-cli.py $CLIENT_ID $CLIENT_SECRET ping --quiet | grep -q "up"; then
    echo "API is healthy, proceeding..."
    # Add your automation logic here
else
    echo "API is down, aborting"
    exit 1
fi
```

### Batch Operations

```bash
# Add multiple sites
sites=(
    "Site 1,https://site1.com"
    "Site 2,https://site2.com"
    "Site 3,https://site3.com"
)

for site in "${sites[@]}"; do
    IFS=',' read -r title url <<< "$site"
    python wpsec-cli.py CLIENT_ID CLIENT_SECRET add_site "$title" "$url"
done
```

### Using Staging Environment

```bash
# Test against staging API
python wpsec-cli.py CLIENT_ID CLIENT_SECRET --stage ping

# Or use custom API URL
python wpsec-cli.py CLIENT_ID CLIENT_SECRET --api-url "https://custom-api.example.com" ping
```

## 🐛 Troubleshooting

### Common Issues

**Authentication Failed**
```
🔐 Error: Client authentication failed, invalid client ID or client secret.
```
- Verify your credentials are correct
- Check if credentials have expired
- Ensure you're using the correct API environment

**Invalid URL Format**
```
🌐 Error: Invalid URL format: example.com
```
- URLs must include `http://` or `https://`
- Example: `https://example.com` not `example.com`

**API Timeout**
```
⏱️ Error: WPSec API timeout. Please try again later.
```
- Check your internet connection
- Try using `--debug` flag for more details
- Consider using staging environment for testing

### Debug Mode

Enable verbose logging:

```bash
python wpsec-cli.py CLIENT_ID CLIENT_SECRET --debug ping
```

This will show:
- HTTP request/response details
- Authentication tokens (partially masked)
- API response times
- Error stack traces

### Getting Help

- Check the debug output first: `--debug`
- Verify API status: `ping` command
- Contact support: support@wpsec.com

## 🔄 Error Handling

The CLI includes robust error handling with:

- **Automatic Retries** - Failed requests are retried with exponential backoff
- **Rate Limiting** - Handles 429 responses gracefully
- **Network Issues** - Detects connection problems and timeouts
- **Validation** - Input validation for URLs, IDs, and parameters
- **Helpful Messages** - Clear error descriptions with suggested fixes

## 📈 Performance

- **Session Reuse** - HTTP connections are reused for efficiency
- **Retry Strategy** - Smart retry logic for temporary failures
- **Timeout Handling** - Configurable timeouts prevent hanging
- **Response Validation** - Validates API responses for reliability

## 📝 Todo

- Remove websites from the CLI

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

### Development Setup

```bash
git clone https://github.com/wpscanner/wpsec-cli.git
cd wpsec-cli

# Install development dependencies
pip install -r requirements.txt

# Run tests
python -m pytest tests/

# Run linting
flake8 wpsec-cli.py
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🔗 Links

- [WPSec Website](https://wpsec.com)
- [API Documentation](https://api.wpsec.com/api/documentation)
- [Docker Hub](https://hub.docker.com/r/jonaslejon/wpsec-cli)
- [Support](mailto:support@wpsec.com)
- [GitHub Issues](https://github.com/wpscanner/wpsec-cli/issues)

## 📊 Version History

### v0.5.0 (Current)
- Added colorized output with emojis
- Improved error handling and validation
- Added debug mode and quiet mode
- Enhanced report pagination
- Better URL validation
- Added file output for reports

### Previous Versions
See [CHANGELOG.md](CHANGELOG.md) for full version history.

---

Made with ❤️ by the WPSec team