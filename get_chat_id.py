#MADE JUST TO GET CHAT ID AND SO THIS IS NOT CONNECTED IN THE MAIN PYTHON FILE
from telethon import TelegramClient
from decouple import config

api_id = config('TG_API_ID')
api_hash = config('TG_API_HASH')
client = TelegramClient('anon', api_id, api_hash)

client.start()

for chats in client.iter_dialogs():
    print(chats.name, chats.id)
