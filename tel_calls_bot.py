from telethon import TelegramClient, events
from datetime import datetime
from send_email import SendEmailAfterTrade
from decouple import config
from web3 import Web3
import requests
import pancake
import time


bsc = "https://bsc-dataseed.binance.org/"
web3 = Web3(Web3.HTTPProvider(bsc))

api_id = config('TG_API_ID')
api_hash = config('TG_API_HASH')
client = TelegramClient('anon', api_id, api_hash)
email_pass = config('EMAIL_PASS')

keyword = 'https://poocoin.app/tokens/'#Replace for your own keyword to check in a message

tg_channels = {
    "Telegram Channel Name": 'telegram channel id here'
}

base_token_price = 0
ath_price = []
is_token_sold = False

chat_id = tg_channels["Telegram Channel Name"]
buy_amount_bnb = 0.05 #amount of bnb to buy
base_market_cap = 7000 #set market cap of projects you want to be in. Above this marketcap will terminate buying the token.
percent_down_from_ath = 0.70 #selling point from all time high if target times x's not reach in percent
times_x_up = 1.25 #times x up to activate selling point
times_x_exit = 10 #times x's up and selling point


def sell_at_specific_price(token_address, bought_price):
    global ath_price, is_token_sold, times_x_exit, times_x_up, percent_down_from_ath, email_pass
    ath_price.append(bought_price)
    print('In process checking of token price per second...')
    while True:
        time.sleep(.15)
        current_token_price = float(pancake.get_token_price_usd(token_address))

        if current_token_price > ath_price[0]:
            ath_price.append(current_token_price)

            if ath_price[0] > ath_price[1]:
                ath_price.remove(ath_price[1])
            else:
                ath_price.remove(ath_price[0])

        selling_point_price = ath_price[0] - ((ath_price[0] - bought_price) * percent_down_from_ath)

        if current_token_price > bought_price * times_x_exit:
            sold_hash = pancake.sell_token(token_address)
            print(f'Token sold at {current_token_price}')
            send_sold_mail1 = SendEmailAfterTrade(email_pass)
            send_sold_mail1.body = f'Successfully sold a token. Transaction hash : {sold_hash}'
            send_sold_mail1.send_mail_message()
            is_token_sold = True
            break

        if current_token_price < bought_price:
            sold_hash = pancake.sell_token(token_address)
            print(f'Token sold at {current_token_price}')
            send_sold_mail2 = SendEmailAfterTrade(email_pass)
            send_sold_mail2.body = f'Successfully sold a token. Transaction hash : {sold_hash}'
            send_sold_mail2.send_mail_message()
            is_token_sold = True
            break

        elif current_token_price > bought_price * times_x_up:
            if current_token_price < selling_point_price:
                sold_hash = pancake.sell_token(token_address)
                print(f'Token sold at {current_token_price}')
                send_sold_mail3 = SendEmailAfterTrade(email_pass)
                send_sold_mail3.body = f'Successfully sold a token. Transaction hash : {sold_hash}'
                send_sold_mail3.send_mail_message()
                is_token_sold = True
                break


@client.on(events.NewMessage(chats=[chat_id]))
async def my_event_handler(msg):
    global base_token_price, is_token_sold, times_x_exit, buy_amount_bnb, email_pass
    if is_token_sold is True:
        await client.disconnect()
    if keyword[:5] in msg.raw_text and msg.post is True:
        text_words = msg.raw_text.split()
        for words in text_words:
            if keyword[:5] in words:
                url_resp = requests.get(words).url
                if keyword in url_resp and pancake.get_bnb_balance() > buy_amount_bnb:

                    token_address = str(url_resp[len(keyword):])
                    print(f'token address: {url_resp[len(keyword):]}')

                    token_price_usd = float(pancake.get_token_price_usd(token_address))

                    market_cap = pancake.get_circulating_supply(token_address) * token_price_usd
                    print(f'Token Marketcap : {market_cap}')

                    print(f'Token Price in USD : {token_price_usd}')
                    print(f'Time in UTC : {datetime.utcnow()}')

                    buy_hash = ''
                    tx_used_fee = 0
                    tx_buy_result = 0
                    base_nonce = pancake.get_nonce()
                    successfully_bought_a_token = False
                    print('In process buying a token...')

                    while True:
                        if pancake.get_bnb_balance() > buy_amount_bnb and market_cap < base_market_cap:
                            if pancake.is_blacklisted(token_address) is True:
                                print('You are blacklisted!')
                                break
                            if pancake.get_nonce() == base_nonce:

                                buy_hash = pancake.buy_token(token_address, buy_amount_bnb)

                                token_price_usd = float(pancake.get_token_price_usd(token_address))
                                print(f'Bought price : {token_price_usd}')
                                base_token_price = token_price_usd

                                market_cap = pancake.get_circulating_supply(token_address) * token_price_usd
                                print(f'Bought Marketcap : {market_cap}')

                                time.sleep(8)
                                base_nonce += 1
                                (gas_buy_fee, tx_buy_result) = pancake.get_tx_reciept(buy_hash[27:])
                                tx_used_fee += gas_buy_fee
                                successfully_bought_a_token = True
                            if tx_buy_result == 1:
                                print(f'tx_result : {tx_buy_result}')
                                successfully_bought_a_token = True
                                break
                            else:
                                print(f'tx used fee : {tx_used_fee}')
                                if tx_used_fee > .0015:
                                    successfully_bought_a_token = False
                                    print('Buy limit executed. Transaction keeps on failing.')
                                    break
                        else:
                            break

                    if successfully_bought_a_token is True:
                        print('Successfully bought a token!')

                        send_buy_mail = SendEmailAfterTrade(email_pass)
                        send_buy_mail.body = f'Successfully bought a token. \n'\
                            f'Transaction hash : {buy_hash}\n' \
                            f'Token address: {token_address}\n'
                        send_buy_mail.send_mail_message()

                        sell_price = base_token_price * times_x_exit
                        print(f'Selling price : {sell_price}')

                        sell_at_specific_price(token_address, base_token_price)
                    else:
                        print('Failed! Did not met one of your specifications in buying a token.')
                        break
    else:
        print('Token address not found in the message.')

client.start()
client.run_until_disconnected()

