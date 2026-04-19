# HT-IBKR-Integrations

Basic Code Structures for interaction with Interactive Brokers TWS (Trader Work Station) or IB_Gateway to connect, get account information, portfolio data, stock prices, historical data, screeners and placing trades (buy and sell orders)

## Installation (Windows)

Download an install this repo

```bash
git clone https://github.com/HobbyTrader/HT-IBKR-Integrations.git
cd HT-IBKR-Integrations
py -m venv env
env\scripts\activate
py -m pip install -U pip
pip install -r requirements.txt

```

## Interactive Broker's API

The python application will use a special package called [ib_async](https://github.com/ib-api-reloaded/ib_async) to connect to the interactive broker's API. The APIs are exposed through a local desktop application called Trader Workstation (TWS) that run on a JAVA.

Get the latest version of [Trader's Workstation](https://www.interactivebrokers.com/en/trading/tws.php) API Access. You will need to create and fund an account to use the API for Paper Trading.  

Interactive Broker'S TWS API [official documentation](https://www.interactivebrokers.com/campus/ibkr-api-page/twsapi-doc/#requests-limitations).
***We are using ib_async NOT IBKR's python package, but it is usefull to read through the available features***  

## Configuration  

See the [ib_async github repo](https://github.com/ib-api-reloaded/ib_async) to view a detailed installation and configuration process and [ib_async documentation](https://ib-api-reloaded.github.io/ib_async/).

But in simple terms you must go to files-> Global Confgiuration -> API -> Settings and check the following parameters:
![alt text](img/twsconfig.png)

## Running the samples

The Traderworkstation must be running for the samples to work (it can be in live trading or paper trading)
> **WARNING**  
> Samples will place trades so make sure you use PAPER TRADING while testing and developping
>
> **NOTES**
> With a funded account some Market Data Subscriptions will be offered free of monthly fees. But real time price data will only be available in the live trading account. Paper Trading account will return 15 minute delayed prices.

| Sample | Description | Result |
| --- | --- | --- |
| 01_connect.py | This script connects to the API. It waits until ENTER is pressed, and simply disconnects.<br><br>This acts a simple configurataion test.| Connected to Trader Work Station or ib_gateway. |
| 02_managed_accounts.py | This script will connect to the API and retrieve your managed accounts.<br><br>The terminal console should display your existing bying power (example for a single account in IBKR)| Account: AA99999999 |
| 03_account_summary.py | This script will connect to the API and retrieve your account details.<br><br>The terminal console should display your existing bying power. | <img src="img\run_02b.png" width="350"> |
| 04_historical_prices_1day.py | This script will connect to the API and retrieve 1 day of historical minute price data, convert it to a PANDAS dataframe, display the last 5 minutes and save to a CSV file in the DATA folder | <img src="img\run_04a.png" width="350"><br><br><img src="img\run_04b.png" width="350"> |
| 05_historical_prices_1year.py | A simple script that loops through 1 full year by 5 day decrements to get minute price data for an entire year. | Print of the week being extracted, saved prices in the DATA folder with only the ticker symbol as filename|

## References  

Learning is a long path and great people offer their help through excellent videos.  
Please visite them for more information

***ib_async and Trader Work Station Explanantions***

| Teacher | Link |
| --- | --- |
| Part-Time-Larry | [Interactive Brokers API with Python and ib_async](https://www.youtube.com/watch?v=EYDLlnmM5x8&t=1s) |
| Part-Time-Larry | [Open Range Breakout Strategy in Python with IBKR API and ib_async](https://www.youtube.com/watch?v=a1813iCcsWQ&t=32s) |
| Part-Time-Larry | [Real-Time Market Scanners Example](https://www.youtube.com/watch?v=S9vxHNv_b8E&t=714s) |

---  

## Run Unit Tests commands

### Run single unit test file

```bash
python -m unitttest tests.dto.test_strategy_dto -v
```

### Run all unit tests for dto

```bash
python -m unittest discover tests/dto -v
```

### Run all unit tests under tests folder and sub folders

```bash
python -m unittest discover tests -v
```

---

---

## Building and Installing the Package

This section explains how to build the `ht-ibkr-integrations` package and install it on Windows and macOS.

### Platform Compatibility

The application is **fully cross-platform** and works on:
- **Windows** (Windows 10+)
- **macOS** (macOS 10.13+)
- **Linux** (Ubuntu 20.04+)

All dependencies (`pandas`, `protobuf`, `schedule`, `ibapi`) are platform-independent and work seamlessly on all supported platforms.

### Prerequisites

Before building the package, ensure you have:

1. **Python 3.12 or higher** installed
   - [Download Python for Windows](https://www.python.org/downloads/)
   - [Download Python for macOS](https://www.python.org/downloads/)

2. **Build tools installed:**
   ```bash
   python -m pip install --upgrade pip
   python -m pip install setuptools wheel build
   ```

### Building the Package

The package is built using Python's standard `build` tool, which creates both a wheel (`.whl`) and source distribution (`.tar.gz`).

#### Step 1: Clone or Navigate to Repository

```bash
# If cloning for the first time:
git clone https://github.com/HobbyTrader/HT-IBKR-Integrations.git
cd HT-IBKR-Integrations
```

#### Step 2: Create Virtual Environment (Recommended)

**Windows:**
```bash
py -m venv venv
venv\Scripts\activate
```

**macOS/Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

#### Step 3: Install Build Dependencies

```bash
python -m pip install --upgrade pip
python -m pip install setuptools wheel build
```

#### Step 4: Build the Package

```bash
python -m build
```

This command creates two distribution files in the `dist/` folder:
- `ht_ibkr_integrations-0.2.0-py3-none-any.whl` (wheel - recommended)
- `ht_ibkr_integrations-0.2.0.tar.gz` (source distribution)

The `py3-none-any` wheel indicates the package is compatible with **any platform** running Python 3.

### Installing the Package

#### Installation on Windows

**Option 1: Install from wheel (Recommended)**

```bash
# Using Command Prompt or PowerShell
py -m pip install dist\ht_ibkr_integrations-0.2.0-py3-none-any.whl
```

**Option 2: Install from source distribution**

```bash
py -m pip install dist/ht_ibkr_integrations-0.2.0.tar.gz
```

**Option 3: Install in development mode** (editable, for development)

```bash
py -m pip install -e .
```

#### Installation on macOS

**Option 1: Install from wheel (Recommended)**

```bash
python -m pip install dist/ht_ibkr_integrations-0.2.0-py3-none-any.whl
```

**Option 2: Install from source distribution**

```bash
python -m pip install dist/ht_ibkr_integrations-0.2.0.tar.gz
```

**Option 3: Install in development mode** (editable, for development)

```bash
python -m pip install -e .
```

### Verifying Installation

After installation, verify that the package and its command-line tools are available:

```bash
# Check package installation
pip show ht-ibkr-integrations
```

You should see:
```
Name: ht-ibkr-integrations
Version: 0.2.0
Location: /path/to/site-packages
Requires: pandas, protobuf, schedule, ibapi
```

### Accessing Command-Line Tools

The package provides several command-line entry points. After installation, you can use:

```bash
# Market scanner
scan

# Load strategy from JSON file
loadstrategy

# Initialize database
init-db

# Close all open positions
close-positions
```

### Post-Installation Setup

#### Initialize Database

After the first installation, initialize the database:

```bash
# Windows
init-db

# macOS/Linux
init-db
```

#### Configure Trader Workstation (TWS)

Before running the application:

1. Download and install [Trader Workstation](https://www.interactivebrokers.com/en/trading/tws.php)
2. Navigate to **Global Configuration** → **API** → **Settings**
3. Enable the following:
   - ✓ Enable ActiveX and Socket Clients
   - ✓ Read-Only API

See the [ib_async documentation](https://ib-api-reloaded.github.io/ib_async/) for detailed configuration.

### Uninstalling the Package

To uninstall the package:

**Windows:**
```bash
py -m pip uninstall ht-ibkr-integrations
```

**macOS/Linux:**
```bash
python -m pip uninstall ht-ibkr-integrations
```

### Troubleshooting

**Issue: Build fails with `ValueError: No distribution was found`**
- Solution: Ensure `setup.py` contains a `setup()` call. Run: `python setup.py --version`

**Issue: `ibapi` import fails**
- Solution: Install the latest IBAPI from [Interactive Brokers](https://interactivebrokers.github.io/#)
  ```bash
  pip install ibapi>=10.37
  ```

**Issue: Permission denied during installation**
- Solution: Use `--user` flag or install in a virtual environment:
  ```bash
  python -m pip install --user dist/ht_ibkr_integrations-0.2.0-py3-none-any.whl
  ```

**Issue: `ModuleNotFoundError` after installation**
- Solution: Ensure all dependencies are installed:
  ```bash
  pip install pandas protobuf schedule ibapi
  ```

---

# Strategie Definition

