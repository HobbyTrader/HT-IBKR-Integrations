# HT-IBKR-Integrations  
Automated trading app using INteractive brokers TWS API.

---
## Run Unit Tests commands
### Run single unit test file
*python -m unitttest tests.dto.test_strategy_dto -v*

### Run all unit tests for dto
*python -m unittest discover tests/dto -v*

### Run all unit tests under tests folder and sub folders
*python -m unittest discover tests -v*

---
## Compile project to make package for installation
### 1 - Install build package
*python -m pip install build*
### 2 - Run build command
*python -m build*
packages are created in dist/ folder
package name and version are taken from information present into pyproject.toml file

> [project]
name = "ht-ibkr-integrations"
version = "0.2.0"

---
## Install package
*python -m pip install dist/ht_ibkr_integrations-0.2.0-py3-none-any.whl*
or
*python -m pip install ht_ibkr_integrations-0.2.0.tar.gz*

