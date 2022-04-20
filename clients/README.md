# Capush Clients
Two sister classes are available as Capush clients (inheriting the same `CapushClient` class: `CapushManager` and `CapushUnit`.

Once a client object from one of these classes is instanciated, events are fired.
`client.addEventListener:`

### Events
* `connected`: on connection to the web socket server
* `error`: Fired when a error on the websocket happens 
* `close`: Fired when the socket connection is closed

* `unit_list`: event.detail contains the list of all connected units and availaibe units 

* `webclient_unit_connect_response`: Fired after a project-unit connection request

* `webclient_unit_disconnect_response`: Fired after a project-unit disconnection request

* `trigger_picture`: fired when a command to trigger picture is received

* `start_record`: fired when a command to start a video record is received

* `stop_record`: fired when a command to stop a video record is received

* ...

### Functions :

* `query_all_units()`: Will send a request to the server to get the status of all units. The server will send a `unit_list` event.

* `unitConnectionRequest(project_name, unit_id)`: Sends a request to the server to connect the project to the unit. The server will send a `webclient_unit_connect_response` event.

* `unitDisconnectionRequest(project_name, unit_id)`: Sends a request to the server to disconnect the project to the unit. The server will send a `webclient_unit_disconnect_response` event.

* `publishEvent(topic, options={})`: Publish a message to the server (WIP)

## Manager
The `CapushManager` class provide events to request connections and disconnections to units.
It provides all the above events and some additional functions: 

### Constructor: 
CapushManager(ws, projectname)

### Functions:

* `unitConnectionRequest(unit_id)`: Sends a request to the server to connect the project to the unit.

* `closeSession(unit_id)`: Sends a request to the server to close the session with unit_id.

* `closeAllSessions()`: Sends a request to the server to close all the sessions of the project.

### Example
```
import {CapushManager} from classes.mjs';
```
Create a socket client:
```
var ws = new WebSocket("ws://localhost:8001/");
```
and pass it as a paramater for the client 
```
var client = new CapushManager(ws, projectname);
```


example can be found on [main.js](manager/js/main.js)

## Units

### Constructor: 
CapushUnit(ws, {'unit_name': ''})

### Example

run [basic.mjs](clients/unit_examples/basic.mjs) using the [NPM esm module](https://www.npmjs.com/package/esm)

`> node -r esm basic.mjs`
```
#!/usr/bin/env node
import {CapushUnit} from './../classes.mjs';
import WebSocket from 'ws'
var clientproperties = {'unit_name': 'basic'}
var unit = new CapushUnit(new WebSocket("ws://localhost:8001/"), clientproperties);
unit.addEventListener("connected", () => {
	console.log("Hey I'm "+ unit.name + ", I do nothing " );
})
```
