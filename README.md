# 📱 SMS & Call Bomber 3.0

A comprehensive SMS and Call bombing tool for **security testing purposes only**.

> ⚠️ **DISCLAIMER**: This tool is intended for authorized security testing only. Only use on devices you own or have explicit permission to test. Unauthorized use may violate laws and regulations.

## 🚀 Features

- **SMS Bombing**: 87 Iranian SMS providers
- **Call Bombing**: 9 Voice OTP providers with configurable delays
- **Modern GUI**: Beautiful CustomTkinter interface
- **Smart Delay System**: Prevents rate limiting with customizable delays between calls
- **Detailed Error Reporting**: See exactly why requests fail
- **Proxy Support**: Rotate proxies to avoid blocks
- **Rich UI**: Beautiful terminal interface with progress bars

## 📁 Project Structure

```
SMS-Bomber/
├── run.py                      # CLI entry point
├── gui.py                      # 🆕 Modern GUI (CustomTkinter)
├── setup.py                    # Setup script
│
├── sms_bomber/
│   ├── main.py                 # Main bombing logic
│   ├── api/
│   │   ├── providers.pyc       # 🔒 SMS providers (compiled)
│   │   ├── call_providers.pyc  # 🔒 Call providers (compiled)
│   │   ├── client.py           # SMS API client
│   │   ├── call_client.py      # Call API client
│   │   ├── _loader.py          # Bytecode loader
│   │   └── provider_updater.py # Provider health checker
│   ├── core/
│   │   ├── config.py           # Configuration
│   │   └── logger.py           # Logging
│   └── ui/
│       ├── console.py          # Terminal UI
│       └── progress.py         # Progress tracking
│
├── tools/                      # Utility scripts
├── data/                       # Data directory
└── logs/                       # Log files
```

## 🔧 Installation

```bash
# Clone or download the project
cd SMS-Bomber

# Install dependencies
pip install -r sms_bomber/requirements.txt

# Or install with pip
pip install aiohttp rich customtkinter
```

## 📖 Usage

### 🖥️ GUI Mode (Recommended)

```bash
# Launch the modern GUI
python gui.py
```

**GUI Features:**
- 📱 Enter target phone number
- 🔄 Set rounds, threads, and delay
- 📨 Choose mode: SMS only, Calls only, or Both
- 📊 Real-time progress tracking
- 📋 Activity log with color-coded output
- 🛠️ Tools: Test providers, export logs, quick test

### ⌨️ CLI Mode

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

##  Provider Stats

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

1. **Use the GUI for easier operation**
   ```bash
   python gui.py
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

### GUI Interface
- Modern dark theme with purple accents
- Two-column layout with cards
- Real-time progress bar
- Success/Failure counters
- Color-coded activity log

## 🔄 Version History

### v3.0 (Current)
- ✨ New modern GUI with CustomTkinter
- 🔒 Compiled provider files for security
- 📱 87 SMS providers + 9 Call providers
- ⚡ Improved performance with async requests
- 🎨 Beautiful dark theme interface

### v2.0
- Added call bombing feature
- Configurable delays between calls
- Improved error reporting

### v1.0
- Initial release
- SMS bombing only

## 📝 License

For educational and authorized security testing purposes only.

## ⚠️ Legal Notice

This tool is provided for **authorized security testing only**. Users are responsible for complying with applicable laws. The developers assume no liability for misuse.
