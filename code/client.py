import asyncio, logging, time

logging.basicConfig(filename="client.log", level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

async def send_request(reader, writer, str):
    writer.write(str.encode())
    await writer.drain()
    logging.debug(f"Request sent: {str.strip()}")
    response = await reader.read(10000)
    logging.info(f"Got response {response.decode().strip()}\n")


async def main():
    requests = [
    f"IAMAT kiwi.cs.ucla.edu +34.068930-118.445127 {time.time()}\n",
    "WHATSAT kiwi.cs.ucla.edu 10 5\n",
    f"IAMAT kiwi.cs.ucla.edu +39.068930-118.445127 {time.time()}\n",
    f"IAMAT sprout.cs.ucla.edu +39.068930-118.445127 {time.time()}\n",
    "WHATSAT tasha.cs.ucla.edu 50 20\n",
    "WHATSAT kiwi.cs.ucla.edu 100 100\n",
    f"IAMAT elminster.cs.ucla.edu +39.068930-118.445127 {time.time()}\n",
    f"IAMAT tasha.cs.ucla.edu +39.068930-118.445127 {time.time()}\n",
    "WHATSAT kiwi.cs.ucla.edu 10 5\n",
    "FLUFFYDOG\n"
    ]

    requests2 = [
        [f"IAMAT kiwi.cs.ucla.edu +34.068930-118.445127 {time.time()}\n", 10001],
        ["WHATSAT kiwi.cs.ucla.edu 10 2\n", 10002]
    ]

    for request in requests2:
        msg, port = request
        reader, writer = await asyncio.open_connection("127.0.0.1", port)
        await send_request(reader, writer, msg)
        writer.close() 
        await writer.wait_closed()
        
asyncio.run(main())


"AIzaSyDUosP1G0nB-UDOsNnJ4Ety8KNz5q6TzDs"