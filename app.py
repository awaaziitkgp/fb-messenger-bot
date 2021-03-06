import os
import sys
import json

import requests
from flask import Flask, request

app = Flask(__name__)


@app.route('/', methods=['GET'])
def verify():
    # when the endpoint is registered as a webhook, it must echo back
    # the 'hub.challenge' value it receives in the query arguments
    if request.args.get("hub.mode") == "subscribe" and request.args.get("hub.challenge"):
        if not request.args.get("hub.verify_token") == os.environ["VERIFY_TOKEN"]:
            return "Verification token mismatch", 403
        return request.args["hub.challenge"], 200

    return "Hello world", 200


@app.route('/', methods=['POST'])
def webhook():

    # endpoint for processing incoming messaging events
    add_persistent_menu()

    data = request.get_json()
    log(data)  # you may not want to log every incoming message in production, but it's good for testing

    if data["object"] == "page":

        for entry in data["entry"]:
            for messaging_event in entry["messaging"]:

                if messaging_event.get("message"):  # someone sent us a message

                    sender_id = messaging_event["sender"]["id"]        # the facebook ID of the person sending you the message
                    recipient_id = messaging_event["recipient"]["id"]  # the recipient's ID, which should be your page's facebook ID
                    message_text = messaging_event["message"]["text"]  # the message's text

                    send_message(sender_id, "got it, thanks!")



                if messaging_event.get('postback'):
                        payload_text = messaging_event["postback"][
                            "payload"]  # the payload's text
                        if payload_text == 'DEV_ISSUE':
                            
                            try:
                                msg = "Don't worry"
                            except KeyError:
                                msg = "Please tell me what your issue is."
                            send_message(messaging_event["sender"]["id"], msg)
                            



                if messaging_event.get("delivery"):  # delivery confirmation
                    pass

                if messaging_event.get("optin"):  # optin confirmation
                    pass

                if messaging_event.get("postback"):  # user clicked/tapped "postback" button in earlier message
                    pass

    return "ok", 200


def send_message(recipient_id, message_text):

    log("sending message to {recipient}: {text}".format(recipient=recipient_id, text=message_text))

    params = {
        "access_token": os.environ["PAGE_ACCESS_TOKEN"]
    }
    headers = {
        "Content-Type": "application/json"
    }
    data = json.dumps({
        "recipient": {
            "id": recipient_id
        },
        "message": {
            "text": message_text
        }
    })
    r = requests.post("https://graph.facebook.com/v2.6/me/messages", params=params, headers=headers, data=data)
    if r.status_code != 200:
        log(r.status_code)
        log(r.text)





def add_persistent_menu():
    params = {
        "access_token": os.environ["PAGE_ACCESS_TOKEN"]
    }
    headers = {
        "Content-Type": "application/json"
    }
    data = json.dumps({
                      "setting_type": "call_to_actions",
                      "thread_state": "existing_thread",
                      "call_to_actions": [
                         
                          {
                              "type": "postback",
                              "title": "Latest News",
                              "payload": "PAYLOAD_RECRUIT"
                          },
                          {
                              "type": "postback",
                              "title": "Facing some development issue",
                              "payload": "DEV_ISSUE"
                          },
                          {
                              "type": "web_url",
                              "title": "View Website",
                              "url": "http://awaaziitkgp.org/"
                          }
                      ]
                      })
    r = requests.post("https://graph.facebook.com/v2.6/me/thread_settings",
                      params=params, headers=headers, data=data)
    if r.status_code != 200:
        error_msg = "Got following error while adding persistent menu:\nStatus Code : {}\nText : {}".format(
            r.status_code, r.text)
        slack_notification(error_msg)
        log(r.status_code)
        log(r.text)










def log(message):  # simple wrapper for logging to stdout on heroku
    print str(message)
    sys.stdout.flush()


if __name__ == '__main__':
    app.run(debug=True)
