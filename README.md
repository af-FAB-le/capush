# Capush
This current state of implementation includes the basis for logging into a project and connect to one or several websocket based units. It also enable the creation of streaming units through WEBRTC, unit subscribing to streams and recording of the streams

## Websocket Server (python)
Run the Websocket server with python3 [main.py](main.py)
Run the HTTP server with python3 [httpserver.py](httpserver.py)

The server will listen to `127.0.0.1:8001` by default, these parameters can be changed in [config.json](config.json)

## Clients (javascript ES6) - library
All clients can inherit the class `CapushClient` inside [classes.mjs](clients-js/classes.mjs)
[Documentation](clients-js)

### Web-based manager
Browser based interface to connect to units is accessible through a http server running: [index.html](clients-js/manager/index.html)


### Units - Browser
Examples of units scripts can be found under [clients-js/](clients-js)
