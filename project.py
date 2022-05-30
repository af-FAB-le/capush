import os
import asyncio
from datetime import datetime
import logging
from aiortc.contrib.media import MediaRelay
import av
from av import AudioFrame, VideoFrame
from av.frame import Frame
import cv2
import numpy as np
import json

class Project():
	def __init__(self, project_id, contentdirectory):
		self.id = project_id
		self.__sessions = {}
		self.user = None
		self.__recordingtasks = []
		self.__containers = []
		self.__contentdirectory = os.path.join(contentdirectory, str(self.id))
		self.__streamsources = {}
		self.__streamtargets = {}

		if(not os.path.exists(self.__contentdirectory)):
			os.makedirs(self.__contentdirectory)

		av.logging.set_level(av.logging.ERROR)
		logging.info("Project %s: created"%(self.id))	

	@property
	def asDict(self):
		sessions = [session.unit_id for k, session in self.__sessions.items()]
		infos = {
			'project_id' : self.id,
			'recording': self.isRecording,
			'sessions': sessions
		}
		return infos
	
	@property
	def isRecording(self):
		return self.__recordingtasks != []

	def me_say(self,s):
		return "Project %s: %s"%(self.id, s)

	async def addSession(self, unit):
		self.__sessions[unit.websocket.id] = Session(self.id, unit.websocket.id)
		# print(self.me_say("adding session"))
		if(unit.has_videostream):
			# print(self.me_say("Camera unit: should add camera sources to RTC and reoffer receivers"))
			self.__streamsources[unit.id]= unit
			for key, target in self.__streamtargets.items():
				await target.updateRTCReceiver(self.__streamsources)

		if(unit.gets_videostreams):
			# print(self.me_say("Screen unit: should add camera sources to RTC and offer receiver"))
			self.__streamtargets[unit.id] = unit

			if len(self.__streamsources.items())>0:
				await unit.updateRTCReceiver(self.__streamsources)

	async def remSession(self, unit):
		if(unit.id in self.__sessions):
			del self.__sessions[unit.id]
				
		if unit.has_videostream and (unit.id in self.__streamsources):
			del self.__streamsources[unit.id]

			# Updating RTC connections
			for key, target in self.__streamtargets.items():
				await target.updateRTCReceiver(self.__streamsources)

		if unit.gets_videostreams and (unit.id in self.__streamtargets):
			del self.__streamtargets[unit.id]

	async def startVideo(self):
		logging.info("Project %s: Start recording from %s camera sources"%(self.id, len(self.__streamsources)))
		for key, source in self.__streamsources.items():
			if source.videostream:
				logging.info("Project %s: Start recording from unit: %s "%(self.id, source.asDict()))
				await self.__startRecord(source)
				await source.websocket.send(json.dumps({'type': 'recording_status', 'message': {'recording' : True}}))

	async def stopVideo(self):
		for task in self.__recordingtasks:
			task.cancel()
		for container, stream, sourceid in self.__containers:
			for packet in stream.encode(None):
				container.mux(packet)
			container.close()
			await self.__streamsources[sourceid].websocket.send(json.dumps({'type': 'recording_status', 'message': {'recording' : False}}))

		self.__recordingtasks = []
		logging.info("Project %s: New entry in project containing video from %s sources"%(self.id, len(self.__containers)))
		self.__containers = []

	async def takePicture(self):
		logging.info("Project %s: Taking picture from %s camera sources"%(self.id, len(self.__streamsources)))
		for key, source in self.__streamsources.items():
			if source.videostream:
				picfile = os.path.join(self.__contentdirectory, datetime.now().strftime("%F%H%M%S%f")+'_'+str(source.id)+'.png')
				relay = MediaRelay()
				frame = await relay.subscribe(source.videostream).recv()
				self.__snapShot(picfile, frame)
				logging.info("Project %s: new picture from unit %s at %s"%(self.id, source.id, picfile))
				await source.websocket.send(json.dumps({'type': 'snapshot'}))

	async def __startRecord(self, source):
		relay = MediaRelay()
		track = relay.subscribe(source.videostream)
		file = os.path.join(self.__contentdirectory, datetime.now().strftime("%F%H%M%S%f")+'_'+str(source.id)+'.mp4')
		container = av.open(file=file, mode="w")
		frame = await track.recv()
		if container.format.name == "image2":
			stream = container.add_stream("png", rate=30)
			stream.pix_fmt = "rgb24"
		else:
			stream = container.add_stream("libx264", rate=30)
			stream.pix_fmt = "yuv420p"

		stream.width = frame.width
		stream.height = frame.height

		self.__containers += [(container, stream, source.id)]
		self.__recordingtasks += [asyncio.ensure_future(self.__run_track(track, container, stream))]

	def __snapShot(self, file, frame):
		pic = frame.to_ndarray(format="bgr24")
		cv2.imwrite(file, pic)

	async def __run_track(self, track, container, stream):
		firstframepts = 0
		while True:
			frame = await track.recv()
			if(firstframepts == 0):
				firstframepts = frame.pts
			pts = frame.pts
			frame.pts = pts-firstframepts
			packets = stream.encode(frame)

			for packet in packets:
				container.mux(packet)

class Session():
	def __init__(self, project_id, unit_id):
		self.project_id = project_id;
		self.unit_id = unit_id
		self.webclient_connectionstart = datetime.now()
		logging.info("Project %s: connection to %s started at %s"%(self.project_id, self.unit_id, self.webclient_connectionstart.strftime("%F-%H-%M-%S")))

	def __del__(self):
		logging.info("Project %s: connection to %s ended at %s"%(self.project_id, self.unit_id, datetime.now().strftime("%F-%H-%M-%S")))
