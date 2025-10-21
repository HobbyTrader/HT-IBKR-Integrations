# HT-IBKR-Integrations
Basic Code Structures for interaction with Interactive Brokers TWS (Trader Work Station) or IB_Gateway to connect, get account information, portfolio data, stock prices, historical data, screeners and placing trades (buy and sell orders)

# Installation (Windows)
Download an install this repo
```
git clone https://github.com/HobbyTrader/HT-IBKR-Integrations.git
cd HT-IBKR-Integrations
py -m venv env
env\scripts\activate
py -m pip install -U pip
pip install -r requirements.txt

```

# Interactive Broker's API
The python application will use a special package called [ib_async](https://github.com/ib-api-reloaded/ib_async) to connect to the interactive broker's API. The APIs are exposed through a local desktop application called Trader Workstation (TWS) that run on a JAVA. 

Get the latest version of [Trader's Workstation](https://www.interactivebrokers.com/en/trading/tws.php) API Access. You will need to create and fund an account to use the API for Paper Trading.  

Interactive Broker'S TWS API [official documentation](https://www.interactivebrokers.com/campus/ibkr-api-page/twsapi-doc/#requests-limitations).   
***We are using ib_async NOT IBKR's python package, but it is usefull to read through the available features***  


# Configuration  
See the [ib_async github repo](https://github.com/ib-api-reloaded/ib_async) to view a detailed installation and configuration process and [ib_async documentation](https://ib-api-reloaded.github.io/ib_async/).

But in simple terms you must go to files-> Global Confgiuration -> API -> Settings and check the following parameters:
![alt text](img/twsconfig.png)

# Running the samples
The Traderworkstation must be running for the samples to work (it can be in live trading or paper trading)   
> WARNING  
> Samples will place trades so make sure you use PAPER TRADING while testing and developping

> NOTES  
> With a funded account some Market Data Subscriptions will be offered free of monthly fees. But real time price data will only be available in the live trading account. Paper Trading account will return 15 minute delayed prices.

| Sample | Description | Result |
|---|---|---|
| 01_connect.py | This script connects to the API. It waits until ENTER is pressed, and simply disconnects.<br><br>This acts a simple configurataion test.| Connected to Trader Work Station or ib_gateway. |
| 02_managed_accounts.py | This script will connect to the API and retrieve your managed accounts.<br><br>The terminal console should display your existing bying power (example for a single account in IBKR)| Account: AA99999999 |
| 03_account_summary.py | This script will connect to the API and retrieve your account details.<br><br>The terminal console should display your existing bying power. | <img src="img\run_02b.png" width="350"> |
| 04_historical_prices_1day.py | This script will connect to the API and retrieve 1 day of historical minute price data, convert it to a PANDAS dataframe, display the last 5 minutes and save to a CSV file in the DATA folder | <img src="img\run_04a.png" width="350"><br><br><img src="img\run_04b.png" width="350"> |
| 05_historical_prices_1year.py | A simple script that loops through 1 full year by 5 day decrements to get minute price data for an entire year. | Print of the week being extracted, saved prices in the DATA folder with only the ticker symbol as filename|
|  |  |  |
|  |  |  |
|  |  |  |


# References  
Learning is a long path and great people offer their help through excellent videos.  Pelase visite them for more information
---
***ib_async and Trader Work Station Explanantions***
| Teacher | Link |
|---|---|
|Part-Time-Larry | [Interactive Brokers API with Python and ib_async](https://www.youtube.com/watch?v=EYDLlnmM5x8&t=1s) |
|Part-Time-Larry | [Open Range Breakout Strategy in Python with IBKR API and ib_async](https://www.youtube.com/watch?v=a1813iCcsWQ&t=32s) |
|Part-Time-Larry | [Real-Time Market Scanners Example](https://www.youtube.com/watch?v=S9vxHNv_b8E&t=714s) |

---  
