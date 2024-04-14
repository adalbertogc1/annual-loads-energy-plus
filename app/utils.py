
import os
from ladybug.futil import unzip_file
from ladybug.config import folders
from ladybug.config import folders
from ladybug.futil import preparedir, unzip_file
import requests
import streamlit as st
from pathlib import Path

def download_file_by_name(url, target_folder, file_name, mkdir=False):
    """Download a file to a directory.

    Args:
        url: A string to a valid URL.
        target_folder: Target folder for download (e.g. c:/ladybug)
        file_name: File name (e.g. testPts.zip).
        mkdir: Set to True to create the directory if doesn't exist (Default: False)
    """
    # create the target directory.
    if not os.path.isdir(target_folder):
        if mkdir:
            preparedir(target_folder)
        else:
            created = preparedir(target_folder, False)
            if not created:
                raise ValueError("Failed to find %s." % target_folder)
    file_path = os.path.join(target_folder, file_name)

    # Set the security protocol to the most recent version
    try:
        # TLS 1.2 is needed to download over https
        requests.packages.urllib3.util.ssl_.DEFAULT_CIPHERS = 'ALL:@SECLEVEL=1'
    except AttributeError:
        # Handle the case when TLS 1.2 is not available
        if url.lower().startswith('https'):
            print('This system lacks the necessary security'
                  ' libraries to download over https.')

    # Attempt to download the file
    try:
        with requests.get(url, stream=True) as response:
            response.raise_for_status()
            with open(file_path, 'wb') as file:
                for chunk in response.iter_content(chunk_size=8192):
                    file.write(chunk)
    except Exception as e:
        raise Exception('Download failed with the error:\n{}'.format(e))


def download_file(url, file_path, mkdir=False):
    """Write a string of data to file.

    Args:
        url: A string to a valid URL.
        file_path: Full path to intended download location (e.g. c:/ladybug/testPts.pts)
        mkdir: Set to True to create the directory if doesn't exist (Default: False)
    """
    # Check if the URL ends with .zip
    if not url.lower().endswith('.zip'):
        raise ValueError("URL does not point to a ZIP file.")

    folder, fname = os.path.split(file_path)
    return download_file_by_name(url, folder, fname, mkdir)


def get_weather_files_from_url(_weather_URL, _folder_= "test/weather"):
    """
    Automatically download a .zip file from a URL where climate data resides,
    unzip the file, and open .epw, .stat, and ddy weather files.
    -

        Args:
            _weather_URL: Text representing the URL at which the climate data resides. 
                To open the a map interface for all publicly availabe climate data,
                use the "LB EPWmap" component.
            _folder_: An optional file path to a directory into which the weather file
                will be downloaded and unziped.  If None, the weather files will be
                downloaded to the ladybug default weather data folder and placed in
                a sub-folder with the name of the weather file location.

        Returns:
            epw_file: The file path of the downloaded epw file.
            stat_file: The file path of the downloaded stat file.
            ddy
    """
    # process the URL and check if it is outdated
    _weather_URL = _weather_URL.strip()
    if _weather_URL.lower().endswith('.zip'):  # onebuilding URL type
        _folder_name = _weather_URL.split('/')[-1][:-4]
    else: # dept of energy URL type
        _folder_name = _weather_URL.split('/')[-2]
        if _weather_URL.endswith('/all'):
            repl_section = '{0}/all'.format(_folder_name)
            new_section = '{0}/{0}.zip'.format(_folder_name)
            _weather_URL = _weather_URL.replace(repl_section, new_section)
            _weather_URL = _weather_URL.replace(
                'www.energyplus.net/weather-download',
                'energyplus-weather.s3.amazonaws.com')
            _weather_URL = _weather_URL.replace(
                'energyplus.net/weather-download',
                'energyplus-weather.s3.amazonaws.com')
            _weather_URL = _weather_URL[:8] + _weather_URL[8:].replace('//', '/')
            msg = 'The weather file URL is out of date.\nThis component ' \
                'is automatically updating it to the newer version:'
            print(msg)
            print(_weather_URL)

    # create default working_dir
    if _folder_ is None:
        _folder_ = folders.default_epw_folder
    print('Files will be downloaded to: {}'.format(_folder_))

    # default file names
    epw = os.path.join(_folder_, _folder_name, _folder_name + '.epw')
    stat = os.path.join(_folder_, _folder_name, _folder_name + '.stat')
    ddy = os.path.join(_folder_, _folder_name, _folder_name + '.ddy')

    # download and unzip the files if they do not exist
    if not os.path.isfile(epw) or not os.path.isfile(stat) or not os.path.isfile(ddy):
        zip_file_path = os.path.join(_folder_, _folder_name, _folder_name + '.zip')
        download_file(_weather_URL, zip_file_path, True)
        unzip_file(zip_file_path)

    # set output
    st.session_state.epw_path = Path(epw)
    st.session_state.ddy_path = Path(ddy)