import os
import subprocess
import streamlit as st

from pathlib import Path
from typing import Tuple

from honeybee_radiance.config import folders as rad_folders
from honeybee_radiance_command.ra_gif import Ra_GIF


@st.cache
def dgp_comfort_category(dgp):
    """Get text for the glare comfort category given a DGP value."""
    if dgp < 0.35:
        return 'Imperceptible Glare'
    if dgp < 0.40:
        return 'Perceptible Glare'
    if dgp < 0.45:
        return 'Disturbing Glare'

    return 'Intolerable Glare'


@st.cache
def eval_hdr(hdr_path, target_folder: Path,
             evalglare_path: Path) -> Tuple[Path, float, str]:

    # TODO: add them as parameters
    projection = '-vth'
    width = 800
    height = 800

    # get the path the the evalglare command and setup the check image argument
    evalglare_exe = evalglare_path.absolute().as_posix()

    # path to the evaluated HDR image
    checkhdr_path = target_folder.joinpath('check_hdr.hdr')

    cmds = [evalglare_exe, '-c', checkhdr_path.as_posix()]
    # since pcomp is used to merge images, the input usually doesn't have view information
    # add default view information for hemispheical fish-eye camera
    cmds.extend([projection, '-vv', '180', '-vh', '180'])
    cmds.append(hdr_path.as_posix())
    # run the evalglare command in a manner that lets us obtain the stdout result
    use_shell = True if os.name == 'nt' else False
    process = subprocess.Popen(cmds, stdout=subprocess.PIPE, shell=use_shell)
    stdout = process.communicate()

    # process the stdout result into the component outputs
    glare_result = stdout[0].decode('utf-8').split(':')[-1].strip()
    glare_indices = [float(val) for val in glare_result.split(' ')]
    dgp = glare_indices.pop(0)
    category = dgp_comfort_category(dgp)

    return checkhdr_path, dgp, category


@st.cache
def hdr_to_gif(hdr_path: Path, target_folder: Path) -> Path:
    gif_path = target_folder.joinpath(f'{hdr_path.stem}.gif')

    ra_gif = Ra_GIF(input=hdr_path.as_posix(), output=gif_path.as_posix())
    env = None
    if rad_folders.env != {}:
        env = rad_folders.env
    env = dict(os.environ, **env) if env else None

    ra_gif.run(env, target_folder.as_posix())

    return gif_path
