class AbstractMiddleware:

    active_sessions = {}

    def __init__(self):
        self.view_id = None
        self.last_session_id = None
        self.last_object_id = None
        self.last_object_2d_id = None
        self.data_buffer = {}


    def generate_object_ids(self, process):
        pass