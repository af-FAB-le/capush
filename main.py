# WEBSOCKETS server 
import asyncio
import websockets
import json
from capush import Capush

async def main():
	controller = Capush()
	with open('config.json') as json_file:
		data = json.load(json_file)
		ws_server_address = data[0]['websocket-server-address']
		ws_server_port = data[0]['websocket-server-port']
		async with websockets.serve(controller.handler, ws_server_address, ws_server_port):
			await asyncio.Future() # run forever

try:
	asyncio.run(main())
except KeyboardInterrupt:  # dirty
	pass