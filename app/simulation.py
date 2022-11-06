"""Helper functions to schedule runs on Pollination."""
import streamlit as st
import shutil

from enum import Enum
from zipfile import ZipFile
from pathlib import Path

from pollination_streamlit.api.client import ApiClient
from pollination_streamlit.interactors import Job
from pollination_streamlit.api.client import ApiClient
from pollination_streamlit.interactors import NewJob, Recipe
from queenbee.job.job import JobStatusEnum


class SimStatus(Enum):
    NOTSTARTED = 0
    INCOMPLETE = 1
    COMPLETE = 2
    FAILED = 3
    CANCELLED = 4


def create_job(recipe_args: dict,
               project_owner: str,
               project_name: str,
               simulation_name: str,
               simulation_description: str,
               recipe_name: str,
               recipe_tag: str,
               recipe_owner: str,
               api_key: str,
               ) -> NewJob:
    """Create a Job to run on Pollination.

    Args:
        recipe_args: A dictionary of recipe arguments. Each of this dictionary
            must match with the recipe arguments.
        project_owner: Username on Pollination
        project_name: Name of the project where this job will be run. Example is "demo"
        simulation_name: Name of the simulation. This could be anything.
        simulation_description: Description for the simulation. This could be anything.
        recipe_name: Name of the recipe from Pollination. This must match exactly with
            name of the recipe on Pollination.
        recipe_tag: The version of the recipe you wish to use. Example is "latest".
        recipe_owner: Owner of the recipe. Example is "ladybug-tools"
        api_client: ApiClient object.

    Returns:
        A Job object to run on Pollination.
    """
    api_client: ApiClient = ApiClient(api_token=api_key)

    recipe = Recipe(recipe_owner, recipe_name, recipe_tag, api_client)

    new_job = NewJob(project_owner, project_name, recipe, [],
                     simulation_name, simulation_description, api_client)

    arguments = {}
    model_path = new_job.upload_artifact(recipe_args['model'], '.')
    arguments['model'] = model_path
    arguments['sky'] = recipe_args['sky']
    arguments['metric'] = 'luminance'
    arguments['resolution'] = 800
    arguments['radiance-parameters'] = '-ab 2 -aa 0.25 -ad 512 -ar 16'

    new_job.arguments = [arguments]
    return new_job


def request_status(job: Job) -> SimStatus:
    """Request status of a Job on Pollination.

    args:
        job: A Pollination Job object.

    returns:
        Status of a job on Pollination.
    """

    if job.status.status in [
            JobStatusEnum.pre_processing,
            JobStatusEnum.running,
            JobStatusEnum.created,
            JobStatusEnum.unknown]:
        return SimStatus.INCOMPLETE

    if job.status.status == JobStatusEnum.failed:
        return SimStatus.FAILED

    if job.status.status == JobStatusEnum.cancelled:
        return SimStatus.CANCELLED

    return SimStatus.COMPLETE


def recreate_job(
        job_url: str,
        api_key: str) -> Job:
    """Re-create a Job object from a job URL.

    args:
        job_url: Valid URL of a job on Pollination as a string.
        api_client: ApiClient object containing Pollination credentials.

    returns:
        A Pollination Job object created using the job_url and ApiClient.
    """
    api_client: ApiClient = ApiClient(api_token=api_key)

    url_split = job_url.split('/')
    job_id = url_split[-1]
    project = url_split[-3]
    owner = url_split[-5]

    return Job(owner, project, job_id, api_client)


@st.cache
def download_output(job: Job, target_folder: Path, folder_name: str,
                    output_name: str) -> Path:
    """Download output from a finished Job on Pollination and get a dictionary.

    args:
        job: A Pollination Job object.
        output_folder: Path to the folder where the output will be downloaded.
        folder_name: Name of the sub folder that will be created inside the target
            folder.
        output_name: Name of the output to download from a Pollination job. This you
            find on recipe page on Pollination for the recipe you are using.

    returns:
        Path to the folder where the output is downloaded.
    """

    output_folder = target_folder.joinpath(folder_name)

    if not output_folder.exists():
        output_folder.mkdir(parents=True, exist_ok=True)
    else:
        shutil.rmtree(output_folder)
        output_folder.mkdir(parents=True, exist_ok=True)

    run = job.runs[0]

    res = run.download_zipped_output(output_name)
    with ZipFile(res) as zip_folder:
        zip_folder.extractall(output_folder)

    return output_folder
