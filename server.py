import os
from dotenv import load_dotenv, dotenv_values
import asyncio, aiohttp, json, logging, time, re, socket
import sys

class HerdServer:
    ports = {'Bailey':10000,
            'Bona':10001,
            'Campbell':10002, 
            'Clark':10003, 
            'Jaquez':10004}
    friends = {"Clark": ["Jaquez", "Bona"],
               "Campbell": ["Bailey", "Bona", "Jaquez"],
               "Jaquez": ["Clark", "Campbell"],
               "Bailey": ["Bona", "Campbell"],
               "Bona":[] # "Clark", "Campbell", "Bailey"]
               }

    def __init__ (self, name="Bailey"):
        self.name = name
        logging.basicConfig(filename="server.log", level=logging.DEBUG, 
                            format=f'%(asctime)s - {self.name} - %(levelname)s - %(message)s')
        self.extra = {'servername': self.name}
        self.myport = self.ports[name]
        self.server = None
        self.client_info = {}

    async def create_server(self):
        self.server = await asyncio.start_server(
            self.handle_requests, '127.0.0.1', port=self.myport, family=socket.AF_INET
        )
        logging.debug("Server online.", extra=self.extra)

    # check coordinates and add to hash table
    def add_client(self, name, loc_str: str, time_str: str):
        try:
            logging.debug(f"Handling add_client {name} {loc_str} {time_str}")
            coords = [float(i) for i in re.findall("[+-][\.0-9]+", loc_str)]
            logging.debug(coords)

            # check if out of bounds
            if len(coords) != 2 or coords[0] < -180 or coords[0] > 180 or coords[1] < -180 or coords[1] > 180:
                return False
            coords.append(float(time_str))
            self.client_info[name] = coords
            print(self.client_info)
            return True
        except ValueError:
            return False
        
    # send request to google places API.
    async def gplaces_request(self, client: str, n: int, r: int):

        if not (isinstance(n, int) and isinstance(r, int)):
            logging.error(f"Parameters must be ints.", extra=self.extra)
        if n < 1 or n > 20 or r < 1 or r > 50:
            logging.error(f"Parameter out of range: n={n}, r={r}",extra=self.extra)
            return
        
        async with aiohttp.ClientSession() as session:
            load_dotenv()
            print(self.client_info)
            key = os.getenv("GPLACE_KEY")
            request = "https://maps.googleapis.com/maps/api/place/nearbysearch/json?"
            request += "location=" + str(self.client_info[client][0]) + "%2c"
            request += str(self.client_info[client][1])
            request += "&radius=" + str(r * 1000)
            request += "&key=" +key
            logging.debug(f"Google Places API call is {request}")
            async with session.get(request) as resp:
                
                logging.info(f"Google Places API returns {resp.status}")
                json_string = await resp.text()
                #logging.info(json_string)

                wanted = json.loads(json_string)
                wanted["results"] = wanted["results"][:n]
                places = json.dumps(wanted)
                #logging.info(json.dumps(wanted, sort_keys=True, indent=4))
                return places

    async def write_and_close(self, writer, response): 
        logging.debug(f"Writing Response {response}")
        writer.write(response.encode())
        await writer.drain()
        logging.debug(f"Response sent")
        writer.close()
        await writer.wait_closed()
    
    async def open_connection(self, name):
        try:
            _ , writer = await asyncio.open_connection("127.0.0.1", self.ports[name])
            return writer
        except Exception:
            return None

    async def propagate_msg(self, message, signatures:str):
        logging.debug("Begins notifying friends.")
        writes = []
        for server_mate in self.friends[self.name]:
            writer1 = await self.open_connection(server_mate)
            if writer1 and not server_mate in signatures:
                logging.debug("Adding send task to server " + server_mate)
                writes.append(self.write_and_close(writer1, message))
        
        await asyncio.gather(*writes)
        logging.debug("All friends notified")
    
    async def handle_requests(self, reader, writer):
        logging.info("Client established connection.")
        try:
            request = await reader.readline()
            request = request.decode().strip()
            logging.debug("Received request")

            if not request: # if None is read, the client disconnected.
                logging.info("Request is None")
                writer.close()
                await writer.wait_closed()
                return
            
            logging.info("request is " + request)

            # classify requests
            args = request.split()
            response = "? " + request + "\n"
            # empty message
            if len(args) != 4:
                await self.write_and_close(writer, response)
                return
            
            if(args[0] == "IAMAT"):
                logging.info("Processing IAMAT")
                # add to hash table: {name: [long, lat, time]}
                if not self.add_client(args[1], args[2], args[3]):
                    await self.write_and_close(writer, response)
                    return

                logging.debug("Hash Table Updated.")
                #respond to client
                response = f"AT {self.name} {str(time.time() - float(args[3]))} {args[1]} {args[2]} {args[3]}\n"
                print(response)
                await self.write_and_close(writer, response)

                # update neighboring servers
                #message = f"UPDATE {args[1]} {args[2]} {args[3]} {self.name}\n"
                #await self.propagate_msg(message, self.name)

            elif args[0] == "WHATSAT":
                logging.info("Processsing WHATSAT")
                
                if(not args[1] in self.client_info):
                    logging.debug("Client not found in hash table")
                    await self.write_and_close(writer, response)
                    return
                
                api_response = await self.gplaces_request(args[1], int(args[3]), int(args[2]))
                # api request function returns null: error encountered
                if not api_response:
                    logging.debug("API parameters contain error")
                    await self.write_and_close(writer, response)
                    return

                await self.write_and_close(writer, api_response + "\n")
        except KeyboardInterrupt:
            print("Interrupted")

async def start_server(name):
    herd_member = HerdServer(name)
    await herd_member.create_server()
    return herd_member

async def main():
    # argument parsing for valid server name.
    if(len(sys.argv) == 2):
        name = sys.argv[1]
        # start server at given port
        herd_member = await start_server(name)

        try:
            async with herd_member.server:
                await herd_member.server.serve_forever()
        except (KeyboardInterrupt, asyncio.exceptions.CancelledError):
            logging.exception("Keyboard Interrupt Detected, " + name + " shutting down", 
                              extra={"servername":name})
            herd_member.server.close()
            await herd_member.server.wait_closed()
    else:
        print("Wrong number of arguments")

if __name__ == "__main__":
    asyncio.run(main())