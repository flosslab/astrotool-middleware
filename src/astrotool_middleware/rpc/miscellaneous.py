import base64
from typing import TYPE_CHECKING

import models as m
from utils.utils import visivoRpc

if TYPE_CHECKING:
    from middleware import Middleware


class MiscellaneousRPC:

    @visivoRpc("update.contour")
    def update_contour(self: 'Middleware',process: 'm.Process', value):
        """Update the contour filter for the given session."""
        print(f'Updating Contour Filter: {value}')
        x = process.rendering
        x.contour_filter.SetValue(0, value)
        x.render_window.Render()
        return {"success": True, "message": f"Contour updated to {value}"}

    @visivoRpc("update.cutting.plane")
    def update_cutting_plane(self: 'Middleware', process: 'm.Process', value=0):
        """Update the cutting plane position for the given session."""
        obj = process.rendering
        values = [*obj.plane.normal[0:2], value / obj.pixel_scale]
        obj.plane.SetOrigin(*values)
        obj._update_reslice(*values)
        obj.render_window.Render()
        obj.render_2d_window.Render()
        return {"status": "updated"}

    @visivoRpc("update.render.layout")
    def update_render_layout(self: 'Middleware', process: 'm.Process', value):
        obj = process.rendering
        obj.switch3d_layout(value)
        obj.render_window.Render()
        return {"status": "updated", 'message': f'to {value}'}

    # @exportRpc("upload.chunk")
    # def receive_chunk(self, chunk_data):
    #     """Concatenate chunk data to the buffer and return the current buffer size
    #     for the client to update its progress bar."""
    #     decoded_chunk = chunk_data
    #     self.data_buffer += decoded_chunk
    #     return {"status": "chunk received", "buffer_size": len(self.data_buffer)}

    @visivoRpc("file.chunk.upload")
    def upload_chunk(self: 'Middleware', session: 'm.Session', process: 'm.Process', file_name, chunk_index,
                     total_chunks, data):
        base64_data = data
        chunk_bytes = base64.b64decode(base64_data)
        if file_name not in session.uploads:
            session.uploads[file_name] = {
                "chunks": {},
                "totalChunks": total_chunks,
                "dataBuffer": None,
            }
        upload = session.uploads[file_name]
        upload["chunks"][chunk_index] = chunk_bytes
        if len(upload["chunks"]) == total_chunks:
            print(f"All chunks are received. '{file_name}'. Recomposing...")
            ordered_chunks = [
                upload["chunks"][i] for i in sorted(upload["chunks"])
            ]
            upload["dataBuffer"] = b''.join(ordered_chunks)
            print(f"File '{file_name}' built in RAM ({len(upload['dataBuffer'])} byte)")

            return {
                "status": "completed",
            }

        return f"Chunk {chunk_index + 1}/{total_chunks} received"

    @visivoRpc("contour.toggle")
    def toggle_contours(self: 'Middleware', session: 'm.Session', process: 'm.Process', enabled: bool):
        """Abilita o disabilita il rendering dei contorni."""
        obj = process.rendering
        obj.contour_actor_2d.SetVisibility(enabled)
        obj.render_2d_window.Render()
        print(f"contour.toggle {obj.contour_actor_2d.GetVisibility()}")

        return {"status": "updated"}

    @visivoRpc("contour.update_levels")
    def update_contour_levels(self: 'Middleware', session: 'm.Session', process: 'm.Process', level: int, min: float,
                              max: float):
        """Aggiorna dinamicamente i livelli min/max dei contorni."""
        obj = process.rendering
        obj.contour_filter_2d.GenerateValues(level, min, max)
        obj.contour_mapper_2d.SetScalarRange(min, max)
        obj.render_2d_window.Render()
        print(f'contour.update_levels {level}, {min}, {max}')
        return {"status": "updated"}
