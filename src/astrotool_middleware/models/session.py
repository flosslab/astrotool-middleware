import uuid

from models.process import Process


class Session:
    def __init__(self, _id=None, process: Process | None=None):
        self.id = _id or str(uuid.uuid4())
        self.processes = {process.id: process} if process else {}
        self.uploads = {}

    def last_process(self):
        return self.processes and self.processes[list(self.processes.keys())[-1]]
