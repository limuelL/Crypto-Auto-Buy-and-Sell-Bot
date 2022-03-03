from telethon.tl.types import ChannelParticipantsAdmins
from telethon import TelegramClient, events
import pancake
import time
from decouple import config
from send_email import SendEmailAfterTrade
from web3 import Web3

chat = ''
buy_amount_bnb = 0.01 #amount of bnb to buy
times_x_exit = 5 #times x's up and selling point
times_x_up = 1.25 #times x up to activate selling point
percent_down_from_ath = 0.70 #selling point from all time high if target times x's not reach in percent

bsc = "https://bsc-dataseed.binance.org/"
web3 = Web3(Web3.HTTPProvider(bsc))
api_id = config('TG_API_ID')
api_hash = config('TG_API_HASH')

client = TelegramClient('anon', api_id, api_hash)
email_pass = config('EMAIL_PASS')
pancake_url = "https://api.pancakeswap.info/api/v2/tokens/"
keywords = ['https://pancakeswap.finance/swap?outputCurrency=', 'https://poocoin.app/tokens/', '0x']#keywords to check in a message

converter = {
        "one": "1",
        "two": "2",
        "three": "3",
        "four": "4",
        "five": "5",
        "six": "6",
        "seven": "7",
        "eight": "8",
        "nine": "9",
        "zero": "0",
        "first": '',
        "second": '',
        "third": '',
        "fourth": ''
        }

tg_channels = {
    "Telegram Channel Name": 'telegram channel id here'
}

tg_name = tg_channels["Telegram Channel Name"]
is_token_sold = False
contract_address = ''
base_token_price = 0
group_admins = []
ath_price = []
chat_id = 0


async def get_chat_username(channel):
    async for chats in client.iter_dialogs():
        channel_id = str(abs(channel))[3:]
        try:
            if channel_id == str(chats.message.peer_id.channel_id):
                if chats.entity.username is None:
                    return chats.name
                else:
                    return chats.entity.username
        except AttributeError:
            pass


async def get_admin_id():
    chat_param1 = await get_chat_username(tg_name)
    async for user in client.iter_participants(chat_param1, filter=ChannelParticipantsAdmins):
        group_admins.append(user.id)


def fix_modified_address(message_with_ca):
    fixed_address = ''

    for combinations in message_with_ca:
        fixed_address += converter.get(combinations.lower(), combinations) + ' '
    return fixed_address


def check_string(words):
    has_letter = False
    has_number = False

    for x in words:
        if x.isalpha():
            has_letter = True
        if x.isdigit():
            has_number = True
    return has_letter, has_number


def validate_address(raw_address):
    address_length = len(raw_address)
    if address_length == 42:
        return_address = raw_address
    else:
        find_x_loc = raw_address.find('x')
        if find_x_loc == 0:
            return_address = raw_address[:42]
        else:
            return_address = raw_address[find_x_loc - 1:]
            if len(return_address) != 42:
                return_address = return_address[:42]
    return return_address


def sell_at_specific_price(token_address, bought_price):
    global ath_price, is_token_sold, times_x_exit, email_pass
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

        selling_point_decrease = (ath_price[0] - bought_price) * percent_down_from_ath
        selling_point_price = ath_price[0] - selling_point_decrease

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


@client.on(events.NewMessage(chats=[tg_name]))
async def event_handler(msg):
    global base_token_price, is_token_sold, contract_address, buy_amount_bnb, chat, email_pass
    if is_token_sold is True:
        await client.disconnect()
    chat = await get_chat_username(tg_name)
    print(chat)
    try:
        async for text in client.iter_messages(chat, 1):
            message_sender_id = await client.get_entity(msg.from_id)
            await get_admin_id()
            for each_admin_id in group_admins:
                if message_sender_id.id == each_admin_id:
                    admin_message = f'{text.message}'.replace('(', '').replace(')', '').split()
                    admin_message = fix_modified_address(admin_message).split()
                    group_admins.clear()
                    raw_address = ''
                    for combinations in admin_message:
                        (with_letter, with_number) = check_string(combinations)
                        if with_letter is True and with_number is True or with_number is True:
                            raw_address += combinations

                    if keywords[0] in raw_address:
                        contract_address = raw_address[len(keywords[0]):]
                        contract_address = validate_address(contract_address)
                        print(f'Sender Name : {message_sender_id.first_name} {message_sender_id.last_name}\n'
                              f'Username : {message_sender_id.username}\n'
                              f'Token Address: {contract_address}')
                    elif keywords[1] in raw_address:
                        contract_address = raw_address[len(keywords[1]):]
                        contract_address = validate_address(contract_address)
                        print(f'Sender Name : {message_sender_id.first_name} {message_sender_id.last_name}\n'
                              f'Username: {message_sender_id.username}\n'
                              f'Token Address: {contract_address}')
                    elif keywords[2] in raw_address:
                        contract_address = validate_address(raw_address)
                        print(f'Sender Name : {message_sender_id.first_name} {message_sender_id.last_name}\n'
                              f'Username: {message_sender_id.username}\n'
                              f'Token Address: {contract_address}')

                    buy_hash = ''
                    tx_used_fee = 0
                    tx_buy_result = 0
                    base_nonce = pancake.get_nonce()
                    successfully_bought_a_token = False
                    print('In process buying a token...')

                    while True:
                        if pancake.get_bnb_balance() > buy_amount_bnb and contract_address != '':
                            if pancake.is_blacklisted(contract_address) is True:
                                print('You are blacklisted!')
                                break
                            if pancake.get_nonce() == base_nonce:
                                try:
                                    buy_hash = pancake.buy_token(contract_address, buy_amount_bnb)

                                    token_price_usd = float(pancake.get_token_price_usd(contract_address))
                                    print(f'Bought price : {token_price_usd}')
                                    base_token_price = token_price_usd

                                    market_cap = pancake.get_circulating_supply(contract_address) * token_price_usd
                                    print(f'Bought Marketcap : {market_cap}')

                                    time.sleep(8)
                                    base_nonce += 1
                                    (gas_buy_fee, tx_buy_result) = pancake.get_tx_reciept(buy_hash[27:])
                                    tx_used_fee += gas_buy_fee
                                    successfully_bought_a_token = True
                                except KeyError:
                                    print('Waiting for liquidity...')

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
                            f'Token address: {contract_address}\n'
                        send_buy_mail.send_mail_message()

                        sell_price = base_token_price * times_x_exit
                        print(f'Selling price : {sell_price}')

                        sell_at_specific_price(contract_address, base_token_price)
                    elif contract_address == '':
                        print('Contract address not found in the message!')
                    else:
                        print("Failed. You don't have enough balance to buy this token.")
                        break

    except TypeError:
        print('Type Error encountered!')
    except ValueError:
        print('Value error encountered')


client.start()
client.run_until_disconnected()