# Crypto-Auto-Invest-And-Sell-Bot
Auto invest and sell bot for newly launched projects in the **Binance Smart Chain (BSC) platform listed in pancakeswap exchange**.<br/>

And are providing relevant project informations in the **Telegram App**, including the token address, which we really need to execute a transaction.<br/>

Specially made for playing with **low marketcap shitcoins or memecoins** which we can assume most of the time as **"pump and dump"**.<br/>

## How does it work
### There are two main scripts here.<br/>
 - First is `tel_calls_bot.py`, which monitors a specific Telegram Channel for new coins or tokens being called by influencers and then invest them *(becoming an early investor)*.<br/>
 - Second is `snipe_bot.py`, which monitors a specific Telegram Group Chat and look and wait for contract/token address to be posted by admins/mods in the chat and then invest in them as well *(So you can become one of the first investors)*. This also wait for the contract address to acquire liquidity and will not return an error or worst stop the program if liquidity has not yet been added.<br/><br/>

### Features
- You can set for specific x's or percent income where you want to exit.<br/>
- You can set for a selling point from ATH (either 25%, 50%, or 75%) if ever your target x is not reached. To also avoid loss of capital.<br/>
- Fixes contract addresses modified by telegram chat admins/mods.<br/>
- Ability to check transaction receipt status and a fix in case it failed.<br/>
- Ability to detect blacklisting function in a contract.<br/>
- Allows you to select the project market cap in which you want to make an investment. (only for `tel_calls_bot.py`). <br/><br/>

This also has the functionality of sending you an email including the transaction hash and token address whenever the bot invested or sold a coin or token.<br/>
**Note**: *in order for the email to work, you need to turn ON "less secure" feature in the email settings of your sender email address, so it is advisable to create a temporary email for this. But you still have the choice if you don't want to use this feature.*<br/>

## Script Status
`tel_calls_bot.py` was successfully tested and is actively running on the Heroku Cloud Platform.<br/>
`snipe_bot.py` was successfully tested locally, but not yet on an actual live project. <br/>

## Run Script in Heroku
[Heroku Documentation](https://devcenter.heroku.com/articles/getting-started-with-python/ "Heroku Documentation") to deploy python script in their platform.<br/>

## Todo 
> - [ ] Add a GUI for better access.<br/>
> - [ ] Check for other possible bugs.
