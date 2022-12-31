#  CryptoStoreAI (DEMO)
[![made-with-python](https://img.shields.io/badge/Made%20with-Python-1f425f.svg)](https://www.python.org/)

	

<img src = "https://github.githubassets.com/images/mona-loading-dark.gif" height=20/> VideoDownloader aim to download video from different site

## :hammer_and_wrench: Installation 

Use the package manager [pip](https://pip.pypa.io/en/stable/) to install requirements.

```bash
pip install -r requirements.txt
```
Create a `.env` file and fill out the file with your  [Binance](https://www.binance.com/en) personal key fallowing  [`.env.exemple`](https://github.com/chenak-a/CryptoStoreAI/blob/main/.env.exemple) formate



## :building_construction: Usage

```python
def run():
    #run
    run = Controller()

    #add user
    run.addUser("me",api_key=os.getenv("APIKEY"),api_secret=os.getenv("APISEC"))

    #add Cryptocurrency to your list
    run.addcoin("BTCUSDT")

    #connecte user to Cryptocurrency of the list (Activate trading on this Cryptocurrency)
    run.addcoinUser("me","BTCUSDT")

    #get balance of all activated Cryptocurrency
    run.getbalance("me")

    # update data
    run.data("BTCUSDT")
    
if __name__ == '__main__':
    run()
```
## :tada: Result

![](./img/BTCUSDT.PNG)
![](http://i.imgur.com/Ssfp7.gif)
## 🌱 Learn More
Backend  : graql server https://github.com/chenak-a/servergoQbites

frontend : react https://github.com/chenak-a/QbitesReact
## :pirate_flag: License
[MIT](https://choosealicense.com/licenses/mit/)

