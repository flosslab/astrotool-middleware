from typing import TYPE_CHECKING

import models as m
from utils.utils import visivoRpc

if TYPE_CHECKING:
    from middleware import Middleware


class SessionRPC:

    @visivoRpc("get.session.id")
    def get_session_id(self: 'Middleware', session):
        if not session:
            session = m.Session()
            self.__class__.active_sessions[session.id] = session
            print(f"[{session.id}] - New session created")
        else:
            print(f"[{session.id}] - Reconnected to existing session")
        last_process = session.last_process()
        last_process_id = last_process.id if last_process else None
        return {"sessionId": session.id, "processId": last_process_id}
