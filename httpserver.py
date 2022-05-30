from bottle import get, run, static_file
import json

@get('/capush/<filepath:path>')
def capush_web(filepath) :
    return static_file(filepath, root = 'clients-js')
     
@get('/<filepath:path>')
def capush_web(filepath) :
    return static_file(filepath, root = '')

with open('config.json') as json_file:
    data = json.load(json_file)
    http_server_address = data[0]['http-server-address']
    http_server_port = data[0]['http-server-port']
run(host=http_server_address, port=http_server_port)

