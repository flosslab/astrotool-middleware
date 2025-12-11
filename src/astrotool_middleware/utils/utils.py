import inspect

from spectral_cube import SpectralCube
from vtkmodules.web.wslink import exportRpc
import numpy as np

def visivoRpc(name=None):
    """
    Extend exportRpc decorator to add a session argument.
    """
    def decorator(func):
        @exportRpc(name)
        def wrapper(self, *args, **kwargs):
            payload = args[0] if args else kwargs
            client_id = payload.get("sessionId")
            process_id = payload.get("processId")
            session = self.active_sessions.get(client_id)
            process = session.processes.get(process_id) if session else None
            # if session is None:
            #     raise ValueError(f"Sessione non trovata per client_id={client_id}")
            for key in ["sessionId", "processId"]:
                payload.pop(key, None)  # Usa pop per evitare KeyError
            sig = inspect.signature(func)
            params = sig.parameters.keys()
            if "session" in params:
                payload["session"] = session
            if "process" in params:
                payload["process"] = process
            bound_args = sig.bind_partial(self, **payload)
            bound_args.apply_defaults()

            # Esegui la funzione originale con gli argomenti corretti
            return func(**bound_args.arguments)

        return wrapper
    return decorator


class Utils:

    @staticmethod
    def get_stats(buffer):
        cube = SpectralCube.read(buffer)
        masked = cube.with_mask(cube.mask)
        valid_data = masked.unmasked_data[:].value
        valid_mask = masked.mask.include()[:]
        valid_values = valid_data[valid_mask]

        return {
            "rms": float(np.std(valid_values)),
            "three_rms": float(np.std(valid_values) * 3),
            "scalar_range": {
                "lower": float(np.min(valid_values)),
                "upper": float(np.max(valid_values)),
            },
            "mean": float(np.mean(valid_values))
        }
