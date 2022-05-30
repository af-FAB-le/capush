# JavaScript library for capush clients - [classes.mjs](classes.mjs)

## CapushClient ([EventTarget](https://developer.mozilla.org/fr/docs/Web/API/EventTarget))
Two classes are available as Capush clients :`CapushClient` and `CapushManager`.

Once a client object from one of these classes is instanciated, events are fired.
`client.addEventListener:`

### Constructor: 
CapushClient( **[WebSocket](https://developer.mozilla.org/fr/docs/Web/API/WebSocket)** ws, **[Object](https://developer.mozilla.org/fr/docs/Web/JavaScript/Reference/Global_Objects/Object)** args)

**args:**
{
 
`name`: [`String`](https://developer.mozilla.org/fr/docs/Web/JavaScript/Reference/Global_Objects/String) 
if defined, the client will be attached to the project and not made available to others to connect

`project_id`: [`String`](https://developer.mozilla.org/fr/docs/Web/JavaScript/Reference/Global_Objects/String)
 if defined, the client will be attached to the project and not made available to others to connect

`gets_streams`: [`Boolean`](https://developer.mozilla.org/fr/docs/Web/JavaScript/Reference/Global_Objects/Boolean)
if defined, the server will create a [RTCPeerConnection](https://developer.mozilla.org/fr/docs/Web/API/RTCPeerConnection) to stream the content of the current streaming clients connected to the same project
**//Note//:** when using this parameter, the client subscribes to `projectState`

`stream`: [`MediaStream`](https://developer.mozilla.org/fr/docs/Web/API/MediaStream)
if defined, the client will create a [RTCPeerConnection](https://developer.mozilla.org/fr/docs/Web/API/RTCPeerConnection) to stream the content of connected camera clients
Note: when using this parameters, the client will also fire `snapshot`, `record_started` and `record_ended` events.

`subscribers`: `Array` of keywords :
 - `'globalState'` to subscribe to the activties on the unit connections of the whole ecosystem
 - `'projectState'` to subscribe to the activties on the current connected project
}

### [Events](https://developer.mozilla.org/fr/docs/Web/API/Event)
* `connected`: on connection to the server done
* `error`: Fired when a error on the websocket happens 
* `close`: Fired when the socket connection is closed
* `webclient_unit_connect_response`: Fired after a project-client connection request
* `webclient_unit_disconnect_response`: Fired after a project-client disconnection request
* `unit_info`: event.detail contains info on the state of this current client-unit
* `connection_status_change`: 
- event.detail.status: Int of value 1 if the client is not connected to any project, else 2
- event.detail.project_id: Contains the id of the project or *Null*

**`globalState` events**
Events fired is the `subscriber` parameter is set to `'globalState'`
* `unit_list`: If subscriber set to `globalState`, event.detail contains the list of all connected clients and availaibe clients 

**`projectState` and `globalState` events**
Events fired is the `subscriber` parameter is set to `'globalState'` or `'projectState'`

* `project_info:` If subscriber set to `globalState` or `projectState`. event.detail contains info on the state of the current project connected to the client

* `project_recording_start`: project started recording from the connected streaming clients
* `project_recording_stop`: project started recording from the connected streaming clients

* `peer_connection_start`: A new client is connected to the project event.detail contains the client information

* `peer_connection_stop`: A client disconnected from the project event.detail contains the client information

**`stream` events**
These events are fired when the client is sending a video stream
* `snapshot` If client has `stream`, when a snapshot is taken from this source
* `recording_start` If client has `stream`, when a record from this source is started 
* `recording_stop` If client has `stream`, when a record from this source is ended

### Functions :

* `query_all_units()`: Will send a request to the server to get the status of all clients. The server will send a `unit_list` event.

* `unitConnectionRequest(project_name, unit_id)`: Sends a request to the server to connect the project to the desired client. The server will send a `webclient_unit_connect_response` event.

* `unitDisconnectionRequest(project_name, unit_id)`: Sends a request to the server to disconnect the project from a connected client. The server will send a `webclient_unit_disconnect_response` event.

* `publishEvent(topic, options={})`: Publish a message to the server (WIP)

* `close()`: to call before ending the program (beforeUnload)

### Examples
* [webcam](webcam_unit.html)
* [buttons](button_unit.html)
* [clara's project webcam](webcam_owned_unit.html)
* [clara's project screen](screen_owned_unit.html)

## CapushManager (CapushClient)
The `CapushManager` class provides events to request connections and disconnections to client-units.
It provides all the features from `CapushClient` with some additional functions enabling the managment of connections from a project to the different client-units: 

### Constructor: 
CapushManager(ws, properties)

### Functions (in addition to the CapushClient's ones):

* `unitConnectionRequest(unit_id)`: Sends a request to the server to connect the project to the client.

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

example can be found on the manager example [index.html](manager/js/index.html)
