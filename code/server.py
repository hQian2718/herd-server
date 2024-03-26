import os
from dotenv import load_dotenv, dotenv_values
import asyncio
import aiohttp
import json
import logging
import time
import re
import socket
import argparse

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
               "Bona":["Clark", "Campbell", "Bailey"]
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
            self.handel_request_clean, host="127.0.0.1", port=self.myport, family=socket.AF_INET
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
            # print(self.client_info)
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
            key = os.getenv("GPLACE_KEY")
            # key = "AIzaSyA83pvRMs3tb_6pz6xm9aoj7wTBFJ04oU0"
            request = "https://maps.googleapis.com/maps/api/place/nearbysearch/json?"
            request += "location=" + str(self.client_info[client][0]) + "%2c"
            request += str(self.client_info[client][1])
            request += "&radius=" + str(r * 1000)
            request += "&key=" +key
            logging.debug(f"Google Places API call is {request}")
            async with session.get(request) as resp:
                
                logging.info(f"Google Places API returns {resp.status}")
                json_string = await resp.text()

                wanted = json.loads(json_string)
                wanted["results"] = wanted["results"][:n]
                places = json.dumps(wanted, indent=4)

                #string manipulation
                result = re.sub(r'\n{2,}', '\n', places)
                result = result.rstrip('\n')
                return places + "\n\n"

    async def write_and_close(self, writer, response): 
        response = response.rstrip('\n')
        logging.debug(f"Writing Response {response}")
        writer.write(response.encode())
        await writer.drain()
        # logging.debug(f"Response sent")
        writer.close()
        await writer.wait_closed()
        # logging.debug("Writer closed here.")
    
    async def open_connection(self, name):
        try:
            _ , writer = await asyncio.open_connection("127.0.0.1", self.ports[name], family=socket.AF_INET)
            return writer
        except Exception:
            return None
    
    async def propagate_msg(self, req, signatures:str):
        logging.debug("Begins notifying friends.")
        writes = []
        for server_mate in self.friends[self.name]:
            if not server_mate in signatures:
                writer1 = await self.open_connection(server_mate)
                logging.debug("Server friend " + server_mate + " doesn't know!")
                if writer1:
                    msg = f"UPDATE {req[1]} {req[2]} {req[3]} {signatures}{self.name}\n"
                    logging.debug("Friend online, sending update to " + server_mate)
                    writes.append(self.write_and_close(writer1, msg))
                else:
                    logging.debug("Friend not online, skipping.")
        
        await asyncio.gather(*writes)
        logging.debug("All friends notified")
    
    async def handle_set(self, request):
        args = request.split()
        if len(args) != 4:
                return "?" + request + "\n"  
        else:
            logging.info("Processing IAMAT")
            # add to hash table: {name: [long, lat, time]}
            if not self.add_client(args[1], args[2], args[3]):
                return "?" + request + "\n"  

            logging.debug("Hash Table Updated.")
            #respond to client
            response = f"AT {self.name} {str(time.time() - float(args[3]))} {args[1]} {args[2]} {args[3]}\n"
            # update neighboring servers
            await self.propagate_msg(args, "")
            return response

    async def handle_query(self, request):
        _, name, r_km, n = request.split()
        logging.info("Processsing WHATSAT")
        if(not name in self.client_info):
            logging.debug("Client not found in hash table")
            return "? " + request + "\n"
        else:        
            api_response = await self.gplaces_request(name, int(n), int(r_km))
            # api_response = response
                # api request function returns null: error encountered
            if not api_response:
                logging.debug("API parameters contain error")
                return "? " + request + "\n"

            coords = str(self.client_info[name][0]) + str(self.client_info[name][1])
            if not coords.startswith("+") and not coords.startswith("-"):
                coords = "+" + coords 
            
            header = f"AT {self.name} +1.00 {name} {coords} {self.client_info[name][2]}\n"
            return header + api_response
    
    async def handle_flood(self, request):
        args = request.split()

        if not args[1] in self.client_info or float(args[3]) > self.client_info[args[1]][2]:
            self.add_client(args[1], args[2], args[3])
            await self.propagate_msg(args, args[4])
        return request
    
    async def handel_request_clean(self, reader, writer):
        request = await reader.read(1000)
        request = request.decode().strip()
        logging.info(f"Input: {request}")
        response = "? " + request + "\n"
        if(request.startswith("IAMAT")):
            response = await self.handle_set(request)
        elif(request.startswith("WHATSAT")):
            response = await self.handle_query(request)
        elif(request.startswith("UPDATE")):
            await self.handle_flood(request)
            await writer.drain()
            return
        
        # write back
        writer.write(response.encode())
        await writer.drain()
        writer.close()

async def start_server(name):
    herd_member = HerdServer(name)
    await herd_member.create_server()
    return herd_member

async def main():

    parser = argparse.ArgumentParser('Herd Server')
    parser.add_argument('server_name', type=str,
                        help='required server name input')
    args = parser.parse_args()
    try:
        herd_member = await start_server(args.server_name)
        async with herd_member.server:
            await herd_member.server.serve_forever()
            
        logging.info("Server is shutting down.")
        herd_member.server.close()
    except Exception as e:
        logging.error("Exception encountered, shutting down." + e.__str__())

if __name__ == "__main__":
    asyncio.run(main())