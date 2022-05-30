import asyncio
import json
from pyee.base import EventEmitter
import websockets
class CapushClient(EventEmitter):
    def __init__(self, name = None, gets_videostreams =False, stream= None, videostream = None, project_id = None, subscribers = []):
        super().__init__()
        self.project_info = {}
        self.peers = {}
        self.pc = None
        self.incomingstreams = {'data':{}, 'streams':{}}
        self.subscribers = []

        self.name = name
        self.gets_videostreams = gets_videostreams
        self.has_videostream = stream != None
        self.videostream = stream
        self.project_id = project_id
        self.subscribers = subscribers

        if self.gets_videostreams and not 'projectState' in self.subscribers:
            self.subscribers += ['projectState']

    async def start(self, websocket):
            try: 
                self.websocket = websocket
                await self.createServerConnection()
                asyncio.ensure_future(self.run())
            except websockets.ConnectionClosed: 
                print("connection closed")

    async def run(self):
        while True:
            try: 
                msg = await self.websocket.recv()
                msg = (json.loads(msg))
                if('type' in msg):
                    topic = msg['type']

                    if topic == 'init_confirmation':
                        self.on_init_confirmation(msg['message'])
                        self.emit('unit_info', msg['message'])

                    elif topic ==  "unit_list":
                        self.emit('unit_list', msg['message'])

                    elif topic ==  'webclient_unit_connect_response':
                        self.emit('webclient_unit_connect_response', msg['message'])

                    elif topic ==  'webclient_unit_disconnect_response':  
                        self.emit('webclient_unit_disconnect_response', msg['message'])

                    elif topic ==  "project_info":
                        self.onProjectInfo(msg['message'])

                    elif topic ==  "unit_info":
                        self.update(msg['message'])
                        self.emit('unit_info', msg['message'])

                    elif topic ==  'RTC_answer':
                        self.emit('RTC_answer', msg['message'])

                    elif topic ==  'snapshot':
                        self.emit('snapshot')

                    elif topic ==  'recording_status':
                        self.emit('recording_status', msg['message'])          

                    elif topic ==  'RTC_offer':
                        self.onRTCOffer(msg['message'])
                    else:
                        print(msg)

            except websockets.ConnectionClosed as e : 
                #self.pc_close()
                print('Connection to server lost')

#     onRTCOffer(offer){
#         self.pc = new RTCPeerConnection({sdpSemantics: 'unified-plan'})
#         self.pc.setRemoteDescription(offer)
#         self.incomingstreams.data = offer.data
#         self.incomingstreams.streams = {}
#         self.pc.addEventListener('track', (evt) => {
#             if (evt.track.kind == 'video') {
#                 var tracks = evt.streams[0].getVideoTracks()
#                 console.log(evt.track)
#                 console.log(tracks)
#                 for (const [peerid, trackid] of Object.entries(self.incomingstreams.data)) {
#                     var track = tracks.find(t => t.id === trackid)
#                     self.incomingstreams.streams[peerid] = new MediaStream([track])
#                 }
#                 console.log(self.incomingstreams)

#                 self.dispatchEvent(new CustomEvent('incomingstreams', {detail:self.incomingstreams.streams}))
#             } else {
#                 console.log('audio track received')
#             }
#         })

#         self.pc.createAnswer().then((answer)  => {
#             return self.pc.setLocalDescription(answer)
#         }).then(()  =>  {
#             var answer = self.pc.localDescription
#             var msg = {
#                 'type' : 'RTC_answer', 'message': {
#                     sdp: answer.sdp,
#                     type: answer.type
#                 }
#             }
#             var request = JSON.stringify(msg)
#             self.websocket.send(request)
#         })
#     }

    def close(self):
        self.websocket.close()
        #self.pc_close()
    

#     pc_close(){
#         if(self.pc){
#             if(self.pc.connectionState != 'closed'){
#                 if (self.pc.getTransceivers) {
#                     self.pc.getTransceivers().forEach(function(transceiver) {
#                         if (transceiver.stop) {
#                             transceiver.stop()
#                         }
#                     })
#                 }
#             // close local audio / video
#             self.pc.getSenders().forEach(function(sender) {
#                 if(sender.track){
#                     sender.track.stop()
#                 }
#             })

#             self.pc.close()


    def properties(self):
        d = {}
        if(self.project_id):
            d['project_id'] = self.project_id
        
        if(self.name):
            d['name'] = self.name
        
        if(self.has_videostream):
            d['has_videostream'] = self.has_videostream
        

        if(self.gets_videostreams):
            d['gets_videostreams'] = self.gets_videostreams
        
        if(self.subscribers):
            d["subscribers"] = self.subscribers
        
        return d
    

    async def createServerConnection(self):
        msg = {
            'type' : 'init', 'message': self.properties()
        }
        if(self.has_videostream):
            #self.pc =  new RTCPeerConnection({sdpSemantics: 'unified-plan'})
            if(self.videostream):
                pass # get stream
                # for each track
                    #self.pc.addTrack(track, self.videostream)
                # create offer .. 


        # return new Promise((done)  => {
        #     if(self.has_videostream){

        #         self.pc =  new RTCPeerConnection({sdpSemantics: 'unified-plan'})
        #         if(self.videostream){
        #             // Get tracks and send offer
        #             self.videostream.getTracks().forEach((track) => {
        #                 self.pc.addTrack(track, self.videostream)
        #             })
        #             return self.pc.createOffer().then((offer)  => {
        #                 return self.pc.setLocalDescription(offer)
        #             }).then(()  =>  {
        #                 return new Promise((resolve)  => {
        #                     if (self.pc.iceGatheringState === 'complete') {
        #                         resolve()
        #                     } 
        #                     else {
        #                         function checkState() {
        #                             if (self.iceGatheringState === 'complete') {
        #                                 self.removeEventListener('icegatheringstatechange', checkState)
        #                                 resolve()
        #                             }
        #                         }
        #                         self.pc.addEventListener('icegatheringstatechange', checkState)
        #                     }
        #                 })
        #             }).then(()  =>  {
                       
                       # offer = self.pc.localDescription
                    #     msg['message']['RTC_offer'] = {
                    #         sdp: offer.sdp,
                    #         type: offer.type
                    #     }

                    #     self.addEventListener('RTC_answer', (answer) => {
                            
                    #         self.pc.setRemoteDescription(answer.detail)
                    #     }, {once: true })
                    #     done()
                    # })
                
        else:
            print("No stream to send")
       
        request = json.dumps(msg)
        await self.websocket.send(request)


    def on_init_confirmation(self, infos):
        self.name = infos['name']
        self.id = infos['id']
        self.status = infos['status']
        self.project_id = infos['connected_to']
        self.emit('connected')
    

    def update(self, infos):
        self.name = infos['name']
        self.id = infos['id']
        self.project_id = infos['connected_to']
        self.status = self.updateConnectionStatus(infos['status'])
    

    def updateConnectionStatus(self, status):
        if(self.status != status):
            if(self.project_id):
                self.emit('connection_status_change', {'status' : status, 'project_id' : self.project_id})
        return status

    def onProjectInfo(self, infos):
        #todo snapshot 
        if('recording' in self.project_info):
            if(infos['recording'] != self.project_info['recording']):
                if (infos.recording):
                    self.emit('project_recording_start')  
                else:
                    self.emit('project_recording_stop')

        
        self.project_info['recording'] = infos['recording']

        for i, peer in self.peers.items():
            if not peer['id'] in [session['id'] for session in infos.session.values()]: # check if session still exist
                self.emit('peer_connection_end', peer)
                del self.peers[peer.id]
            
        
        for i, session in infos.sessions:
            if(session['id'] != self.id):
                if not session['id'] in [peer.id for peer in self.peers.values()]: # check for new session
                    self.emit('peer_connection_start', session)
                    self.peers[session['id']] = session
    

    def query_all_units(self):
        msg = {
            'type': 'unit_list_request',
            'message': ''
        }
        request = JSON.stringify(msg)
        self.websocket.send(request)
    

    def unitConnectionRequest(self, project_id, unit_id):
        msg_content = {
            'project_id' : project_id,
            'unit_id' : unit_id
        }
        msg = {
            'type' : 'project_unit_connect_request',
            'message': msg_content
        }
        request = JSON.stringify(msg)
        self.websocket.send(request)

        # @self.once('webclient_unit_connect_response')
        # def handleConnectionReponse()
        # self.addEventListener("webclient_unit_connect_response", (response) => {
        #     self.handleConnectionReponse(response.detail)
        # }, {once: true })
    

    def unitDisconnectionRequest(self, project_id, unit_id):
        msg_content = {
            'project_id' : project_id,
            'unit_id' : unit_id
        }
        msg = {
            'type' : 'project_unit_disconnect_request',
            'message': msg_content
        }

        request = JSON.stringify(msg)
        self.websocket.send(request)

        # self.addEventListener("webclient_unit_disconnect_response", (response) => {
        #     self.handleDisonnectionReponse(response.detail)
        # }, {once: true})
    

    def publishEvent(self, topic, options={}):
        msg_content = {
            'options': options,
            'topic': topic
        }

        msg = {
            'type' : 'unit_event',
            'message': msg_content,
        }

        request = json.dumps(msg)
        self.websocket.send(request)



