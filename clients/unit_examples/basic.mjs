#!/usr/bin/env node
import {CapushUnit} from './../classes.mjs';
import WebSocket from 'ws'
var clientproperties = {'unit_name': 'basic'}
var unit = new CapushUnit(new WebSocket("ws://localhost:8001/"), clientproperties);
unit.addEventListener("connected", () => {
	console.log("Hey I'm "+ unit.name + ", I do nothing " );
})