import io
import json

import numpy as np
import vtk
from astropy.io import fits
from vtkmodules.util.numpy_support import numpy_to_vtk

from utils import Utils


class ProcessFile:

    def __init__(self, base64_string: str):
        self.stats = {}
        self.image_data = None
        self.process(base64_string)

    def process(self, _data):
        _input_buffer = io.BytesIO(_data)
        self.image_data = self.fits_to_image_data(_input_buffer)

    def fits_to_image_data(self, buffer):
        hdul = fits.open(
            name=buffer,
            ignore_missing_simple=False,
            decompress_in_memory=True
        )
        data = hdul[0].data.astype(np.float32)
        self.stats = Utils.get_stats(hdul)
        shape = data.shape[-3:] if len(data.shape) > 3 else data.shape
        axis_x, axis_y, axis_z = shape
        vtk_data_array = numpy_to_vtk(data.flatten())
        vtk_data_array.SetNumberOfComponents(1)
        vtk_data_array.SetName("FITSImage")
        image_data = vtk.vtkImageData()
        image_data.SetDimensions(axis_z, axis_y, axis_x)
        image_data.SetOrigin(0.0, 0.0, 0.0)
        image_data.SetSpacing(1.0, 1.0, 1.0)
        image_data.GetPointData().SetScalars(vtk_data_array)
        json_data = self.header_to_json(header=hdul[0].header)
        self.put_header_into_image(json_data, image_data)
        return image_data

    @staticmethod
    def header_to_json(header):
        result = json.dumps({x[0]: {'descr': x[2], 'value': x[1]} for x in header._cards})
        return result

    @staticmethod
    def put_header_into_image(json_data, source):
        source.GetFieldData().AddArray(vtk.vtkStringArray())
        json_meta_data = source.GetFieldData().GetAbstractArray(0)
        json_meta_data.SetName("Header")
        json_meta_data.InsertNextValue(json_data)

    def get_image_data(self):
        return self.image_data

    def get_stats(self):
        return self.stats

# if __name__ == "__main__":
#     with open("cubehi.fits", "rb") as f:
#         ProcessFile(f.read())
