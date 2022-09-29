import logging
import json, os
from datetime import datetime

from flask import Blueprint
from flask import current_app
from flask import request
from flask import Response
from flask import jsonify

from pywebpush import webpush, WebPushException

from subscription_db import *

notify_bp = Blueprint('notify', __name__)

DER_BASE64_ENCODED_PRIVATE_KEY_FILE_PATH = os.path.join(os.getcwd(),"private_key.txt")
DER_BASE64_ENCODED_PUBLIC_KEY_FILE_PATH = os.path.join(os.getcwd(),"public_key.txt")

VAPID_PRIVATE_KEY = open(DER_BASE64_ENCODED_PRIVATE_KEY_FILE_PATH, "r+").readline().strip("\n")
VAPID_PUBLIC_KEY = open(DER_BASE64_ENCODED_PUBLIC_KEY_FILE_PATH, "r+").read().strip("\n")

VAPID_CLAIMS = {
    "sub": "mailto:zborowska40@gmail.com"
}

def _notify_all_subscribers(title, body, icon = None):
    sended = 0
    icon_path = "assets/{}".format(icon) if icon is not None else ""
    for sub in USER_SUBSCRIPTION_STORAGE:
        try:
            webpush(
                subscription_info=sub.subscription_info_json(),
                data=json.dumps({
                    "notification": {
                        "title": title,
                        "body": body,
                        "icon": icon_path,
                    }
                }),
                vapid_private_key=VAPID_PRIVATE_KEY,
                vapid_claims=VAPID_CLAIMS
            )
            count += 1
        except WebPushException as ex:
            pass
    print("{} notification(s) sent".format(sended))

@notify_bp.route("/subscription/", methods=["GET", "POST"])
def subscription():
    """
        POST creates a subscription
        GET returns vapid public key which clients uses to send around push notification
    """

    if request.method == "GET":
        return Response(response=json.dumps({"public_key": VAPID_PUBLIC_KEY}),
            headers={"Access-Control-Allow-Origin": "*"}, content_type="application/json")

    subscription_token = request.get_json("subscription_token")

    add_new_subscription(subscription_token)

    print("Database Size:", len(USER_SUBSCRIPTION_STORAGE))
    for sub in USER_SUBSCRIPTION_STORAGE:
        print(sub)

    return Response(status=201, mimetype="application/json")

@notify_bp.route("/push_v2/",methods=['GET'])
def push_v2():
    count = 0
    for sub in USER_SUBSCRIPTION_STORAGE:
        try:
            print(sub)
            webpush(
                subscription_info=sub.subscription_info_json(),
                data=json.dumps({
                    "notification": {
                        "title": "Angular News",
                        "body": "Newsletter Available!",
                        "icon": "assets/dishwasher_white.png",
                        "vibrate": [100, 50, 100],
                        "data": {
                            "dateOfArrival": 1664386861,
                            "primaryKey": 1
                        },
                        "actions": [{
                            "action": "explore",
                            "title": "Go to the site"
                        }]
                    }
                }),
                vapid_private_key=VAPID_PRIVATE_KEY,
                vapid_claims=VAPID_CLAIMS
            )
            count += 1
            print("webpush success")
        except WebPushException as ex:
            print("webpush fail")
    
    print("{} notification(s) sent".format(count))
    # return "{} notification(s) sent".format(count)
    return jsonify({'notification(s) sent': count})

def broadcast_notification_action_start(program_estimated_runtime):
    _notify_all_subscribers(
        "Neues Programm gestartet...",
        "{:.1f} minuten erwartete Laufzeit".format(program_estimated_runtime / 60),
        "dishwasher_action_start.png"
    )

def broadcast_notification_action_finish(program_runtime):
    _notify_all_subscribers(
        "Spülprogramm beendet!",
        "Programm nach {:.0f} minuten erfolgreich beendet".format(program_runtime / 60),
        "dishwasher_action_finish.png"
    )
