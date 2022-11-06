import streamlit as st
from pathlib import Path
from typing import List

from rhino3dm import File3dm

from ladybug.epw import EPW
from ladybug.dt import DateTime
from honeybee_3dm.config import Config, LayerConfig, FaceObject
from honeybee_radiance.lightsource.sky import ClimateBased
from honeybee_radiance.view import View


def write_mat_file(transmittance: float, target_folder: Path) -> Path:

    ref_material = Path(r'assets\daylight.mat')

    with open(ref_material.as_posix(), 'r') as ref_file:
        data = ref_file.readlines()

    mat = [
        '\n'*2,
        f'void glass rad_glass_{int(transmittance*100)}\n',
        '0\n',
        '0\n',
        f'3 {transmittance} {transmittance} {transmittance}\n'
    ]

    data += mat

    mat_file_path = target_folder.joinpath('daylight.mat')

    with open(mat_file_path.as_posix(), 'w') as mat_file:
        mat_file.writelines(data)

    return mat_file_path


@st.cache
def write_config(glass_layers: List[str],
                 ignore_layers: List[str],
                 transmittance: float,
                 target_folder: Path) -> Path:

    mat_file_path = write_mat_file(transmittance, target_folder)

    mat_name = f'rad_glass_{int(transmittance*100)}'

    layers = {}

    if glass_layers:
        for name in glass_layers:
            layers[name] = LayerConfig(honeybee_face_object=FaceObject.aperture,
                                       radiance_material=mat_name,
                                       include_child_layers=True)

    if ignore_layers:
        for name in ignore_layers:
            layers[name] = LayerConfig(ignore=True, include_child_layers=False)

    config = Config(sources={'radiance_material': mat_file_path.as_posix()},
                    layers=layers)

    config_path = target_folder.joinpath('config.json')
    with open(config_path, 'w', encoding='utf-8') as f:
        f.write(config.json())

    return config_path


def get_brightest_hour(epw: EPW) -> int:

    max_ill = epw.direct_normal_illuminance.max
    hoy = None

    for count, val in enumerate(epw.direct_normal_illuminance.values):
        if val == max_ill:
            hoy = count
            break

    return hoy


def get_sky(epw: EPW, north_angle: int) -> str:

    hoy = get_brightest_hour(epw)
    dt = DateTime.from_hoy(hoy)
    return ClimateBased.from_epw(epw, dt.month, dt.day, dt.hour, north_angle)


def get_views(rh: File3dm) -> List[View]:

    hb_views = []
    views = rh.NamedViews
    for view in views:
        name = view.Name
        location = view.Viewport.CameraLocation
        direction = view.Viewport.CameraDirection
        up_vector = view.Viewport.CameraUp

        hb_views.append(View(name,
                             (location.X, location.Y, location.Z),
                             (direction.X, direction.Y, direction.Z),
                             (up_vector.X, up_vector.Y, up_vector.Z),
                             'h'))

    return hb_views
