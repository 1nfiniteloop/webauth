
$(document).ready(function() {
    websocket.init();
});


var websocket = {
    socket: null,

    init: function() {
        if (location.protocol == "https:")
        {
            var protocol = "wss://";
        }
        else
        {
            var protocol = "ws://";
        }
        var url = protocol + location.host + "/auth/websocket";
        this.socket = new WebSocket(url);
        this.socket.onopen = this.onOpen;
        this.socket.onclose = this.onClose;
        this.socket.onerror = this.onError;
        this.socket.onmessage = this.onMessage;
    },

    onOpen: function(event) {
        $('#status').text("CONNECTED").addClass("connected");
    },

    onClose: function(event) {
        $('#status').text("DISCONNECTED").removeClass("connected");
    },

    onError: function(event) {
        $('#status').text("ERROR");
        console.log("Error: ", event);
    },

    onMessage: function(event) {
        message.received(JSON.parse(event.data));
    },

    send: function(msg) {
        this.socket.send(JSON.stringify(msg));
    }
};

var message = {

    received: function(msg) {
        console.log("Request received: \"" + msg.id + "\" type: " + msg.type);
        if (msg.type == "authorization_request") {
            this.onAuthorizationRequest(msg);
        } else if (msg.type == "authorization_update") {
            this.onAuthorizationUpdate(msg);
        } else if (msg.type == "error") {
            console.log("Error received: ", msg.error_text);
        } else {
            console.log("Unknown request received: ", msg);
        }
    },

    onAuthorizationRequest: function(msg) {
        var node = $('<div/>').attr("id", "message-" + msg.id).html(
            "<b>" + msg.unix_account_name + "@" + msg.hostname + "</b> requests authorization for: <b>" + msg.service_name + "</b>"
        ).addClass("message");

        // TODO break out button, else we have circular dependencies to websocket
        var approve_btn = $('<button/>').text("Approve").click({'onStateApproved': this.onStateApproved }, function(event) {
            websocket.send({
                "type": "authorization_response",
                "id": msg.id,
                "state": "AUTHORIZED"
            });
            event.data.onStateApproved(msg);
        });

        var reject_btn = $('<button/>').text("Reject").click({'onStateRejected': this.onStateRejected }, function(event) {
            websocket.send({
                "type": "authorization_response",
                "id": msg.id,
                "state": "UNAUTHORIZED"
            });
            event.data.onStateRejected(msg);
        });

        node.append(approve_btn, reject_btn);
        $("#messages").append(node);
    },

    onAuthorizationUpdate: function(msg) {
        if (msg.state == "EXPIRED")
        {
            this.onStateExpired(msg);
        }
    },

    onStateApproved: function(msg) {
        $("#message-" + msg.id).addClass("approved").fadeOut("slow", function() {
            $( this ).remove();
        });
    },

    onStateRejected: function(msg) {
        $("#message-" + msg.id).addClass("rejected").fadeOut("slow", function() {
            $( this ).remove();
        });
    },

    onStateExpired: function(msg) {
        $("#message-" + msg.id).addClass("expired").fadeOut("slow", function() {
            $( this ).remove();
        });
    }
};