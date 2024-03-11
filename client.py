import os
from dotenv import load_dotenv, dotenv_values
import asyncio, aiohttp, json, logging
import sys

logging.basicConfig(filename="client.log", level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

async def send_request(reader, writer, str):
    writer.write(str.encode())
    await writer.drain()
    logging.debug("Request sent")
    response = await reader.readline()
    logging.info(f"Got response {response.decode().strip()}")

async def main():
    reader, writer = await asyncio.open_connection("127.0.0.1", 10000)
    for request in requests:
        print(request)
        await send_request(reader, writer, request)
    
    writer.close()
    await writer.wait_closed()
        

asyncio.run(main())

requests = [
    "IAMAT kiwi.cs.ucla.edu +34.068930-118.445127 1621464827.959498503\n",
    "WHATSAT kiwi.cs.ucla.edu 10 5\n",
    "FLUFFYDOG\n"
]