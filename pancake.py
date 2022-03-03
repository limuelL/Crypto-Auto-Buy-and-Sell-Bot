from web3 import Web3
import time
from web3.exceptions import ABIFunctionNotFound
from decouple import config
import requests


pancake_url = "https://api.pancakeswap.info/api/v2/tokens/"
bsc = "https://bsc-dataseed.binance.org/"
web3 = Web3(Web3.HTTPProvider(bsc))
bsc_api_key = config('BSC_API_KEY')
private_key = config('PRIVATE_KEY')

pancake_abi = open('pancake_abi', 'r').read()
contract_abi = open('contract_abi', 'r').read()

router_address = web3.toChecksumAddress("0x10ED43C718714eb63d5aA57B78B54704E256024E")#pancakeswap router address
sender_address = web3.toChecksumAddress("Your BEP20 wallet address")
base_address = web3.toChecksumAddress("0xbb4cdb9cbd36b01bd1cbaebf2de08d9173bc095c")#wbnb address

contract = web3.eth.contract(address=router_address, abi=pancake_abi)

token_balance_readable = 0


def get_nonce():
    return web3.eth.getTransactionCount(sender_address)


def get_tx_reciept(tx_hash):
    gwei_per_bnb = 1000000000
    gas_price = 5.5 / gwei_per_bnb

    tx_reciept = web3.eth.wait_for_transaction_receipt(tx_hash)
    tx_status = tx_reciept.status
    gas_fee = gas_price * tx_reciept.gasUsed
    return gas_fee, tx_status


def get_bnb_balance():
    address_balance = web3.eth.getBalance(sender_address)
    readable_balance = web3.fromWei(address_balance, 'ether')
    return readable_balance


def is_blacklisted(contract_address):
    raw_contract_abi = requests.get("https://api.bscscan.com/api"
                                    "?module=contract"
                                    "&action=getabi"
                                    f"&address={contract_address}"
                                    f"&apikey={bsc_api_key}")
    try:
        token_abi = raw_contract_abi.json()['result']
        token_address = web3.toChecksumAddress(contract_address)
        token_contract = web3.eth.contract(address=token_address, abi=token_abi)
        return token_contract.functions.isBlacklisted(sender_address).call()
    except ABIFunctionNotFound:
        return False
    except ValueError:
        return False


def get_token_price_usd(token_address):
    token_address = web3.toChecksumAddress(token_address)
    token_contract = web3.eth.contract(address=token_address, abi=contract_abi)
    one_token = 10**int(token_contract.functions.decimals().call())
    bnb_per_token = contract.functions.getAmountsOut(one_token, [token_address, base_address]).call()
    bnb_per_token_converted = float(web3.fromWei(bnb_per_token[1], 'ether'))

    token_data = requests.get(url=pancake_url + base_address)
    json_raw = token_data.json()
    bnb_price_in_usd = float(json_raw['data']['price'])
    return bnb_per_token_converted * bnb_price_in_usd


def get_circulating_supply(contract_add):
    global bsc_api_key
    contract_id = web3.toChecksumAddress(contract_add)

    circulating_supply_response = requests.get("https://api.bscscan.com/api""?module=stats"
                                               "&action=tokenCsupply"
                                               f"&contractaddress={contract_add}"
                                               f"&apikey={bsc_api_key}")

    sdr_result = circulating_supply_response.json()['result']

    token = web3.eth.contract(address=contract_id, abi=contract_abi)
    token_decimal = token.functions.decimals().call()

    circulating_supply = int(sdr_result[:-token_decimal])
    return circulating_supply


def buy_token(token_address, base_bnb_amount):
    global private_key

    print(f'Current Account Balance (BNB) : {get_bnb_balance()}')

    contract_address = web3.toChecksumAddress(token_address)

    start = time.time()

    pancakeswap_buy_txn = contract.functions.swapExactETHForTokensSupportingFeeOnTransferTokens(
        0,
        [base_address, contract_address],
        sender_address,
        (int(time.time()) + 1000000)
    ).buildTransaction({
        'from': sender_address,
        'value': web3.toWei(base_bnb_amount, 'ether'),
        'gas': 300000,
        'gasPrice': web3.toWei('5.5', 'gwei'),
        'nonce': web3.eth.getTransactionCount(sender_address),
    })

    signed_txn = web3.eth.account.sign_transaction(pancakeswap_buy_txn, private_key=private_key)
    tx_token = web3.eth.send_raw_transaction(signed_txn.rawTransaction)
    buy_hash = f'https://www.bscscan.com/tx/{web3.toHex(tx_token)}'
    print("Transaction Hash : " + buy_hash)
    return buy_hash


def sell_token(token_address):
    global token_balance_readable, private_key
    sold_hash = ''
    tx_used_fee = 0
    tx_sell_result = 0

    contract_address = web3.toChecksumAddress(token_address)

    token = web3.eth.contract(address=contract_address, abi=contract_abi)
    token_balance = token.functions.balanceOf(sender_address).call()
    token_balance_readable = web3.fromWei(token_balance, 'ether')

    print(f'Token Balance : {token_balance_readable}')

    sell_contract = web3.eth.contract(address=contract_address, abi=contract_abi)

    start = time.time()

    approve = sell_contract.functions.approve(router_address, token_balance).buildTransaction({
        'from': sender_address,
        'gasPrice': web3.toWei('5', 'gwei'),
        'nonce': web3.eth.getTransactionCount(sender_address),
    })

    signed_txn = web3.eth.account.sign_transaction(approve, private_key=private_key)
    tx_token = web3.eth.send_raw_transaction(signed_txn.rawTransaction)
    print(f"APPROVED! Transaction Hash : https://www.bscscan.com/tx/{web3.toHex(tx_token)}")

    time.sleep(10)
    pbase_nonce = get_nonce()

    while True:
        if token_balance_readable > 0:
            if get_nonce() == pbase_nonce:
                pancakeswap_sell_txn = contract.functions.swapExactTokensForETHSupportingFeeOnTransferTokens(
                    token_balance, 0,
                    [contract_address, base_address],
                    sender_address,
                    (int(time.time()) + 1000000)
                ).buildTransaction({
                    'from': sender_address,
                    'gasPrice': web3.toWei('5.5', 'gwei'),
                    'nonce': web3.eth.getTransactionCount(sender_address),
                })

                signed_txn = web3.eth.account.sign_transaction(pancakeswap_sell_txn, private_key=private_key)
                tx_token = web3.eth.send_raw_transaction(signed_txn.rawTransaction)
                sold_hash = f'https://www.bscscan.com/tx/{web3.toHex(tx_token)}'

                token = web3.eth.contract(address=contract_address, abi=contract_abi)
                token_balance = token.functions.balanceOf(sender_address).call()
                token_balance_readable = web3.fromWei(token_balance, 'ether')

                time.sleep(8)
                pbase_nonce += 1
                (gas_sell_fee, tx_sell_result) = get_tx_reciept(sold_hash[27:])
                tx_used_fee += gas_sell_fee
            if tx_sell_result == 1:
                break
            else:
                if tx_used_fee > .003:
                    print('Sell limit executed. Transaction keeps on failing.')
                    break
        else:
            break

    print("SOLD! Transaction Hash : " + sold_hash)
    return sold_hash
