# 📱 SMS & Call Bomber 3.0

A comprehensive SMS and Call bombing tool for **security testing purposes only**.

> ⚠️ **DISCLAIMER**: This tool is intended for authorized security testing only. Only use on devices you own or have explicit permission to test. Unauthorized use may violate laws and regulations.

## 🚀 Features

- **SMS Bombing**: 87 Iranian SMS providers
- **Call Bombing**: 9 Voice OTP providers with configurable delays
- **Smart Delay System**: Prevents rate limiting with customizable delays between calls
- **Detailed Error Reporting**: See exactly why requests fail
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
# Combined SMS + Call bombing (87 SMS + 9 Call providers)
python run.py 09123456789 -c 3 -t 10 -v

# SMS only (87 providers)
python run.py 09123456789 -c 5 -t 15 --sms-only

# Calls only with 20s delay between each call
python run.py 09123456789 -c 3 --calls-only -d 20 -v

# Calls with no delay (all at once)
python run.py 09123456789 -c 3 --calls-only --no-delay
```

### Arguments
| Argument | Description |
|----------|-------------|
| `target` | Target phone number (09xxxxxxxxx) |
| `-c, --count` | Number of bombing rounds (default: 1) |
| `-t, --threads` | Concurrent threads (default: 5) |
| `-d, --delay` | Delay in seconds between calls (default: 20) |
| `-v, --verbose` | Show detailed output with error messages |
| `-x, --proxy` | Proxy URL (http://host:port) |
| `--sms-only` | SMS bombing only |
| `--calls-only` | Call bombing only |
| `--no-delay` | Send all calls at once (no delay) |

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
| SMS | 87 | SMS OTP providers |
| Call | 9 | Voice verification providers |

### SMS Providers Include:
- **E-commerce**: Digikala, DigikalaJet, SnappFood, SnappMarket, SnappExpress, Okala, Takhfifan, Digistyle, Banimode, Timcheh
- **Transport**: Snapp, Tapsi, Alibaba, Trip.ir, SnappTrip, Flightio, MrBilit, iToll
- **Messaging**: Shad, Rubika, Gap
- **Finance**: BitPin, Bit24, Bitbarg, DigiPay, Abantether, Iranicard
- **Entertainment**: Namava, GapFilm, Filmnet, Aparat, Karnaval
- **Health**: DrDr, Doctoreto, SnappDoctor, Bimito, Helsa, Pezeshket, Nobat
- **Real Estate**: Divar, Sheypoor, Kilid, Otaghak, Shab
- **Food Delivery**: Delino, Alopeyk
- **And many more...**

### Call Providers:
- Digikala Call, Alibaba Call, Namava Call, Trip.ir Call, Snapp Call
- Paklean Call, Novinbook Call, Azki Call, Ragham Call

## 🛡️ Tips for Better Success Rate

1. **Update providers regularly**
   ```bash
   python update_providers.py
   ```

2. **Use verbose mode to see failures**
   ```bash
   python run.py 09xxxxxxxxx -v
   ```

3. **Adjust call delay for better delivery**
   ```bash
   # 20 second delay between calls (default)
   python run.py 09xxxxxxxxx --calls-only -d 20
   
   # No delay (all calls at once)
   python run.py 09xxxxxxxxx --calls-only --no-delay
   ```

4. **Use more threads for speed**
   ```bash
   python run.py 09xxxxxxxxx -t 20
   ```

5. **Use proxy to avoid IP blocks**
   ```bash
   python run.py 09xxxxxxxxx --proxy http://proxy:port
   ```

6. **Discover new providers**
   ```bash
   python discover_providers.py 09xxxxxxxxx --add
   ```

## 🔄 Recent Updates (v3.0)

- Added 60+ new SMS providers from Iranian-Sms-Bomber project
- Added 4 new call providers (Paklean, Novinbook, Azki, Ragham)
- Added configurable delay between calls (`-d` / `--delay`)
- Added `--no-delay` option to send all calls at once
- Improved error reporting with HTTP status codes and response details
- Fixed phone number formatting for providers using `{phone[1:]}`
- Better verbose output showing exact failure reasons

## 📝 License

For educational and authorized security testing purposes only.

## ⚠️ Legal Notice

This tool is provided for **authorized security testing only**. Users are responsible for complying with applicable laws. The developers assume no liability for misuse.
