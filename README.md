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
### 1 - Install package for building
*python -m pip install setuptools*
*python -m pip install build*

Current installed package in python environment

<table>
<tr><td>Package </td> <td> Version</td><td>Package </td> <td> Version</td></tr>
<tr><td>aeventkit</td> <td>2.1.0</td><td>appnope </td> <td>0.1.4</td></tr>
<tr><td>asttokens</td> <td> 3.0.0</td><td>beautifulsoup4</td> <td>4.14.2</td></tr>
<tr><td>build</td> <td>1.4.0</td><td>certifi</td> <td>2025.10.5</td></tr>
<tr><td>charset-normalizer</td> <td>3.4.4</td><td>comm</td> <td>0.2.3</td></tr>
<tr><td>debugpy</td> <td>1.8.17</td><td>decorator   </td> <td> 5.2.1</td></tr>
<tr><td>executing </td> <td>2.2.1</td><td>google      </td> <td> 3.0.0</td></tr>
<tr><td>ib_async </td> <td> 2.0.1</td><td>ibapi        </td> <td> 10.37.2</td></tr>
<tr><td>idna  </td> <td>3.11</td><td>ipykernel  </td> <td> 7.0.1</td></tr>
<tr><td>ipython </td> <td> 9.6.0</td> <td>ipython_pygments_lexers</td> <td> 1.1.1</td></tr>
<tr><td>jedi </td> <td> 0.19.2</td><td>jupyter_client   </td> <td>  8.6.3</td></tr>
<tr><td>jupyter_core  </td> <td>  5.9.1</td><td>matplotlib-inline  </td> <td>  0.2.1</td></tr>
<tr><td>nest-asyncio  </td> <td>  1.6.0</td><td>numpy    </td> <td>  2.3.4</td></tr>
<tr><td>packaging  </td> <td>  25.0</td><td>pandas   </td> <td>    2.3.3</td></tr>
<tr><td>parso </td> <td>  0.8.5</td><td>pexpect    </td> <td> 4.9.0</td></tr>
<tr><td>pip </td> <td>  25.3</td><td>platformdirs  </td> <td>   4.5.0</td></tr>
<tr><td>prompt_toolkit  </td> <td> 3.0.52</td><td>protobuf    </td> <td>     6.33.0</td></tr>
<tr><td>psutil   </td> <td>     7.1.2</td><td>ptyprocess  </td> <td>     0.7.0</td></tr>
<tr><td>pure_eval   </td> <td>   0.2.3</td><td>Pygments    </td> <td>    2.19.2</td></tr>
<tr><td>pyproject_hooks </td> <td>   1.2.0</td><td>python-dateutil  </td> <td>   2.9.0.post0</td></tr>
<tr><td>pytz   </td> <td>   2025.2</td><td>pyzmq   </td> <td>   27.1.0</td></tr>
<tr><td>requests   </td> <td> 2.32.5</td><td>schedule    </td> <td>  1.2.2</td></tr>
<tr><td>setuptools  </td> <td>    80.9.0</td><td>six  </td> <td>     1.17.0</td></tr>
<tr><td>soupsieve   </td> <td>  2.8</td><td>stack-data  </td> <td>  0.6.3</td></tr>
<tr><td>tornado     </td> <td> 6.5.2</td><td>traitlets   </td> <td>   5.14.3</td></tr>
<tr><td>typing_extensions  </td> <td>  4.15.0</td><td>tzdata    </td> <td>  2025.2</td></tr>
<tr><td>urllib3  </td> <td>  2.5.0</td><td>wcwidth  </td> <td>  0.2.14</td></tr>
<tr><td>xmltodict   </td> <td>  1.0.2</td><td></td><td></td></tr>
</table>


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

