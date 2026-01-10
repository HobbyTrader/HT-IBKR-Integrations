import json
from datetime import time

class TimeEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, time):
            return obj.isoformat()
        return super().default(obj)