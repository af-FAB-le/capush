from aiortc import RTCPeerConnection, RTCSessionDescription
import asyncio
from datetime import datetime
import logging
import json
from aiortc.contrib.media import MediaRelay

class Unit():
	def __init__(self, websocket):
		self.websocket = websocket

	async def init(self, params):
		if('name' in params):
			self.name = params["name"]
		else:
			self.name = 'unnammed_unit_' + str(self.id)
		
		self._status = 1 # 1=available 2=connected to project
		self._last_status_update = datetime.now()
		self._location = ""
		self._last_location_update = datetime.now()
		
		self.pc_receiver = None
		self.__pc_sender = None
		self.__has_videostream = False
		self.videostream = None
		if('RTC_offer' in params):
			await self.initRTCSender(params['RTC_offer'])

		self.__gets_videostreams = False	

		if('gets_videostreams' in params):
			self.__gets_videostreams = bool(params["gets_videostreams"])

		self.__connectedto = None
		if('project_id' in params):
			self.__connectedto = params['project_id']
			self.__updateStatus(2)

		msg = {'type' : 'init_confirmation', 'message': self.asDict()}
		await self.websocket.send(json.dumps(msg))

		if('has_videostream' in params and not self.__has_videostream):
			logging.error(self.me_say("Unit didn't received any video track"))

		# logging.info("New unit connected \n : %s "%(self.toString()))
		logging.info(self.me_say("Initialized: "+ self.toString()))

	async def sendStateToWS(self):
		msg = {'type' : 'unit_info', 'message': self.asDict()}
		await self.websocket.send(json.dumps(msg))

	@property
	def id(self):
		return self.websocket.id
	
	@property
	def has_videostream(self):
		return self.__has_videostream

	@property
	def gets_videostreams(self):
		return self.__gets_videostreams
	
	@property
	def connectedto(self):
		return self.__connectedto
	
	def me_say(self,s):
		return "Unit %s: %s"%(self.id, s)

	def asDict(self):
		return {
		"name" : self.name, 
		"id": self.id,
		"gets___videostreams": self.gets_videostreams,
		"has_videostream": self.has_videostream,
		"status" : self._status, 
		"location" : self._location, 
		"connected_to": self.connectedto,
		"last_location_update" : self._last_location_update.strftime("%F-%H-%M-%S"), 
		"last_status_update": self._last_status_update.strftime("%F-%H-%M-%S")
		}

	def toString(self):
		return json.dumps(self.asDict())

	def getStatus(self):
		return self._status

	def __updateStatus(self, status): # led activity change 
		self._status = status
		self._last_status_update = datetime.now()

	def isAvalaible(self):
		return self._status == 1

	async def startWebConnection(self, project_id):
		self.__updateStatus(2)
		self.__connectedto = project_id
		await self.sendStateToWS()

	async def endWebConnection(self):
		self.__updateStatus(1)
		self.__connectedto = None
		if(self.pc_receiver is not None):
			await self.pc_receiver.close()
			self.pc_receiver = None
		if(self.websocket.open):
			await self.sendStateToWS()

	async def close(self):
		# print("closing")
		if(self.pc_receiver is not None):
			await self.pc_receiver.close()
			self.pc_receiver = None
			# print(self.me_say("Closed icoming RTC Connection"))

		if(self.__pc_sender is not None):
			await self.__pc_sender.close()
			del self.__pc_sender 
			self.__pc_sender = None
			self.videostream = None
			# print(self.me_say("Closed Sending RTC Connection"))

	async def initRTCSender(self, params):
		offer = RTCSessionDescription(sdp=params["sdp"], type=params["type"])
		self.__pc_sender = RTCPeerConnection()
		# pc = self.__pc_sender
		# print(self.__pc_sender)
		# @.__pc_sender.on(self, "connectionstatechange")
		async def on_connectionstatechange():
			# print(self.__pc_sender)
			# print(self.me_say("RTC connection state is %s" % self.__pc_sender.connectionState))
			if self.__pc_sender.connectionState == "failed":
				# logging.error("closing")
				await self.__pc_sender.close()
		self.__pc_sender.add_listener("connectionstatechange", on_connectionstatechange)

		# @.__pc_sender.on(self, "track")
		def on_track(track):
			# logging.info("Track %s received", track.kind)
			if track.kind == "video":
				self.__has_videostream = True
				self.videostream = track
				relay = MediaRelay()
				relay.subscribe(self.videostream)
				# print(self.me_say("received track: %s"%(self.name)))
				
			# @track.on("ended")
			async def on_ended():
				self.__has_videostream = False
				self.videostream = None
				#if(self.__pc_sender is not None):
				await self.__pc_sender.close()
				# logging.info("Track %s ended", track.kind)
			track.add_listener("endded", on_ended)

		self.__pc_sender.add_listener("track", on_track)


		await self.__pc_sender.setRemoteDescription(offer)
		answer = await self.__pc_sender.createAnswer()
		await self.__pc_sender.setLocalDescription(answer)
		response = {
			"type": 'RTC_answer',
			"message": {"sdp": self.__pc_sender.localDescription.sdp, "type": self.__pc_sender.localDescription.type}
		}
		await self.websocket.send(json.dumps(response))
		# print(self.me_say("sent RTC_answer"))

	async def updateRTCReceiver(self, sources):
		if(self.pc_receiver != None):
			print(self.pc_receiver.connectionState)
			await self.pc_receiver.close()
			print(self.pc_receiver.connectionState)
		nsources = len(sources.items())
		ntracks = 0
		if(nsources > 0):
			self.pc_receiver = RTCPeerConnection()
			async def on_connectionstatechange():
				if self.pc_receiver.connectionState == "failed":
					await self.pc_receiver.close()
				self.pc_receiver.add_listener("connectionstatechange", on_connectionstatechange)
			
			datas = {}
			for key, source in sources.items():
				if(source.videostream):
					relay = MediaRelay()
					newtrack = relay.subscribe(source.videostream)
					datas[source.id] = newtrack.id
					self.pc_receiver.addTrack(newtrack)
					ntracks += 1
			if(ntracks> 0):
				offer = await self.pc_receiver.createOffer()
				await self.pc_receiver.setLocalDescription(offer)
				response = {
					"type": 'RTC_offer',
					"message": {"sdp": self.pc_receiver.localDescription.sdp, "type": self.pc_receiver.localDescription.type, "data": datas}
				}

				await self.websocket.send(json.dumps(response))

	async def setNewReceiver(self, params):
		answer = RTCSessionDescription(sdp=params["sdp"], type=params["type"])
		print(self.pc_receiver.connectionState)
		if(self.pc_receiver.connectionState != 'closed'):
			await self.pc_receiver.setRemoteDescription(answer)

	def __del__(self):
		logging.info(self.me_say("deleted"))