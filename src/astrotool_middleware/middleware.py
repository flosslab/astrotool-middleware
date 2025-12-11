# import to process args
import argparse
import gc
import logging

from vtkmodules.vtkCommonColor import vtkNamedColors
from vtkmodules.web import protocols
from vtkmodules.web import wslink as vtk_wslink
from wslink import server

from models import AbstractMiddleware
from rpc import *

vtkColors = vtkNamedColors()

logger = logging.getLogger(__name__)


# =============================================================================
#  Custom ServerProtocol class
# =============================================================================
class Middleware(
    vtk_wslink.ServerProtocol,
    AbstractMiddleware,
    GeneralRPC
):
    # Application configuration
    authKey = "wslink-secret"

    def initialize(self):
        # Protocols registering
        self.registerVtkWebProtocol(protocols.vtkWebMouseHandler())
        self.registerVtkWebProtocol(protocols.vtkWebViewPort())
        self.registerVtkWebProtocol(protocols.vtkWebPublishImageDelivery(decode=False))
        self.registerVtkWebProtocol(protocols.vtkWebViewPortGeometryDelivery())
        self.updateSecret(Middleware.authKey)  # Update secrets
        self.getApplication().SetImageEncoding(0)  # Set no image encoding

    def generate_object_ids(self, process):
        object_id_map = self.getApplication().GetObjectIdMap()
        process.last_object_id = object_id_map.SetActiveObject(
            f"VIEW-{process.id}",
            process.rendering.render_window
        )
        process.last_object_2d_id = object_id_map.SetActiveObject(
            f"VIEW-2D-{process.id}",
            process.rendering.render_2d_window
        )
        return process

    def onClose(self, client_id):
        """Called when a websocket connection is closed."""
        session = self.active_sessions.get(client_id)
        if session:
            session.destroy()
            del session
            del self.active_sessions[client_id]
            gc.collect()
            print(f"close: {client_id}")
