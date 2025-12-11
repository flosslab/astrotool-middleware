import json

import vtk
from astromodules.renderingAnnotation import LegendScaleActor
from vtkmodules.vtkCommonColor import vtkNamedColors

from models.process_file import ProcessFile

vtkColors = vtkNamedColors()


class Rendering:

    def __init__(self):
        self.image_data = None

        # Pipeline 3d
        self.renderer = vtk.vtkRenderer()
        self.render_window = vtk.vtkRenderWindow()
        self.render_window.SetOffScreenRendering(1)
        self.render_window.AddRenderer(self.renderer)
        self.render_window_interactor = vtk.vtkRenderWindowInteractor()
        self.render_window_interactor.SetRenderWindow(self.render_window)
        self.render_window_interactor.GetInteractorStyle().SetCurrentStyleToTrackballCamera()
        # Pipeline 2d
        self.renderer_2d = vtk.vtkRenderer()
        self.render_2d_window = vtk.vtkRenderWindow()
        self.render_2d_window.SetOffScreenRendering(1)
        self.render_2d_window.AddRenderer(self.renderer_2d)
        self.render_2d_interactor = vtk.vtkRenderWindowInteractor()
        self.render_2d_interactor.SetRenderWindow(self.render_2d_window)
        self.render_2d_interactor.SetInteractorStyle(vtk.vtkInteractorStyleImage())  # disable interactions

        self.renderer.SetBackground(0.1, 0.1, 0.1)
        self.renderer_2d.SetBackground(0.1, 0.1, 0.1)
        self.render_window.Render()
        self.render_2d_window.Render()

    def _create_reader(self):
        self.scalar_range = self.image_data.GetScalarRange()
        self.bounds = self.image_data.GetBounds()
        self.header = json.loads(self.image_data.GetFieldData().GetAbstractArray("Header").GetValue(0))

    def _create_mapper_and_actor(self):
        self.center_pixel_x = self.header['CRPIX1']['value']
        self.center_pixel_y = self.header['CRPIX2']['value']
        self.center_pixel_z = self.header['CRPIX3']['value']
        self.center_RA = self.header['CRVAL1']['value']
        self.center_DEC = self.header['CRVAL2']['value']
        self.center_Z = self.header['CRVAL3']['value']
        self.pixel_scale = abs(self.header['CDELT1']['value'])
        self.translate_x = self.center_RA - ((self.center_pixel_x - 1.5) * self.pixel_scale)
        self.translate_y = self.center_DEC - ((self.center_pixel_y - 1.5) * self.pixel_scale)
        self.translate_z = self.center_Z - ((self.center_pixel_z - 1) * self.pixel_scale)
        transform = vtk.vtkTransform()
        transform.Translate(self.translate_x, self.translate_y, 0)
        transform.Scale(self.pixel_scale, self.pixel_scale, self.pixel_scale)
        self.transform = transform
        self.mapper = vtk.vtkDataSetMapper()
        self.mapper.SetInputData(self.image_data)
        self.actor = vtk.vtkActor()
        self.actor.SetMapper(self.mapper)
        self.actor.SetUserTransform(transform)
        camera = self.renderer.GetActiveCamera()
        camera.SetPosition(self.center_RA, self.center_DEC, self.center_Z + 100)
        camera.SetFocalPoint(self.center_RA, self.center_DEC, self.center_Z)
        camera.SetViewUp(0, 1, 0)
        print(f"Camera position: {camera.GetPosition()}")
        print(f"Camera focal point: {camera.GetFocalPoint()}")
        self.renderer.AddActor(self.actor)
        self.renderer.ResetCamera()

    def _create_contour_filter(self):
        self.contour_filter = vtk.vtkContourFilter()
        self.contour_filter.SetInputData(self.image_data)
        range_min, range_max = self.contour_filter.GetOutput().GetScalarRange()
        contour_value = (range_max + range_min) / 2
        self.contour_filter.SetValue(0, contour_value)
        self.mapper.SetInputConnection(self.contour_filter.GetOutputPort())
        self.mapper.SetLookupTable(self._get_contour_lut())

    def _create_cutting_plane(self):
        plane = vtk.vtkPlane()
        center_z = (self.bounds[-1] + 30) / 2  # TODO: capire +30
        plane.SetOrigin(0, 0, center_z)
        plane.Push(-center_z)
        plane.SetNormal(0, 0, 1)

        cutter = vtk.vtkCutter()
        cutter.SetCutFunction(plane)
        cutter.SetInputData(self.image_data)  # usa il reader per l'input
        cutter.Update()

        cutter_mapper = vtk.vtkPolyDataMapper()
        cutter_mapper.SetInputConnection(cutter.GetOutputPort())
        cutter_mapper.SetScalarVisibility(0)  # Disabilita la visibilità del colore scalare
        cutter_mapper.Update()

        plane_actor = vtk.vtkActor()
        plane_actor.GetProperty().SetColor(0.8, 0.8, 0.8)
        plane_actor.GetProperty().SetSelectionColor(0.2, 0.5, 0.2, 1)
        plane_actor.GetProperty().SetLineWidth(2)
        plane_actor.GetProperty().SetAmbient(1.0)
        plane_actor.GetProperty().SetDiffuse(0.0)
        plane_actor.SetMapper(cutter_mapper)
        plane_actor.SetUserTransform(self.transform)

        self.plane = plane
        self.cutter = cutter
        self.cutterMapper = cutter_mapper
        self.cutterActor = plane_actor

        self.renderer.AddActor(self.cutterActor)

    def _create_iso_contour(self):
        # **1. Creazione della slice mantenendo la posizione spaziale**
        self.reslice = vtk.vtkImageReslice()
        self.reslice.SetInputData(self.image_data)
        self.reslice.SetOutputDimensionality(2)
        self.reslice.SetResliceAxesOrigin(0, 0, self.bounds[4])
        self.reslice.SetInterpolationModeToLinear()

        # **2. Creazione dell'attore per la slice**
        self.image_actor = vtk.vtkImageActor()
        self.image_actor.SetCoordinateSystemToWorld()
        self.image_actor.SetUserTransform(self.transform)

        # **3. Mapper per la slice (senza LUT, colori originali)**
        self.image_actor.GetMapper().SetInputConnection(self.reslice.GetOutputPort())

        # **4. Aggiunta della slice al renderer**
        self.renderer_2d.AddActor2D(self.image_actor)

        # **5. Calcolo del gradiente per i contorni**
        gradient = vtk.vtkImageGradient()
        gradient.SetInputConnection(self.reslice.GetOutputPort())  # Usa la slice mantenendo coordinate corrette
        gradient.Update()

        contours_filter = vtk.vtkContourFilter()
        contours_filter.GenerateValues(
            15,
            self.stats['three_rms'],
            self.stats['scalar_range']['upper']
        )  # Genera contorni sulle variazioni di intensità
        contours_filter.SetInputConnection(gradient.GetOutputPort())  # Usa il gradiente

        self.contour_filter_2d = contours_filter

        # **6. Creazione della LUT per i contorni (rosso → arancione → giallo → verde)**
        self.reslice.Update()
        range_min, range_max = [round(x, 4) for x in self.image_data.GetScalarRange()]
        lut = vtk.vtkLookupTable()
        lut.SetTableRange(range_min, range_max)
        lut.SetNumberOfTableValues(256)
        # color = vtk.vtkLookupTable().Color()
        # for i in range(256):
        #     h = (i * 240) / 255

        # lut.Build()
        # lut.SetTableValue(0, 1.0, 0.0, 0.0, 1.0)  # Rosso
        # lut.SetTableValue(int(range_max/4), 1.0, 0.5, 0.0, 1.0)  # Arancione
        # lut.SetTableValue(int(range_max/4)*2, 1.0, 1.0, 0.0, 1.0)  # Giallo
        # lut.SetTableValue(int(range_max/4)*3, 0.0, 1.0, 0.0, 1.0)  # Verde

        # **7. Creazione del mapper per i contorni**
        contour_mapper = vtk.vtkPolyDataMapper()
        contour_mapper.SetInputConnection(contours_filter.GetOutputPort())
        contour_mapper.SetLookupTable(lut)
        contour_mapper.SetScalarVisibility(True)
        contour_mapper.SetScalarRange(range_min, range_max)
        # contour_mapper.SetScalarModeToUsePointData()


        self.contour_mapper_2d = contour_mapper

        # **8. Creazione dell'attore per i contorni**
        contour_actor = vtk.vtkActor()
        contour_actor.SetMapper(contour_mapper)
        contour_actor.GetProperty().SetLineWidth(1)  # Linee più visibili
        contour_actor.SetUserTransform(self.transform)  # Sincronizza posizione
        contour_actor.SetVisibility(False)  # Sincronizza posizione

        self.contour_actor_2d = contour_actor

        legend_2d = LegendScaleActor()
        legend_2d.SetLabelModeToWCS()
        legend_2d.SetLegendVisibility(0)

        self.renderer_2d.AddActor2D(self.contour_actor_2d)
        self.renderer_2d.AddActor2D(legend_2d)

        self.render_2d_window.Render()

    def _update_reslice(self, x, y, z):
        reslice_axes = vtk.vtkMatrix4x4()
        reslice_axes.Identity()
        reslice_axes.SetElement(0, 3, x)  # Imposta il piano Z centrale
        reslice_axes.SetElement(1, 3, y)  # Imposta il piano Z centrale
        reslice_axes.SetElement(2, 3, z)  # Imposta il piano Z centrale
        self.reslice.SetResliceAxes(reslice_axes)

    def _gen_wireframe(self):
        outline = vtk.vtkOutlineFilter()
        outline.SetInputData(self.image_data)

        outline_mapper = vtk.vtkPolyDataMapper()
        outline_mapper.SetInputConnection(outline.GetOutputPort())

        outline_actor = vtk.vtkActor()
        outline_actor.SetMapper(outline_mapper)
        outline_actor.GetProperty().SetRepresentationToWireframe()
        outline_actor.GetProperty().SetColor(1, 1, 1)
        outline_actor.SetUserTransform(self.transform)
        self.renderer.AddActor(outline_actor)

    def _get_contour_lut(self):
        lookup_table = vtk.vtkLookupTable()
        lookup_table.Build()
        range_min, range_max = self.image_data.GetScalarRange()
        lookup_table.SetTableRange(range_min, range_max)
        num_colors = lookup_table.GetNumberOfTableValues()
        for i in range(num_colors):
            t = i / (num_colors - 1)
            lookup_table.SetTableValue(i, t, 0.1 * t, 0.5 * t, 1.0)
        lookup_table.SetTableValue(0, 0.7, 0.7, 0.7, 1.0)
        return lookup_table

    def destroy(self):
        # 3d
        self.render_window.Finalize()
        self.render_window.OffScreenRenderingOn()
        self.render_window_interactor.TerminateApp()
        self.render_window_interactor.SetRenderWindow(None)
        self.renderer.RemoveAllViewProps()
        # 2d
        self.render_2d_window.Finalize()
        self.render_2d_window.OffScreenRenderingOn()
        self.render_2d_interactor.TerminateApp()
        self.render_2d_interactor.SetRenderWindow(None)
        self.renderer_2d.RemoveAllViewProps()

    def _create_cube_axes_actor(self):
        axis_x_title = self.header['CTYPE1']['value']
        axis_y_title = self.header['CTYPE2']['value']
        axis_z_title = self.header['CTYPE3']['value']

        cubeAxesActor = vtk.vtkCubeAxesActor()
        cubeAxesActor.SetCamera(self.renderer.GetActiveCamera())
        cubeAxesActor.SetUseTextActor3D(1)
        cubeAxesActor.SetXTitle(axis_x_title)
        cubeAxesActor.SetYTitle(axis_y_title)
        cubeAxesActor.SetZTitle(axis_z_title)
        cubeAxesActor.DrawXGridlinesOn()
        cubeAxesActor.DrawYGridlinesOn()
        cubeAxesActor.DrawZGridlinesOn()
        cubeAxesActor.SetFlyModeToStaticEdges()
        cubeAxesActor.SetBounds(self.bounds)
        cubeAxesActor.SetUserTransform(self.transform)
        self.cubeAxesActor = cubeAxesActor

        def update_axes_and_legend(obj, event):
            camera_position = [round(pos, 6) for pos in self.renderer.GetActiveCamera().GetPosition()]

            # Calcoliamo lo spostamento della fotocamera rispetto al centro in pixel
            pixel_offset_x = round(camera_position[0] - self.center_RA, 6)
            pixel_offset_y = round(camera_position[1] - self.center_DEC, 6)
            pixel_offset_z = round(camera_position[2] + 0, 6)

            # Calcoliamo i nuovi range di RA e DEC in base allo spostamento della fotocamera
            ra_min = self.translate_x + (self.bounds[0] + pixel_offset_x) * self.pixel_scale
            ra_max = self.translate_x + (self.bounds[1] + pixel_offset_x) * self.pixel_scale
            dec_min = self.translate_y + (self.bounds[2] + pixel_offset_y) * self.pixel_scale
            dec_max = self.translate_y + (self.bounds[3] + pixel_offset_y) * self.pixel_scale
            z_min = 0 + (self.bounds[4] + pixel_offset_z) * self.pixel_scale
            z_max = 0 + (self.bounds[5] + pixel_offset_z) * self.pixel_scale

            # Aggiornare gli assi con i limiti trasformati
            new_bounds = [ra_min, ra_max, dec_min, dec_max, z_min, z_max]
            cubeAxesActor.SetBounds(new_bounds)

            # Aggiorniamo la scena
            self.render_window.Render()

        update_axes_and_legend(None, None)

    def switch3d_layout(self, layout_type):
        if layout_type == 'legend':
            self.renderer.RemoveActor(self.cubeAxesActor)
            self.renderer.AddActor(self.legend)
        else:
            self.renderer.RemoveActor(self.legend)
            self.renderer.AddActor(self.cubeAxesActor)

    def _create_legend_actor(self):
        self.legend = LegendScaleActor()
        self.legend.SetLabelModeToWCS()
        self.legend.SetLegendVisibility(0)

    def generate_from_source(self, source):
        processed_file = ProcessFile(source)
        self.stats = processed_file.get_stats()
        self.image_data = processed_file.get_image_data()
        processed_file = None
        self._create_reader()
        self._create_mapper_and_actor()
        self._create_contour_filter()
        self._create_cutting_plane()
        self._create_iso_contour()
        self._create_cube_axes_actor()
        self._create_legend_actor()
        self.switch3d_layout('layout')
        self._gen_wireframe()

        self.render_window.Render()
        self.render_2d_window.Render()
        self.renderer_2d.ResetCamera()


class SplineCallback:
    def __init__(self, spline_widget):
        self.spline = spline_widget

    def __call__(self, caller, ev):
        spline_widget = caller
        length = spline_widget.GetSummedLength()
        print(f'Length: {length}')
