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
class Unit {
    constructor(args){
        this.name = args.name;
        this.id = args.id;
        this.type = args.type;
        this.last_location = args.location;
        this.location_time = args.last_location_update;
        this.status = args.status;
        this.status_time = args.last_status_update;
        this.pan = 0.0;
        this.tilt = 0.0;
        this.has_pan_tilt = false;
        this.is_bot = false;
    }
}

class CapushClient extends EventTarget{
    constructor(websocket, client_properties){
        super()
        this.websocket = websocket
        this.websocket.addEventListener('open', () => {
            this.initServerConnection(client_properties )
            console.log('Connected to websocket server.');
            this.dispatchEvent(new CustomEvent('connected'));
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

             case 'trigger_picture':  
             this.dispatchEvent(new CustomEvent('trigger_picture', {detail: event.message}));
                 break;

             case 'start_record':  
             this.dispatchEvent(new CustomEvent('start_record', {detail: event.message}));
                 break;

             case 'stop_record':  
             this.dispatchEvent(new CustomEvent('trigger_picture', {detail: event.message}));
                 break;

             default:
                 console.log(event);
                 break;
            }

        });

        this.websocket.addEventListener('error', function (error) {
         this.dispatchEvent(new CustomEvent('error', {detail: error}));
        });

        this.websocket.addEventListener('close', function(event) {
         this.dispatchEvent(new CustomEvent('close', {detail: event}));
        });

        this.name = "Default name"
        if(client_properties.unit_name){
            this.name = client_properties.unit_name;
        }
        if(client_properties.has_screen){
            this.has_screen = client_properties.has_screen;
        }
        if(client_properties.has_trigger){
            this.has_trigger = client_properties.has_trigger;
        }
        if(client_properties.location){
            this.location = client_properties.location;
        }
        if(client_properties.has_camera){
            this.has_camera = client_properties.has_camera;
        }
    }
    
    initServerConnection(client_properties){
        var msg = {
            'type' : 'init', 'message': client_properties
        }
        var request = JSON.stringify(msg);
        this.websocket.send(request);
    }

    query_all_units(){
        var msg = {
            type: 'unit_list_request',
            message: ''
        }
        var request = JSON.stringify(msg);
        this.websocket.send(request);
    }

    unitConnectionRequest(project_name, unit_id){
        var msg_content = {
            'project_name' : project_name,
            'unit_id' : unit_id
        }
        var msg = {
            'type' : 'project_unit_connect_request',
            'message': msg_content
        }
        console.log(msg)
        var request = JSON.stringify(msg);
        this.websocket.send(request);
    }

    unitDisconnectionRequest(project_name, unit_id){
        var msg_content = {
            project_name : project_name,
            unit_id : unit_id
        }
        var msg = {
            'type' : 'project_unit_disconnect_request',
            'message': msg_content
        }

        var request = JSON.stringify(msg);
        this.websocket.send(request);
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
    constructor(websocket, projectname){
        var client_properties = {}
        client_properties.client_type = 'manager';
        client_properties.project_name = projectname
        super(websocket, client_properties)
        this.projectname = projectname
        this.all_units = {};
        this.available_units = {};
        this.units = {};
        this.addEventListener("connected", () => {
            console.log("connected");
        })

        this.addEventListener("unit_list", (units) => {
            this.all_units = units.detail.all;
            this.available_units = units.detail.available;
            this.checkUnitConnections();
            console.log(this.all_units)
            window.dispatchEvent(new CustomEvent("unit_list", {detail:units.detail}));
        });

        this.addEventListener("webclient_unit_connect_response", (response) => {
            this.handleConnectionReponse(response.detail);
        });

        this.addEventListener("webclient_unit_disconnect_response", (response) => {
            this.handleDisonnectionReponse(response.detail);
        });

        this.addEventListener('error', function (error) {
            console.log('Error connecting to websocket server: ', error.detail);
            this.closeAllSessions();
        });

        this.addEventListener('close', function(event) {
            console.log('Connection to websocket server closed.', event.detail);
            this.closeAllSessions();
        });

    }

    unitDisconnectionRequest(unit_id){
        super.unitDisconnectionRequest(this.projectname, unit_id)
    }

    unitConnectionRequest(unit_id){
        super.unitConnectionRequest(this.projectname, unit_id)
    }

    handleDisonnectionReponse(e){
        if(e.accepted == 1){
            console.log("Connection ended, server says:"+e.msg);
        }else{
            console.log("Disonnection refused, server says:"+e.msg);
        }
    }

    handleConnectionReponse(e){
        if(e.accepted == 1){
            console.log("Connection accepted, server says:"+e.msg);
            if (this.beginSession(e.unit_id)){
                this.dispatchEvent(new CustomEvent('newUnitSession', {detail: this.units[e.unit_id]}));
            }
            else{
                console.log("Connexion failed");
                this.unitDisconnectionRequest(e.unit_id);
            }
        }else{
            console.log("Connection refused, server says:"+e.msg);
        }
    }

    beginSession(unit_id){
        var unit = new Unit(this.all_units[unit_id]);
        unit.id = unit_id;
        this.units[unit_id] = unit; // handling sessions as well
        return true;
    }

    removeConnection(unit_id){
        delete this.units[unit_id];
        this.dispatchEvent(new CustomEvent('closingSession', {detail:unit_id}));
    }

    closeSession(unit_id){
        this.unitDisconnectionRequest( unit_id);
        this.removeConnection(unit_id)
        console.log("closing session " + unit_id);
    }

    closeAllSessions(){
        console.log(this.units);
        var unit_ids = Object.keys(this.units);

        for (const i in unit_ids) {
            var elem = unit_ids[i]
            this.closeSession(elem);
        };
    }

    checkUnitConnections(){ // check if the units used in session are still connected 
        var unit_ids = Object.keys(this.units);
        for (const i in unit_ids) {
            var elem = unit_ids[i]
            if(!(elem in this.all_units)){
                console.log("Unit: "+elem+" disconnected from server, ending session");
                this.removeConnection(elem);
            }
        } 
    }
}

class CapushUnit extends CapushClient{
    constructor(websocket, client_properties = {}){
        client_properties.client_type = 'unit';
        super(websocket, client_properties)
    }
}
export {CapushClient, CapushManager, CapushUnit}
