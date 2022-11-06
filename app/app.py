"""Estidama-daylight app."""

import tempfile
import streamlit as st
import rhino3dm

from PIL import Image
from pathlib import Path

from ladybug.epw import EPW

from honeybee_3dm.model import import_3dm
from honeybee_radiance_command.ra_gif import Ra_GIF
from honeybee_radiance.config import folders as rad_folders

from pollination_streamlit_io import get_host

from viewer import show_model
from helper import write_config
from process_hdr import eval_hdr, hdr_to_gif

# TODO: add docstring to all the functions


def main():

    st.set_page_config(
        page_title='Pre-Design Analysis',
        page_icon='images/favicon.png',
        layout='wide',
    )

    col1, col2, col3 = st.columns([1, 1, 1])

    with col2:
        st.header('Viz-analysis')
        st.markdown('Upload a Rhino file that you would use to generate visualization in a'
                    ' a rendering engine such as Enscape, or V-ray.')

        st.session_state.host = get_host()
        if not st.session_state.host:
            st.session_state.host = 'web'

        if 'temp_folder' not in st.session_state:
            st.session_state.temp_folder = Path(
                tempfile.mkdtemp(prefix=f'viz_analytics_{st.session_state.host}_'))

        target_folder = st.session_state.temp_folder

        if 'rhino_file' not in st.session_state:
            rhino_data = st.file_uploader('Upload Rhino file')
            if rhino_data:
                rhino_file = target_folder.joinpath('sample.3dm')
                rhino_file.write_bytes(rhino_data.read())
                st.session_state.rhino_file = rhino_file

        # process rhino file
        if 'rhino_file' in st.session_state:
            rhino3dm_file = rhino3dm.File3dm.Read(st.session_state.rhino_file.as_posix())

            # select the layer for glass
            layer_names = [layer.Name for layer in rhino3dm_file.Layers]

            glass_layers = st.multiselect('Select the layers that represent transparent'
                                          ' surfaces in the model.', layer_names)

            ignore_layers = st.multiselect(
                'Select the layers that you you like to not consider in simulation.'
                ' One example is light fixures that are going block any'
                ' views. Another example is human figures. Since they are not going to be'
                ' in one place for a long time.', layer_names)

            transmittance = st.number_input('transparency of glass as a percentage',
                                            value=0.6, min_value=0.1, max_value=0.9)

            if 'epw' not in st.session_state or not st.session_state.epw:
                epw_data = st.file_uploader('Upload EPW', type='epw')

                if epw_data:
                    epw_file = target_folder.joinpath('sample.epw')
                    epw_file.write_bytes(epw_data.read())
                    st.session_state.epw = epw_file

            if 'epw' in st.session_state and st.session_state.epw:
                epw = EPW(st.session_state.epw)
                st.write(epw)

            config_path = write_config(glass_layers, ignore_layers,
                                       transmittance, target_folder)
            st.write(config_path)

    #     views = rhino3dm_file.NamedViews

    # if 'rhino_file' in st.session_state and 'hbjson' not in st.session_state:
    #     hb_model = import_3dm(st.session_state.rhino_file.as_posix())
    #     hb_model.to_hbjson('sample', target_folder)
    #     st.session_state.hbjson = target_folder.joinpath('sample.hbjson')

    # if 'hbjson' in st.session_state:
    #     show_model(st.session_state.hbjson, target_folder)

    # # testing hdr to gif workflow
    # hdr_path = Path(r'assets\sample.hdr')
    # evalglare_path = Path(r'assets\evalglare\evalglare.exe')

    # eval_hdr_path, dgp, category = eval_hdr(hdr_path, target_folder, evalglare_path)

    # gif_path = hdr_to_gif(eval_hdr_path, target_folder)

    # image = Image.open(gif_path)
    # st.image(image)


if __name__ == '__main__':
    main()
