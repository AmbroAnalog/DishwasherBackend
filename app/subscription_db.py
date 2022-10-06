import json

USER_SUBSCRIPTION_STORAGE = []

def add_new_subscription(json_payload) -> bool:
    if 'endpoint' not in json_payload:
        print('json_payload for user not compatible')
        return False
    for user in USER_SUBSCRIPTION_STORAGE:
        if user.get_endpoint() == json_payload['endpoint']:
            print('...user already saved')
            return False
    USER_SUBSCRIPTION_STORAGE.append(Subscriber(json_payload))
    return True


class Subscriber(object):
    endpoint = ""
    key_auth = ""
    key_p256dh = ""

    def __init__(self, json_payload) -> None:
        self.endpoint = json_payload['endpoint']
        self.key_auth = json_payload['keys']['auth']
        self.key_p256dh = json_payload['keys']['p256dh']

    def __repr__(self) -> str:
        return json.dumps(self.subscription_info_json())

    def subscription_info_json(self) -> json:
        return {
                "endpoint": self.endpoint,
                "keys": {
                    "auth": self.key_auth,
                    "p256dh": self.key_p256dh,
                }
            }

    def get_endpoint(self) -> str:
        return self.endpoint