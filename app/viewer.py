"""Functions to help visualize HBJSON in a browser."""


import streamlit as st

from pathlib import Path
from typing import Union

from honeybee_vtk.model import Model as VTKModel
from honeybee_vtk.vtkjs.schema import SensorGridOptions, DisplayMode

from pollination_streamlit_viewer import viewer


@st.cache
def write_vtkjs(hbjson_path: Path, last_updated: float, target_folder: Path,
                grid_options: SensorGridOptions = SensorGridOptions.Ignore,
                grid_display_model: DisplayMode = DisplayMode.SurfaceWithEdges) -> Union[
                    Path, None]:
    """Write a vtkjs file.

    The last_updated argument here is only used by Streamlit to decide whether to
    run the function and serve its value or to serve the last cached value of the
    function.

    args:
        hbjson_path: Path to the HBJSON file to be converted to vtkjs.
        last_updated: Last updated time of the HBJSON file as a float.
        target_folder: Path to the folder where the vtkjs file will be written.
        grid_options: a SensorGridOptions object to indicate what to do with the grids
            found in HBJSON. Defaults to ignoring the grids in the model.
        grid_display_mode: Display mode for the Grids. Defaults to SurfaceWithEdges.
            Other options are shaded, surface, wireframe, and points.

    returns:
        Path to the written vtkjs file.
    """
    if not hbjson_path:
        return

    model = VTKModel.from_hbjson(hbjson_path.as_posix(), load_grids=grid_options)

    vtkjs_folder = target_folder.joinpath('vtkjs')

    if not vtkjs_folder.exists():
        vtkjs_folder.mkdir(parents=True, exist_ok=True)

    vtkjs_file = vtkjs_folder.joinpath(f'{hbjson_path.stem}.vtkjs')
    model.to_vtkjs(
        folder=vtkjs_folder.as_posix(),
        name=hbjson_path.stem,
        grid_display_mode=grid_display_model
    )

    return vtkjs_file


def show_model(hbjson_path: Path, target_folder: Path,
               key: str = '3d_viewer',
               grid_options: SensorGridOptions = SensorGridOptions.Ignore,
               subscribe: bool = False) -> None:
    """Show HBJSON in a browser.

    If not done already, this function will convert the HBJSON to vtkjs and write to
    a folder first. This is done so that the next time a call is made to visualize the
    same HBJSON, the function will simply visualize the already created vtkjs file 
    rather than creating it again.

    args:
        hbjson_path: Path to the HBJSON file you'd like to visualize in the browser.
        last_updated_time: Last updated time of the HBJSON file.
        target_folder: Path to the folder where the vtkjs file will be written.
        key: A unique string for this instance of the viewer.
        grid_options: A SensorGridOptions object to indicate what to do with the grids
            found in HBJSON. Defaults to ignoring the grids found in the model.
            Alternatives are Mesh, Sensors, and RadialGrid.
        subscribe: A boolean to subscribe or unsubscribe the VTKJS camera
             and renderer content. If you don't know what you're doing, it's best to
             keep this to False.
    """

    vtkjs_name = f'{hbjson_path.stem}_vtkjs'

    if vtkjs_name not in st.session_state:
        vtkjs = write_vtkjs(hbjson_path, hbjson_path.stat().st_mtime, target_folder,
                            grid_options)
        st.session_state[vtkjs_name] = vtkjs
    else:
        vtkjs = st.session_state[vtkjs_name]

    viewer(content=vtkjs.read_bytes(), key=key, subscribe=subscribe)
