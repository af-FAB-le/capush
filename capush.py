# WEBSOCKETS server 
import asyncio
import websockets
import json
import random
import traceback
import logging
from datetime import datetime
import os
from unit import Unit
from project import Project

class Capush():
	def __init__(self):
		path = os.path.join(os.path.dirname(os.path.realpath(__file__)),'log')
		if(not os.path.exists(path)):
			os.makedirs(path)

		self.captureDirectory = os.path.join(os.path.dirname(os.path.realpath(__file__)),'project_captures')
		if(not os.path.exists(self.captureDirectory)):
			os.makedirs(self.captureDirectory)

		logfile = 'log/debug_'+datetime.now().strftime("%F-%H-%M-%S")+'.log'

		### Uncomment below to save log in file ###
		logging.basicConfig(format='%(asctime)s %(levelname)s: %(message)s', filename=logfile, level=logging.INFO)
		
		self.units = {}
		self.ownedunits = {}
		self.projects = {}

		#BROADCASTERS
		self.websocket_connections = [] # all websocket connections (to broadcast)
		self.globalStateSubscribers = []
		self.projectStateSubscribers = []

		logging.info('Capush server started')

	async def handler(self, websocket):
		"""Handles all websockets messages"""
		try:
			if(websocket not in self.websocket_connections):
				websocket.id = random.randint(0, 100000)
				self.websocket_connections.append(websocket)
				logging.info("Websocket %s: new visitor"%(websocket.id))
			async for message in websocket:
				try:
					event = json.loads(message)
				
					if(type(event) == dict):
						if event['type'] == 'init':
							properties = event['message']
							new_unit = Unit(websocket)
							await new_unit.init(properties)

							if('project_id' in properties):
								self.ownedunits[websocket.id] = new_unit
								if(properties['project_id'] not in self.projects):
									self.projects[properties['project_id']] = Project(properties['project_id'], self.captureDirectory)
								await self.projects[properties['project_id']].addSession(self.ownedunits[websocket.id])
							else : 
								self.units[websocket.id] = new_unit		

							if('subscribers' in properties):
								if('globalState' in properties['subscribers']):
									self.globalStateSubscribers.append(websocket)
									self.projectStateSubscribers.append(websocket)
								if('projectState' in properties['subscribers']):
									self.projectStateSubscribers.append(websocket)
							await self.publishProjectsStatus()

						elif event['type'] == 'unit_list_request':
							logging.info("Websocket %s: Requested unit_list"%(websocket.id))						
							await self.send_units_status(websocket)

						elif event['type'] == 'project_unit_connect_request':
							await self.on_webclient_connection_request(websocket, event['message'])						

						elif event['type'] == 'project_unit_disconnect_request':
							await self.on_webclient_disconnection_request(websocket, event['message'])						

						elif event['type'] == 'unit_event':
							unit = self.allUnits[websocket.id]
							if(unit is not None):
								logging.info("Unit %s: unit_event => %s"%(unit.id, event['message']))
								await self.on_unit_event(unit, event['message'])							

						elif event['type'] == 'RTC_answer':
							await self.allUnits[websocket.id].setNewReceiver(event['message'])
						
						else:
							logging.error('Websocket %s event type received is unknown: %s '%(websocket.id, event['type']))

						await self.publish_units_status()
					
					else:
						logging.error('Websocket %s: event received is not a dict: %s '%(websocket.id, event))
				except Exception as e:
					print(e)
		except websockets.ConnectionClosed: 
			await self.on_unit_dies(websocket)  
			await self.publish_units_status()
			self.websocket_connections.remove(websocket)
			if(websocket in self.globalStateSubscribers):
				self.globalStateSubscribers.remove(websocket)

		except Exception as e:
			print(e)
			logging.error(traceback.format_exc())

	@property
	def allUnits(self):
		return {**self.units, **self.ownedunits}

	@property
	def connectionsInfos(self):
		projectsinfos = {}
		for k, project in self.projects.items():
			projectsinfos[project.id] = self.getProjectInfos(project)
		return projectsinfos

	def getProjectInfos(self, project):
		pinfos = project.asDict
		sessions = pinfos['sessions']
		pinfos['sessions'] = [self.allUnits[unitid].asDict() for unitid in sessions]
		return pinfos

	def get_unit_status(self):
		res = {"all" : {}, "available":{}}
		for unit in self.units :
			res["all"][unit] = self.units[unit].asDict()
			if(self.units[unit].isAvalaible()):
				res["available"][unit] = self.units[unit].asDict()
		return res

	async def send_units_status(self, websocket):
		res = self.get_unit_status()
		event = {
			'type': 'unit_list',
			"message": res
		}
		websocket.send(json.dumps(event))

	async def publish_units_status(self):
		res = self.get_unit_status()
		event = {
			'type': 'unit_list',
			"message": res
		}
		websockets.broadcast(self.globalStateSubscribers, json.dumps(event))	

	async def publishProjectStatus(self, project):
		pinfo = self.getProjectInfos(project)
		pid = project.id
		pwebsockets = [self.allUnits[unit['id']].websocket for unit in pinfo['sessions']  if self.allUnits[unit['id']].websocket in self.projectStateSubscribers + self.globalStateSubscribers]
		msg = {
		'type': 'project_info',
		'message' : pinfo
		}
		websockets.broadcast(pwebsockets, json.dumps(msg))		

	async def publishProjectsStatus(self):
		infos = self.connectionsInfos
		for pid, pinfo in infos.items():
			pwebsockets = [self.allUnits[unit['id']].websocket for unit in pinfo['sessions']  if self.allUnits[unit['id']].websocket in self.projectStateSubscribers+ self.globalStateSubscribers]
			
			msg = {
			'type': 'project_info',
			'message' : pinfo
			}
			websockets.broadcast(pwebsockets, json.dumps(msg))

	async def on_unit_event(self, unit, msg): # unit messages broker
		if unit.connectedto:
			project = self.projects[unit.connectedto]
		else : 
			return 
		if(msg["topic"] == 'startvideo'):
			await project.startVideo()
			await self.publishProjectStatus(project)
		elif(msg["topic"] == 'picture'):
			await project.takePicture()
		elif(msg["topic"] == 'stopvideo'):
			await project.stopVideo()
			await self.publishProjectStatus(project)
		else:
			logging.info("Unit %s: Unrecognized event topic %s"%(unit.id, msg["topic"]))
		
	async def on_unit_dies(self, websocket):
		# print("unit dies: "+str(websocket.id))
		if(websocket.id in self.units):
			logging.info("Unit %s: Connection with unit %s has been lost, removing socket and unit"%(websocket.id, self.units[websocket.id].name))
			if(self.units[websocket.id].getStatus() == 2):
				await self.destroy_project_unit_connection(self.units[websocket.id].connectedto, websocket)
			await self.units[websocket.id].close()
			del self.units[websocket.id]

		elif(websocket.id in self.ownedunits):
			logging.info("Unit %s: Connection with unit %s has been lost, removing socket and unit"%(websocket.id, self.ownedunits[websocket.id].name))
			unit = self.ownedunits[websocket.id]
			await self.projects[self.ownedunits[websocket.id].connectedto].remSession(self.ownedunits[websocket.id])
			await self.publishProjectStatus(self.projects[self.ownedunits[websocket.id].connectedto])
			await self.ownedunits[websocket.id].close()
			del self.ownedunits[websocket.id]

	async def on_webclient_connection_request(self, websocket, msg):
		unit_id = int(msg["unit_id"])
		project_id = msg["project_id"]
		logging.info("Unit %s: Connection request -> project %s - Unit %s"%(websocket.id, project_id, unit_id))

		ansdict = {}
		ansdict["project_id"] = project_id
		ansdict["unit_id"] = unit_id

		if(unit_id in (self.units.keys())):
			unit = self.units[unit_id]
			if(unit.isAvalaible()):
				ansdict["accepted"] = 1
				ansdict["msg"] = "Your connection to %s has been confirmed"%(unit.name)
				await unit.startWebConnection(project_id)
				await self.projects[project_id].addSession(unit)
				await self.publishProjectStatus(self.projects[project_id])

			else:
				#not available
				ansdict["accepted"] = 0
				ansdict["msg"] = "Connection refused, %s is not available"%(unit.name)
		else:
			#No unit
			ansdict["accepted"] = 0
			ansdict["msg"] = "Connection refused, no unit with id  %s"%(unit_id)

		event = {"type": 'webclient_unit_connect_response',"message": ansdict}
		await websocket.send(json.dumps(event))

	async def destroy_project_unit_connection(self, project_id, unitsocket):
		units = {**self.units, **self.ownedunits}
		unit = units[unitsocket.id]
		if (project_id in self.projects):
			await self.projects[project_id].remSession(unit)
			await self.publishProjectStatus(self.projects[project_id])

		if unitsocket.id in self.units:
			await self.units[unitsocket.id].endWebConnection()
		

	async def on_webclient_disconnection_request(self, websocket, msg):
		project_id = msg["project_id"]
		unit_id = int(msg["unit_id"])
		logging.info("Unit %s: Disconnection request -> project %s - Unit %s"%(websocket.id, project_id, unit_id))
		ansdict = {}
		ansdict["project_id"] = project_id
			
		if(unit_id in self.units):
			unitsocket = self.units[unit_id].websocket
			unitname = self.units[unit_id].name
			await self.destroy_project_unit_connection(project_id, unitsocket)
			ansdict["accepted"] = 1
			ansdict["msg"] = "Connection to %s closed"%(unitname)
		elif(unit_id in self.ownedunits):
			ansdict["accepted"] = 0
			ansdict["msg"] = "Unit %s can't be disconnected from project %s"%(unit_id, project_id)	
		else:
			ansdict["accepted"] = 0
			ansdict["msg"] = "Unit %s unknown"%(unit_id)	

		event = {
			"type": 'webclient_unit_disconnect_response',
			"message": ansdict
		}
		await websocket.send(json.dumps(event))

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