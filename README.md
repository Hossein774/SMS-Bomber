# 📱 SMS & Call Bomber 2.0

A comprehensive SMS and Call bombing tool for **security testing purposes only**.

> ⚠️ **DISCLAIMER**: This tool is intended for authorized security testing only. Only use on devices you own or have explicit permission to test. Unauthorized use may violate laws and regulations.

## 🚀 Features

- **SMS Bombing**: 17 verified working Iranian SMS providers (100% success rate)
- **Call Bombing**: Voice OTP and callback flooding
- **Provider Discovery**: Automatically find new SMS endpoints
- **Health Monitoring**: Test and remove dead providers
- **Proxy Support**: Rotate proxies to avoid blocks
- **Rich UI**: Beautiful terminal interface with progress bars

## 📁 Project Structure

```
SMS-Bomber/
├── run.py                      # Main entry point
├── demo_bomber.py              # Quick demo script
├── discover_providers.py       # 🆕 Provider discovery tool
├── integrate_providers.py      # 🆕 Add discovered providers
├── update_providers.py         # Test provider health
├── manage_providers.py         # Provider management CLI
├── test_call_providers.py      # Test call providers
│
├── sms_bomber/
│   ├── main.py                 # Main bombing logic
│   ├── api/
│   │   ├── providers.py        # SMS provider registry
│   │   ├── call_providers.py   # Call provider registry
│   │   ├── client.py           # SMS API client
│   │   ├── call_client.py      # Call API client
│   │   └── provider_updater.py # Provider health checker
│   ├── core/
│   │   ├── config.py           # Configuration
│   │   └── logger.py           # Logging
│   ├── tools/
│   │   ├── __init__.py
│   │   └── provider_discovery.py  # 🆕 Discovery engine
│   └── ui/
│       ├── console.py          # Terminal UI
│       └── progress.py         # Progress tracking
│
├── data/                       # 🆕 Data directory
│   ├── discovered_providers.json
│   └── discovered_providers.py
│
└── logs/                       # Log files
```

## 🔧 Installation

```bash
# Clone or download the project
cd SMS-Bomber

# Install dependencies
pip install -r sms_bomber/requirements.txt
```

## 📖 Usage

### Basic SMS Bombing
```bash
# Combined SMS + Call bombing
python run.py 09123456789 -c 3 -t 10 -v

# SMS only
python run.py 09123456789 -c 5 -t 15 --sms-only

# Calls only
python run.py 09123456789 -c 3 -t 10 --calls-only
```

### Arguments
| Argument | Description |
|----------|-------------|
| `target` | Target phone number (09xxxxxxxxx) |
| `-c, --count` | Number of bombing rounds (default: 1) |
| `-t, --threads` | Concurrent threads (default: 5) |
| `-v, --verbose` | Show detailed output |
| `-x, --proxy` | Proxy URL (http://host:port) |
| `--sms-only` | SMS bombing only |
| `--calls-only` | Call bombing only |

### 🔍 Provider Discovery (NEW!)

Automatically find new SMS/OTP endpoints:

```bash
# Discover endpoints (no testing)
python discover_providers.py

# Discover and test with your phone
python discover_providers.py 09123456789

# Discover, test, and add to registry
python discover_providers.py 09123456789 --add
```

### Provider Management

```bash
# Test all providers
python update_providers.py

# List providers
python manage_providers.py list -v

# Add new provider manually
python manage_providers.py add --name "MyService" --url "https://api.example.com/otp" --data "{'phone': '{phone}'}"

# Export providers
python manage_providers.py export -o backup.json
```

### Integrate Discovered Providers

```bash
# Interactive integration
python integrate_providers.py

# Auto-add all working providers
python integrate_providers.py --auto

# Set minimum confidence
python integrate_providers.py --auto --min-confidence 0.7
```

## 🔍 How Discovery Works

1. **Crawl**: Scans 30+ Iranian websites
2. **Extract**: Finds JavaScript files
3. **Analyze**: Searches for API patterns using regex
4. **Score**: Calculates confidence based on keywords
5. **Test**: Validates endpoints with test requests
6. **Export**: Generates ready-to-use provider code

### Detected Patterns
- OTP/SMS endpoints
- Login/Register APIs
- Phone verification services
- Voice call verification

## 📊 Provider Stats

| Type | Count | Description |
|------|-------|-------------|
| SMS | 40+ | SMS OTP providers |
| Call | 12+ | Voice verification providers |

## 🛡️ Tips for Better Success Rate

1. **Update providers regularly**
   ```bash
   python update_providers.py
   ```

2. **Use verbose mode to see failures**
   ```bash
   python run.py 09xxxxxxxxx -v
   ```

3. **Discover new providers**
   ```bash
   python discover_providers.py 09xxxxxxxxx --add
   ```

4. **Use more threads for speed**
   ```bash
   python run.py 09xxxxxxxxx -t 20
   ```

5. **Use proxy to avoid IP blocks**
   ```bash
   python run.py 09xxxxxxxxx --proxy http://proxy:port
   ```

## 📝 License

For educational and authorized security testing purposes only.

## ⚠️ Legal Notice

This tool is provided for **authorized security testing only**. Users are responsible for complying with applicable laws. The developers assume no liability for misuse.
