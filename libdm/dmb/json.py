import json


class JSONEncoder(json.JSONEncoder):
    def default(self, o):
        try:
            return o.__json__()
        except:
            return json.JSONEncoder.default(self, o)
