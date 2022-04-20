# WEBSOCKETS server 
import asyncio
import websockets
import json
from datetime import datetime
import random
import traceback
import logging
class Capush():
	def __init__(self):
		self.units = {}
		self.project_unit_connections = {}
		self.websocket_connections = [] # all websocket connections (to broadcast)
		self.projects_websockets = {}
		self.unitListTopic = 'unit_list'

	async def handler(self, websocket):
		try:
			if(websocket not in self.websocket_connections):
				websocket.id = random.randint(0, 100000)
				self.websocket_connections.append(websocket)
			async for message in websocket:
				event = json.loads(message)
				if(type(event) == dict):
					if event['type'] == 'init':
						if("client_type" in event['message']):
							if(event['message']["client_type"] == 'manager'):
								self.projects_websockets[websocket.id] = event['message']['project_name']
								await self.publish_units_status()
							elif(event['message']["client_type"] == 'unit'):
								await self.on_new_unit(event['message']['unit_name'], websocket)
							else:
								print("Unknown visitor")
								# close websocket ?
					elif event['type'] == 'unit_list_request':
						await self.publish_units_status()
					elif event['type'] == 'project_unit_connect_request':
						await self.on_webclient_connection_request(websocket, event['message'])
					elif event['type'] == 'project_unit_disconnect_request':
						await self.on_webclient_disconnection_request(websocket, event['message'])
					elif event['type'] == 'unit_event':
						await self.on_unit_event(websocket, event['message'])
					else:
						print("event type is unknown")
						print(event)
				else:
					print('event is not a dict')
					print(event)

		except websockets.ConnectionClosed:
			self.websocket_connections.remove(websocket)
			if(websocket.id in self.units):
				print("connexion with %s has been lost, removing"%(self.units[websocket.id].name))
				await self.on_unit_dies(websocket.id)
			
			elif(websocket.id in self.projects_websockets):
				print("manager connection lost")
				del self.projects_websockets[websocket.id]
				# rem connections

		except Exception as e:
			logging.error(traceback.format_exc())
		
	async def publish_units_status(self):
		print(self.units)
		print(self.projects_websockets)
		res = {"all" : {}, "available":{}}
		for unit in self.units :
			res["all"][unit] = self.units[unit].asDict()
			if(self.units[unit].isAvalaible()):
				res["available"][unit] = self.units[unit].asDict()
		event = {
			'type': self.unitListTopic,
			"message": res
		}
		websockets.broadcast(self.websocket_connections, json.dumps(event))		

# 	def infos_log(self):
# 		rospy.loginfo("Controller status \n : %i unit connected"%(len(self.units)))
# 		jsonStr = json.JSONEncoder().encode([unit.asDict() for unit in self.units.values()])
# 		rospy.loginfo(jsonStr)

	async def on_unit_event(self, websocket, msg):
		if(websocket.id in self.units):
			print("Received message from" + self.units[websocket.id].name)
			print(msg)
		

		elif(websocket.id in self.managers_websockets):
			print("Received message from" + self.projects_websockets[websocket.id])
			print(msg)
		

	async def on_new_unit(self, unit_name, websocket):
		self.units[websocket.id] = Unit(unit_name, websocket)
		print("New unit connected \n : %s "%(unit_name))
		#self.infos_log()
		await self.publish_units_status()

	async def on_unit_dies(self, unit_id):
		unit_id = int(unit_id)
		print("Unit has died \n : %s "%(unit_id))
		await self.on_unit_lost(unit_id)
		await self.publish_units_status()

	async def on_unit_lost(self, unit_id):
		unit_id = int(unit_id)
		if(self.units[unit_id].getStatus() == 2):
			await self.destroy_project_unit_connection(self.units[unit_id].connectedto, unit_id)
		del self.units[unit_id]

	async def on_unit_info(self, data):
		print("Received update from %s "%(data.unit_name))

	async def on_webclient_connection_request(self, websocket, msg):

		unitid = int(msg["unit_id"])
		projectname = msg["project_name"]
		ansdict = {}
		ansdict["project_name"] = self.projects_websockets[websocket.id]
		ansdict["unit_id"] = unitid

		if(unitid in (self.units.keys())):
			unitname = self.units[unitid].name
			ansdict["unit_name"] = unitname
			if(self.units[unitid].isAvalaible()):
					ansdict["accepted"] = 1
					ansdict["msg"] = "Your connection to %s has been confirmed"%(self.units[unitid].name)
					await self.create_project_unit_connection(projectname, unitid)
			else:
				#not available
				ansdict["accepted"] = 0
				ansdict["msg"] = "Connection refused, %s is not available"%(self.units[unitid].name)
		else:
			#No unit named
			ansdict["accepted"] = 0
			ansdict["msg"] = "Connection refused, no unit with id  %s"%(unitid)

		await self.publish_units_status()

		event = {
			"type": 'webclient_unit_connect_response',
			"message": ansdict
		}

		await websocket.send(json.dumps(event))

	async def create_project_unit_connection(self, project_name, unitid):
		if(project_name not in self.project_unit_connections):
			self.project_unit_connections[project_name] = {}
		self.units[unitid].startWebConnection(project_name)
		self.project_unit_connections[project_name][unitid] = web_unit_session(project_name, unitid);
		await self.publish_units_status()

	async def destroy_project_unit_connection(self,project_name, unit_id):
		if (project_name in self.project_unit_connections):
			if(unit_id in self.project_unit_connections[project_name]):
				del self.project_unit_connections[project_name][unit_id]
		else :
			print("Session to be detroyed wasn't recorded... ")
		if unit_id in self.units:
			self.units[unit_id].endWebConnection()
		await self.publish_units_status()

	async def on_webclient_disconnection_request(self, websocket, msg):
		print("Received disconnection request from client")
		project_name = msg["project_name"]
		unitid = int(msg["unit_id"])
		unitname = self.units[unitid].name
		ansdict = {}
		ansdict["project_name"] = project_name
		ansdict["unit_name"] = unitname

		await self.destroy_project_unit_connection(project_name, unitid)
		ansdict["accepted"] = 1
		ansdict["msg"] = "Connection to %s closed"%(unitname)
		ansdict["unitname"] = unitname
		event = {
			"type": 'webclient_unit_disconnect_response',
			"message": ansdict
		}

		await websocket.send(json.dumps(event))

	def getAllUnitsAsDict(self, available_only):
		res = {}
		for unit in self.units :
			if(self.units[unit].isAvalaible() or not available_only):
				res[unit] = self.units[unit].asDict()
		return res

class Unit():
	def __init__(self, name, websocket):
		self.name = name
		self.id = websocket.id
		self.websocket = websocket
		self._status = 1
		self._last_status_update = datetime.now()
		self._location = ""
		self._last_location_update = datetime.now()
		self.connectedto = None

	def asDict(self):
		return {
		"name" : self.name, 
		"id": self.id,
		"status" : self._status, 
		"location" : self._location, 
		"last_location_update" : self._last_location_update.strftime("%H:%M:%S"), 
		"last_status_update": self._last_status_update.strftime("%H:%M:%S")
		}

	def getStatus(self):
		return self._status

	def updateLocation(self, loc):
		self._location = loc
		self._last_location_update = datetime.now()

	def updateStatus(self, status): # led activity change 
		self._status = status
		self._last_status_update = datetime.now()

	def isAvalaible(self):
		return self._status == 1
	def startWebConnection(self, username):
		self.updateStatus(2)
		self.connectedto = username

	def endWebConnection(self):
		self.updateStatus(1)
		self.connectedto = None
	# def __del__(self):

class web_unit_session():
	def __init__(self, project_name, unit_id):
		self.project_name = project_name;
		self.unitId = unit_id
		self.webclient_connectionstart = datetime.now()
		print("Connection from %s to %s started at %s"%(self.project_name, self.unitId, self.webclient_connectionstart.strftime("%H:%M:%S")))
	
	def log(self, tolog): # use to log session activity 
		print("Must log this into a file")

	def __del__(self):
		print("Connection from %s to %s ended at %s"%(self.project_name, self.unitId, datetime.now().strftime("%H:%M:%S")))

async def main():
	controller = Capush()
	with open('config.json') as json_file:
		data = json.load(json_file)
		ws_server_address = data[0]['websocket-server-address']
		ws_server_port = data[0]['websocket-server-port']
		async with websockets.serve(controller.handler, ws_server_address, ws_server_port):
			print("Websocket started")
			await asyncio.Future() # run forever

asyncio.run(main())