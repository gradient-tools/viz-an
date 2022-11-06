import streamlit as st
from pathlib import Path
from typing import List
from honeybee_3dm.config import Config, LayerConfig, FaceObject


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
