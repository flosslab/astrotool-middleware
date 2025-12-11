from typing import TYPE_CHECKING

import models as m
from utils import visivoRpc

if TYPE_CHECKING:
    from middleware import Middleware


class ProcessRPC:

    @visivoRpc("get.process")
    def get_view_id(self: 'Middleware', process: 'm.Process'):
        return {
            "name": process.name,
            "objectIds": {
                "2d": process.last_object_2d_id,
                "3d": process.last_object_id
            },
            "rendering": {
                "3d": {
                    "scalar": process.rendering.contour_filter.contour_values[-1],
                    "cutter": process.rendering.plane.origin[-1] * process.rendering.pixel_scale
                },
                "2d": {
                    "contour": {
                        "enabled": process.rendering.contour_actor_2d.GetVisibility(),
                        "level": process.rendering.contour_filter_2d.GetNumberOfContours(),
                        "min": process.rendering.contour_mapper_2d.GetScalarRange()[0],
                        "max": process.rendering.contour_mapper_2d.GetScalarRange()[1]
                    }
                }
            },
            "resource": {
                "header": process.rendering.header,
                "cutterBounds": process.rendering.actor.GetBounds()[-2:],
                "scalarRange": process.rendering.scalar_range
            },
            "stats": process.rendering.stats
        }

    @visivoRpc("create.process")
    def open_process(self: 'Middleware', session: 'm.Session', process: 'm.Process', resource: dict):
        if not process:
            process = m.Process()
            session.processes[process.id] = process
            self.generate_object_ids(process)
        match resource.get('type'):
            case 'upload':
                process.rendering.generate_from_source(session.uploads[resource['filename']]['dataBuffer'])
                process.name = resource['filename']
            case 'external':
                print(f"Not implemented yet")
            case _:
                print(f"Unknown resource type: {resource.get('type')}")
                return
        return {
            "processId": process.id
        }
