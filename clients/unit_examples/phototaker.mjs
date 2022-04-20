#!/usr/bin/env node
import {CapushClient} from './../classes.mjs';
import WebSocket from 'ws'
var clientproperties = {'unit_name': 'phototaker', 
	"has_screen": false,
	"has_trigger": false,
	"location": undefined,
	"has_camera": false}

var client = new CapushClient(new WebSocket("ws://localhost:8001/"));
client.addEventListener("connected", () => {
	console.log("Hey I'm "+ client.name + ", I do nothing " );
})

// Attach capture source
client.addEventListener("trigger_picture", (event) => {
	console.log("Hey I'm "+ client.name + ", triggering capture" );
	// trigger picture
	//save and send
	//client.publish_file("picture")
})

client.addEventListener("start_record", (event) => {
	console.log("Hey I'm "+ client.name + ", starting record" );
})

client.addEventListener("stop_record", (event) => {
	console.log("Hey I'm "+ client.name + ", ending record" );
})
