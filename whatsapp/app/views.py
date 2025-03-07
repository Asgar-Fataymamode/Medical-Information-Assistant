import logging
import json 
import requests
from flask import Blueprint, request, jsonify, current_app
from .decorators.security import signature_required 

from .utils.whatsapp_utils import( process_whatsapp_message, is_valid_whatsapp_message, )

webhook_blueprint = Blueprint("webhook", __name__)


# def get_user_message_body():
#     body = request.get_json()
#     wa_id = body["entry"][0]["changes"][0]["value"]["contacts"][0]["wa_id"]
#     name = body["entry"][0]["changes"][0]["value"]["contacts"][0]["profile"]["name"]

#     message = body["entry"][0]["changes"][0]["value"]["messages"][0]
#     message_body = message["text"]["body"]
#     return message_body

    
def handle_message():
    """

    Handle incoming webhook events from the WhatsApp API.

    This function processes incoming WhatsApp messages and other events,
    such as delivery statuses. If the event is a valid message, it gets
    processed. If the incoming payload is not a recognized WhatsApp event,
    an error is returned.

    Every message send will trigger 4 HTTP requests to your webhook: message, sent, delivered, read.

    Returns:
        response: A tuple containing a JSON response and an HTTP status code.
    
    """


    body = request.get_json()

   


    #logging info 

    # check if it's a whatsapp status update 

    if (
        body.get("entry", [{}])[0]
        .get("changes", [{}])[0]
        .get("value", {})
        .get("statuses")
    ):
        logging.info("Received a WhatsApp status update.")
        return jsonify({"status":"ok"}), 200
    
    try:
        if is_valid_whatsapp_message(body) :
            process_whatsapp_message(body)
            
            return jsonify({"status":"ok"}),200
        else:
            return(
                jsonify({"status":"erro","message":"Invalid JSON provided "}), 400
                
            )
    except json.JSONDecodeError:
        logging.error("Failed to Decode JSON")
        return jsonify({"status":"error","message":"Invalid JSON provided"}), 400
    

# kinda required verification for whatsapp 
def verify():
    # Parse params from the webhook verification request
    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")
    # Check if a token and mode were sent
    if mode and token:
        # Check the mode and token sent are correct
        if mode == "subscribe" and token == current_app.config['VERIFY_TOKEN']:
            
            # Respond with 200 OK and challenge token from the request
            logging.info("WEBHOOK_VERIFIED")
            return challenge, 200
        else:
            # Responds with '403 Forbidden' if verify tokens do not match
            logging.info("VERIFICATION_FAILED")
            logging.info(f"Received token: {token}, Expected token: {current_app.config['VERIFY_TOKEN']}")
            return jsonify({"status": "error", "message": "Verification failed"}), 403
    else:
        # Responds with '400 Bad Request' if verify tokens do not match
        logging.info("MISSING_PARAMETER")
        return jsonify({"status": "error", "message": "Missing parameters"}), 400



@webhook_blueprint.route("/webhook", methods=["GET"])
def webhook_get():
    return verify()

@webhook_blueprint.route("/webhook", methods=["POST"])
@signature_required
def webhook_post():
    return handle_message()