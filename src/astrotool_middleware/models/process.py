import uuid
from datetime import datetime as dt

import models as m


class Process:
    def __init__(self, name=None):
        self.id = str(uuid.uuid4())
        self.name = name or self._default_name()
        self.rendering = m.Rendering()
        self.type = "upload"
        self.last_interaction_date = None
        self.last_object_id = None
        self.last_object_2d_id = None

    @staticmethod
    def _default_name():
        return "Project_" + dt.now().strftime("%Y-%m-%d-%H:%M:%S")