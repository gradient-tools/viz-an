"""Estidama-daylight app."""

import tempfile
import streamlit as st
import rhino3dm
import time

from PIL import Image
from pathlib import Path

from ladybug.epw import EPW

from honeybee_3dm.model import import_3dm
from honeybee_radiance_command.ra_gif import Ra_GIF
from honeybee_radiance.config import folders as rad_folders

from pollination_streamlit_io import get_host

from viewer import show_model
from helper import write_config, get_sky, get_views, load_css, rhino_3dm_to_hbjson
from process_hdr import eval_hdr, hdr_to_gif
from simulation import create_job, recreate_job, request_status, SimStatus,\
    download_output

# TODO: add docstring to all the functions


def main():

    st.set_page_config(
        page_title='Vizan',
        page_icon='images/favicon.png',
        layout='centered',
    )
    load_css()

    st.header('Vizan')
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

        north_angle = st.number_input('Counter clockwise rotation of North vector'
                                      ' . A value between 0 and 360', value=0,
                                      min_value=0, max_value=360)

        if 'epw' not in st.session_state or not st.session_state.epw:
            epw_data = st.file_uploader('Upload EPW', type='epw')

            if epw_data:
                epw_file = target_folder.joinpath('sample.epw')
                epw_file.write_bytes(epw_data.read())
                st.session_state.epw = epw_file

        if 'epw' in st.session_state and st.session_state.epw:
            epw = EPW(st.session_state.epw)

        config, config_path = write_config(glass_layers, ignore_layers,
                                           transmittance, target_folder)

        views = get_views(rhino3dm_file)

        translate = st.button('Translate to HBJSON')
        if translate:
            st.session_state.hbjson = rhino_3dm_to_hbjson(rhino3dm_file, config,
                                                          config_path, views, target_folder)
        if 'hbjson' in st.session_state:
            show_model(st.session_state.hbjson, target_folder)

        with st.form('pollination-credentials'):
            project_owner = st.text_input('Project owner', value='aec-tech-hack-2022')
            project_name = st.text_input('Project name', value='viz')
            simulation_name = st.text_input('Simulation name', value='point-in-time')
            simulation_description = st.text_input(
                'Simulation description', value='view analysis')
            api_key = st.text_input(
                'Api key', type='password',
                value=st.session_state.api_key if 'api_key' in st.session_state else '')
            st.session_state.api_key = api_key

            submit = st.form_submit_button('Submit')
            if submit:
                if not all([project_owner, api_key]):
                    st.error('Fill all inputs')
                    return
                if 'epw' not in st.session_state:
                    st.error('Upload EPW.')
                    return

                sky = get_sky(EPW(st.session_state.epw), north_angle)

                job = create_job(
                    {'model': st.session_state.hbjson,
                     'sky': sky},
                    project_owner,
                    project_name,
                    simulation_name,
                    simulation_description,
                    'point-in-time-view',
                    'latest',
                    'ladybug-tools',
                    api_key)

                running_job = job.create()
                time.sleep(2)
                st.session_state.study_url = f'https://app.pollination.cloud/{running_job.owner}/projects/{running_job.project}/studies/{running_job.id}'
                st.success('Simulation successfully submitted to Pollination. Running '
                           ' simulation can be viewed'
                           f' [here]({st.session_state.study_url})')

    if 'study_url' in st.session_state and st.session_state.study_url:

        job = recreate_job(st.session_state.study_url, st.session_state.api_key)

        if request_status(job) != SimStatus.COMPLETE:
            clicked = st.button('Refresh to download results')
            if clicked:
                status = request_status(job)
                st.warning(f'Simulation is {status.name}. You can monitor the progress'
                           f' [here]({st.session_state.study_url})')
        else:
            result_folder = download_output(job, target_folder,
                                            'results', 'results')
            if result_folder.exists():
                # testing hdr to gif workflow
                for file in result_folder.iterdir():
                    if file.suffix == '.HDR':
                        print(file)
                        evalglare_path = Path(r'assets\evalglare\evalglare.exe')
                        eval_hdr_path, dgp, category = eval_hdr(
                            file, target_folder, evalglare_path)

                        gif_path = hdr_to_gif(eval_hdr_path, target_folder)
                        print(gif_path)
                        image = Image.open(gif_path)
                        st.markdown(
                            f'{int(dgp*100)}% probability of {category} glare')
                        st.image(image)


if __name__ == '__main__':
    main()
