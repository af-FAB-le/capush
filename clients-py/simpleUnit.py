import asyncio
import websockets
import json
from capushClient import CapushClient

async def main():
	with open('../config.json') as json_file:
		data = json.load(json_file)
		ws_server_address = data[0]['websocket-server-address']
		ws_server_port = data[0]['websocket-server-port'] 
	uri = "ws://"+ws_server_address+":"+str(ws_server_port)

	async with websockets.connect(uri) as websocket:
		capush = CapushClient(name = "Simple Unit")
		await capush.start(websocket)
		
		

		@capush.on('unit_info')
		def unit_info(msg):
			print(msg)

		@capush.on('unit_list')
		def unit_list(msg):
			print(msg)

		@capush.on('webclient_unit_connect_response')
		def webclient_unit_connect_response(msg):
			print(msg)

		@capush.on('webclient_unit_disconnect_response')
		def webclient_unit_disconnect_response(msg):
			print(msg)

		@capush.on('unit_info')
		def unit_info(msg):
			print(msg)

		@capush.on('RTC_answer')
		def RTC_answer(msg):
			print(msg)

		@capush.on('snapshot')
		def snapshot():
			print('picture taken from me ')

		@capush.on('recording_status')
		def recording_status(msg):
			print(msg)

		@capush.on('connected')
		def connected():
			print('connected !')

		@capush.on('connection_status_change')
		def connection_status_change(msg):
			print(msg)

		@capush.on('project_recording_start')
		def project_recording_start():
			print('project recording starting')

		@capush.on('project_recording_stop')
		def project_recording_stop():
			print('project recording ended')

		@capush.on('peer_connection_end')
		def peer_connection_end(msg):
			print(msg)

		@capush.on('peer_connection_start')
		def peer_connection_start(msg):
			print(msg)

		await capush.run() # Starts receive things, not only once
asyncio.get_event_loop().run_until_complete(main())
