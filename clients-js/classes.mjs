class CustomEvent extends Event { 
  constructor(message, data = undefined) {
    super(message, data)
    if(data){
        this.detail = data.detail
    }
    else{
        this.detail = undefined
    }
  }
}

import json from '../config.json' assert {type: 'json'};
//import("foo.json", { assert: { type: "json" } });
class CapushClient extends EventTarget{
    constructor(args){
        super()
        if(!json[0]){
            console.error("config file missing")
        }

        this.websocket = new WebSocket("ws://"+json[0]['websocket-server-address']+":"+ json[0]['websocket-server-port'])
        this.project_info = {}
        this.peers = {}
        this.pc;
        this.incomingstreams = {data:{}, streams:{}}
        this.subscribers = []
        if(args){
            this.name = args.name;
            this.gets_videostreams = Boolean(args.gets_videostreams);
            this.has_videostream = args.stream != undefined;
            this.videostream = args.stream;
            this.project_id = args.project_id;
            this.subscribers = args.subscribers ?  args.subscribers : []
        }


        if(this.gets_videostreams && !this.subscribers.find(e => e === 'projectState')){
            this.subscribers.push('projectState')
        }
        
        this.websocket.addEventListener('open', () => {
            this.createServerConnection()
        });

        this.websocket.addEventListener("message", ({ data }) => {
            const event = JSON.parse(data);
            switch (event.type) {

             case "unit_list":
                this.dispatchEvent(new CustomEvent('unit_list', {detail: event.message}));
                break;

             case 'webclient_unit_connect_response':
                this.dispatchEvent(new CustomEvent('webclient_unit_connect_response', {detail: event.message}));
                break;

             case 'webclient_unit_disconnect_response':  
                this.dispatchEvent(new CustomEvent('webclient_unit_disconnect_response', {detail: event.message}));
                break;

             case "project_info":
                this.onProjectInfo(event.message)
                break;

             case "unit_info":
                this.update(event.message)
                this.dispatchEvent(new CustomEvent('unit_info', {detail: event.message}));
                break;

            case 'RTC_answer':
                this.dispatchEvent(new CustomEvent('RTC_answer', {detail: event.message}));
                break;

            case 'init_confirmation':
                this.on_init_confirmation(event.message);
                this.dispatchEvent(new CustomEvent('unit_info', {detail: event.message}));
                break;        

            case 'snapshot':
                this.dispatchEvent(new CustomEvent('snapshot'));
                break;        

            case 'recording_status':
                this.dispatchEvent(new CustomEvent('recording_status', {detail: event.message}));
                break;            

            case 'RTC_offer':
                this.onRTCOffer(event.message); 
                break;
             default:
                 console.log(event);
                 break;
            }
        });

        this.websocket.addEventListener('error', (event) => {
         this.dispatchEvent(new CustomEvent('error', {detail: error}));
        });

        this.websocket.addEventListener('close', (event) => {
            this.pc_close()
            this.dispatchEvent(new CustomEvent('socketclose', {detail: event}));
            console.error('Connection to server lost')
        });
    }
    
    onRTCOffer(offer){
        this.pc = new RTCPeerConnection({sdpSemantics: 'unified-plan'});
        this.pc.setRemoteDescription(offer)
        this.incomingstreams.data = offer.data
        this.incomingstreams.streams = {}
        this.pc.addEventListener('track', (evt) => {
            if (evt.track.kind == 'video') {
                var tracks = evt.streams[0].getVideoTracks()
                console.log(evt.track)
                console.log(tracks)
                for (const [peerid, trackid] of Object.entries(this.incomingstreams.data)) {
                    var track = tracks.find(t => t.id === trackid)
                    this.incomingstreams.streams[peerid] = new MediaStream([track])
                }
                console.log(this.incomingstreams)

                this.dispatchEvent(new CustomEvent('incomingstreams', {detail:this.incomingstreams.streams}))
            } else {
                console.log('audio track received')
            }
        });

        this.pc.createAnswer().then((answer)  => {
            return this.pc.setLocalDescription(answer);
        }).then(()  =>  {
            var answer = this.pc.localDescription;
            var msg = {
                'type' : 'RTC_answer', 'message': {
                    sdp: answer.sdp,
                    type: answer.type
                }
            }
            var request = JSON.stringify(msg);
            this.websocket.send(request);
        })
    }

    close(){
        this.websocket.close()
        this.pc_close()
    }

    pc_close(){
        if(this.pc){
            if(this.pc.connectionState != 'closed'){
                if (this.pc.getTransceivers) {
                    this.pc.getTransceivers().forEach(function(transceiver) {
                        if (transceiver.stop) {
                            transceiver.stop();
                        }
                    });
                }
            // close local audio / video
            this.pc.getSenders().forEach(function(sender) {
                if(sender.track){
                    sender.track.stop();
                }
            });

            this.pc.close();
                
            }

        }
    }

    properties(){
        var d = {}
        if(this.project_id){
            d['project_id'] = this.project_id
        }
        if(this.name){
            d['name'] = this.name
        }
        if(this.has_videostream){
            d['has_videostream'] = this.has_videostream
        }

        if(this.gets_videostreams){
            d['gets_videostreams'] = this.gets_videostreams
        }
        if(this.subscribers){
            d["subscribers"] = this.subscribers
        }
        return d;
    }

    createServerConnection(){
        var msg = {
            'type' : 'init', 'message': this.properties()
        }
        return new Promise((done)  => {
            if(this.has_videostream){

                this.pc =  new RTCPeerConnection({sdpSemantics: 'unified-plan'});
                if(this.videostream){
                    // Get tracks and send offer
                    this.videostream.getTracks().forEach((track) => {
                        this.pc.addTrack(track, this.videostream);
                    });
                    return this.pc.createOffer().then((offer)  => {
                        return this.pc.setLocalDescription(offer);
                    }).then(()  =>  {
                        return new Promise((resolve)  => {
                            if (this.pc.iceGatheringState === 'complete') {
                                resolve();
                            } 
                            else {
                                function checkState() {
                                    if (this.iceGatheringState === 'complete') {
                                        this.removeEventListener('icegatheringstatechange', checkState);
                                        resolve();
                                    }
                                }
                                this.pc.addEventListener('icegatheringstatechange', checkState);
                            }
                        });
                    }).then(()  =>  {
                        var offer = this.pc.localDescription;
                        msg['message']['RTC_offer'] = {
                            sdp: offer.sdp,
                            type: offer.type
                        }

                        this.addEventListener('RTC_answer', (answer) => {
                            
                            this.pc.setRemoteDescription(answer.detail);
                        }, {once: true })
                        done()
                    })
                }

                else{
                    console.log("No stream to send")
                    done()
                }
            }
            else{
                done()
            }
        }).then(()  =>  {            
            var request = JSON.stringify(msg);
            this.websocket.send(request);
        });
    }

// Client life events

    on_init_confirmation(infos){
        this.name = infos.name
        this.id = infos.id
        this.status = infos.status
        this.project_id = infos.connected_to
        this.dispatchEvent(new CustomEvent('connected'));       
    }

    update(infos){
        this.name = infos.name
        this.id = infos.id
        this.project_id = infos.connected_to
        this.status = this.updateConnectionStatus(infos.status)
    }

    updateConnectionStatus(status){
        if(this.status != status){
            if(this.project_id){
                console.log("I am connected to " + this.project_id)
                this.dispatchEvent(new CustomEvent('connection_status_change', {detail: {'status': status, 'project_id': this.project_id}}));  
            }
        }
        return status
    }

    onProjectInfo(infos){
        //todo snapshot 
        if(this.project_info.recording){
            if(infos.recording != this.project_info.recording){
                if (infos.recording){
                    this.dispatchEvent(new CustomEvent('project_recording_start'));  
                }else{
                    this.dispatchEvent(new CustomEvent('project_recording_stop'));  
                }
            }
        }
        this.project_info.recording = infos.recording

        Object.values(this.peers).forEach((peer, i) => {
            if (!infos.sessions.find( session => session.id === peer.id)){ // check if session still exist
                this.dispatchEvent(new CustomEvent('peer_connection_end', {detail:peer}));  
                delete this.peers[peer.id]
            }
        })

        infos.sessions.forEach((session) =>{
            if(session.id != this.id){
                if(!Object.values(this.peers).find(peer => peer.id === session.id)){ // check for new session
                    this.dispatchEvent(new CustomEvent('peer_connection_start', {detail:session}));  
                    this.peers[session.id] = session
                }
            }
        })
    }

    query_all_units(){
        var msg = {
            type: 'unit_list_request',
            message: ''
        }
        var request = JSON.stringify(msg);
        this.websocket.send(request);
    }

    unitConnectionRequest(project_id, unit_id){
        var msg_content = {
            'project_id' : project_id,
            'unit_id' : unit_id
        }
        var msg = {
            'type' : 'project_unit_connect_request',
            'message': msg_content
        }
        var request = JSON.stringify(msg);
        this.websocket.send(request);

        this.addEventListener("webclient_unit_connect_response", (response) => {
            this.handleConnectionReponse(response.detail);
        }, {once: true })
    }

    unitDisconnectionRequest(project_id, unit_id){
        var msg_content = {
            project_id : project_id,
            unit_id : unit_id
        }
        var msg = {
            'type' : 'project_unit_disconnect_request',
            'message': msg_content
        }

        var request = JSON.stringify(msg);
        this.websocket.send(request);

        this.addEventListener("webclient_unit_disconnect_response", (response) => {
            this.handleDisonnectionReponse(response.detail);
        }, {once: true})
    }

    publishEvent(topic, options={}){
        var msg_content = {
            'options': options,
            'topic': topic
        }

        var msg = {
            'type' : 'unit_event',
            'message': msg_content,
        }

        var request = JSON.stringify(msg);
        this.websocket.send(request);
    }
}

class CapushManager extends CapushClient{
    constructor(args){
        if(! args.subscribers){
            args.subscribers = []
        }
        args.subscribers.push('globalState')

        super(args)
        
        this.all_units = {};
        this.available_units = {};
        this.peers = {};
        this.addEventListener("connected", () => {
            console.log("connected");
        })

        this.addEventListener("unit_list", (units) => {
            this.all_units = units.detail.all;
            this.available_units = units.detail.available;
            this.checkUnitConnections();
        });

        this.addEventListener('error', function (error) {
            console.error('Error connecting to websocket server: ', error.detail);
            this.closeAllSessions();
        });

        this.addEventListener('close', function(event) {
            console.log('Connection to websocket server closed.', event.detail);
            this.closeAllSessions();
        });
    }

    unitDisconnectionRequest(unit_id){
        if(unit_id){
            super.unitDisconnectionRequest(this.project_id, unit_id)
        }else{
            console.error('unit_id undefined')
        }
    }

    unitConnectionRequest(unit_id){
        if(unit_id){
            super.unitConnectionRequest(this.project_id, unit_id)
        }else{
            console.error('unit_id undefined')
        }
    }

    handleDisonnectionReponse(e){
        if(e.accepted == 1){
            console.log("Connection ended, server says:"+e.msg);
        }else{
            console.error("Disonnection refused, server says:"+e.msg);
        }
    }

    handleConnectionReponse(e){
        if(e.accepted == 1){
            console.log("Connection accepted, server says:"+e.msg);
        }else{
            console.error("Connection refused, server says:"+e.msg);
        }
    }

    closeSession(unit_id){
        if(unit_id){
            this.unitDisconnectionRequest( unit_id);
            console.log("closing session " + unit_id);
        }else{
            console.error('unit_id undefined')
        }
    }

    closeAllSessions(){
        var unit_ids = Object.keys(this.peers);
        for (const i in unit_ids) {
            var elem = unit_ids[i]
            this.closeSession(elem);
        };
    }

    close(){
        super.close()
    }
    
    checkUnitConnections(){ // check if the units used in session are still connected 
        var unit_ids = Object.keys(this.peers);
        for (const i in unit_ids) {
            var elem = unit_ids[i]
            if(!(elem in this.all_units)){
                console.log("Unit: "+elem+" disconnected from server, ending session");
            }
        } 
    }
}
export {CapushClient, CapushManager}
