import os
from dotenv import load_dotenv, dotenv_values
import asyncio, aiohttp, json, logging
import sys

ports = {'Bailey':10000,
         'Bona':10001,
         'Campbell':10002, 
         'Clark':10003, 
         'Jaquez':10004}

logging.basicConfig(filename="server.log", level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

async def send_request(n: int, r):
    if not (isinstance(n, int) and isinstance(r, int)):
        logging.error(f"Parameters must be ints.")
    if n < 1 or n > 20 or r < 1 or r > 50:
        logging.error(f"Parameter out of range: n={n}, r={r}")
        return
    
    async with aiohttp.ClientSession() as session:
        load_dotenv()
        
        key = os.getenv("GPLACE_KEY")
        request = "https://maps.googleapis.com/maps/api/place/nearbysearch/json?"
        request += "location=" + "+34.068930%2c-118.445127"
        request += "&radius=" + str(r * 1000)
        request += "&key=" +key

        async with session.get(request) as resp:
            
            logging.info(msg=resp.status)
            json_string = await resp.text()
            #logging.info(json_string)

            wanted = json.loads(json_string)
            wanted["results"] = wanted["results"][:n]
            logging.info(json.dumps(wanted, sort_keys=True, indent=4))


async def handle_requests(reader, writer):
    logging.info("Client established connection.")
    while True:
        try:
            # get next request from reader
            logging.debug("About to read")
            request = await reader.readline()
            request = request.decode().strip()
            logging.debug("Received request")
            if not request: # if None is read, the client disconnected.
                logging.info("Request is None")
                break
            logging.info("request is " + request)

            # classify requests
            args = request.split()
            response = "? " + request + "\n"
            # empty message
            if len(args) < 1:
                writer.write(response.encode())
                await writer.drain()
                continue
            
            if(args[0] == "IAMAT"):
                logging.info("Processing IAMAT")
                if len(args) != 4:
                    writer.write(response.encode())
                    await writer.drain()
                    continue
                logging.info("Format correct, sending response.")
                response = "congrates, non-silly sender\n"
                writer.write(response.encode())
                await writer.drain()
                logging.info("Response sent")
            else:
                writer.write(response.encode())
                await writer.drain()
                continue
            
        except KeyboardInterrupt:
            break
    
    logging.info("Closing the connection.")
    writer.close()

async def main():
    # argument parsing for valid server name.
    if(len(sys.argv) == 2):
        myport = ports[sys.argv[1]]

        server = await asyncio.start_server(
            handle_requests, '127.0.0.1', port=myport
        )
        addr = server.sockets[0].getsockname()
        try:
            async with server:
                await server.serve_forever()
        except KeyboardInterrupt:
            logging.exception("Keyboard Interrupt Detected," + myport + " shutting down")
            server.close()
            await server.wait_closed()
    else:
        print("Wrong number of arguments")

if __name__ == "__main__":
    asyncio.run(main())