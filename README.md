# Hobby Trader's HT-IBKR-Integrations  
This project offers tools for algorithmic trading using Interactive Broker's Trader Workstation (TWS) and the accompanying TWS API.  

Before installing this package, two external tools are required:  
- IBKR [Trader Workstation](https://www.interactivebrokers.com/en/trading/tws-updatable-latest.php) (TWS)
- IBKR [TWS API](https://www.interactivebrokers.com/campus/ibkr-api-page/twsapi-doc/#invalid-format-disconnect) package  

For installation to work properly using our pyproject.toml setup file, the python client api package must be installed in "C:\TWS API\source\pythonclient" where a setup.py will be readable.

## Installation (Windows)
If you downloaded the TWS API and installed it in the default location ```C:\TWS API``` the installation process should work properly.  
  
Open a terminal like PowerShell and run the following commands:  
```
git clone https://github.com/HobbyTrader/HT-IBKR-Integrations.git
cd HT-IBKR-Integrations
py -m venv env
env\Scripts\activate
py -m pip install -U pip
pip install -e .[dev]

```
> This will create a virtual environment in your project root folder, update pip, and install dependencies to run and modify the package  

# Test installation
To test if the ht_tools package was installed properly, check if the __version__ attribute exists on import.  
From the terminal run:  
```
pytest ht_tools\tests -v -x -s -k test_version_attribute_exists
``` 
You should see a response ending with a message similar to:  
``` 
ht_tools/tests/test_core/test_setup.py::TestSetup::test_version_attribute_exists PASSED  
====================== 1 passed, x deselected in 0.05s ================================
``` 

# References  
- Official [TWS AI Documentation](https://www.interactivebrokers.com/campus/ibkr-api-page/twsapi-doc/#api-introduction)  
