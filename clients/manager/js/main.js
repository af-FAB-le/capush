import {CapushManager} from '../../classes.mjs';
var client_properties = {"has_screen": true, "has_trigger": true, "location": undefined, "has_camera": false}; 
var tags = []; // TODO figure out what to do with them tags

var ws = new WebSocket("ws://localhost:8001/");
console.log("Waiting for websocket connection")
ws.addEventListener("open", ({ data }) => {
	var client = new CapushManager(new WebSocket("ws://localhost:8001/"), "clara");

	// maybe nicer way to do this but I' m  not a JS pro
	client.addEventListener("newUnitSession", function(event){
		window.dispatchEvent(new CustomEvent('newUnitSession', {detail: event.detail}));
	});

	client.addEventListener("closingSession", function(event){
		window.dispatchEvent(new CustomEvent('closingSession', {detail: event.detail}));
	});

	window.addEventListener('beforeunload', function(){
		client.closeAllSessions();
	});

	window.addEventListener('unitConnectionRequest', function(event){
		client.unitConnectionRequest(event.detail.unit_id);
	});

	window.addEventListener('unitDisconnectionRequest', function(event){
		if(event.detail.unit_id == 'all'){
			client.closeAllSessions();
		}
		else{
			client.closeSession(event.detail.unit_id)
		}
	});

	window.addEventListener('trigger_picture', function(event){
		client.publishEvent('trigger_picture', options = {sourceUnits : event.detail.sourceUnits});
	});
})