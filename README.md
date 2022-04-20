# Capush
This current state of implementation includes the basis for logging into a project and connect to one or several websocket based units.

## Websocket Server (python)
Run the Websocket server with python3 [server.py](server.py)

The server will listen to `127.0.0.1:8001` by default, these parameters can be changer in [config.json](config.json)

## Clients (javascript ES6)
All clients can inherit the class `CapushClient` inside [classes.mjs](clients/classes.mjs)

More details on how to develop new clients types under [clients](clients)
### Web-based manager
Browser based interface to connect to units is accessible through a http server running: [index.html](clients/manager/index.html)


### Units
Examples of units scripts can be found under [clients/unit_examples](clients/unit_examples)

Run it with the esm module for node:
`> node -r esm basic.mjs`
