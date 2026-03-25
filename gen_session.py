import asyncio
from pyrogram import Client

async def main():
    api_id = int(input("Enter API_ID: "))
    api_hash = input("Enter API_HASH: ")
    async with Client("my_account", api_id=api_id, api_hash=api_hash) as app:
        print(await app.export_session_string())

if __name__ == "__main__":
    asyncio.run(main())
