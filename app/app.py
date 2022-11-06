"""Estidama-daylight app."""

import tempfile
import streamlit as st
import rhino3dm


from PIL import Image
from pathlib import Path
from pollination_streamlit_io import get_host
from honeybee_3dm.model import import_3dm
from honeybee_radiance_command.ra_gif import Ra_GIF
from honeybee_radiance.config import folders as rad_folders

from viewer import show_model
from process_hdr import eval_hdr, hdr_to_gif


def main():

    st.session_state.host = get_host()
    if not st.session_state.host:
        st.session_state.host = 'web'

    if 'temp_folder' not in st.session_state:
        st.session_state.temp_folder = Path(
            tempfile.mkdtemp(prefix=f'viz_analytics_{st.session_state.host}_'))

    target_folder = st.session_state.temp_folder

    if 'rhino_file' not in st.session_state:
        rhino_data = st.file_uploader('upload rhino')
        if rhino_data:
            rhino_file = target_folder.joinpath('sample.3dm')
            rhino_file.write_bytes(rhino_data.read())
            st.session_state.rhino_file = rhino_file

    hdr_path = Path(r'assets\sample.hdr')
    evalglare_path = Path(r'assets\evalglare\evalglare.exe')

    eval_hdr_path, dgp, category = eval_hdr(hdr_path, target_folder, evalglare_path)

    gif_path = hdr_to_gif(eval_hdr_path, target_folder)

    image = Image.open(gif_path)
    st.image(image)

    # # process rhino file
    # if 'rhino_file' in st.session_state:
    #     rhino3dm_file = rhino3dm.File3dm.Read(st.session_state.rhino_file.as_posix())
    #     views = rhino3dm_file.NamedViews

    # if 'rhino_file' in st.session_state and 'hbjson' not in st.session_state:
    #     hb_model = import_3dm(st.session_state.rhino_file.as_posix())
    #     hb_model.to_hbjson('sample', target_folder)
    #     st.session_state.hbjson = target_folder.joinpath('sample.hbjson')

    # if 'hbjson' in st.session_state:
    #     st.write(st.session_state.hbjson)
    #     show_model(st.session_state.hbjson, target_folder)


if __name__ == '__main__':
    main()
