import os
import subprocess
import math
from pathlib import Path

from honeybee_radiance.config import folders as rad_folders


def dgp_comfort_category(dgp):
    """Get text for the glare comfort category given a DGP value."""
    if dgp < 0.35:
        return 'Imperceptible Glare'
    elif dgp < 0.40:
        return 'Perceptible Glare'
    elif dgp < 0.45:
        return 'Disturbing Glare'
    else:
        return 'Intolerable Glare'


def eval_hdr(hdr_path, target_folder: Path, evalglare_path: Path) -> Path:
    # check the input image to ensure it meets the criteria

    projection = '-vth'
    width = 800
    height = 800

    # get the path the the evalglare command and setup the check image argument
    evalglare_exe = evalglare_path.absolute().as_posix()

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
    DGP = glare_indices.pop(0)
    category = dgp_comfort_category(DGP)

    return checkhdr_path
