
import os
import copy
from ladybug.futil import unzip_file
from ladybug.config import folders
from ladybug.config import folders
from ladybug.futil import preparedir, unzip_file
import requests
import streamlit as st
from pathlib import Path
from honeybee_energy.lib.programtypes import STANDARDS_REGISTRY
from honeybee_energy.lib.programtypes import BUILDING_TYPES
from honeybee.search import filter_array_by_keywords

CLIMATE_ZONES = ('0A', '1A', '2A', '3A', '4A', '5A', '6A', '0B', '1B', '2B', '3B', '4B', '5B', '6B', '3C', '4C', '5C', '7', '8')

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


def apply_lighting_factor(room, lighting_factor):
    if room.properties.energy.program_type.lighting:
        new_program_type = room.properties.energy.program_type.duplicate()
        if room.identifier not in st.session_state.original_lpds:
            st.session_state.original_lpds[room.identifier] = float(room.properties.energy.program_type.lighting.watts_per_area)
        
        new_program_type.lighting.watts_per_area = lighting_factor*(st.session_state.original_lpds[room.identifier])
        room.properties.energy.program_type = new_program_type

def update_properties_dict(room, properties_dict, property_name, parent_key=''):
    updated_dict = copy.deepcopy(properties_dict)  # Use deepcopy to handle nested dicts correctly
    for key, value in properties_dict.items():
        unique_key = f"{parent_key}_{key}" if parent_key else key
        input_key = f"{room.identifier}_{property_name}_{unique_key}"

        if isinstance(value, dict):
            #updated_dict[key] = update_properties_dict(room, value, property_name, unique_key)
            st.write(key)
            st.json(value,expanded=False)
        elif isinstance(value, str):
            continue
        elif isinstance(value, list):
            for v in value:
                st.json(v,expanded=False)
        else:
            # Handling different data types
            new_value = st.text_input(f"{unique_key}:", value=str(value), key=input_key)
            if isinstance(value, float):
                try:
                    updated_dict[key] = float(new_value)
                except ValueError:
                    st.error(f"Invalid input for {unique_key}. Please enter a valid float.")
            elif isinstance(value, int):
                try:
                    updated_dict[key] = int(new_value)
                except ValueError:
                    st.error(f"Invalid input for {unique_key}. Please enter a valid integer.")
            else:
                # Assuming other types are strings
                updated_dict[key] = new_value
    return updated_dict



def get_vintage_loads():
    key_ = "loads" 
    skip =["pre_1980"]
    # Use Streamlit's 'selectbox' to create a dropdown menu for selecting a construction period.
    # 'STANDARDS_REGISTRY' is a list containing different construction periods. The user's selection is stored in vintage.
    # The '6' at the end specifies the default selection index from the 'STANDARDS_REGISTRY' list, making the seventh item the default choice.
    standards_registry_list = list(STANDARDS_REGISTRY)
    standards_registry_list = [x for x in standards_registry_list if x not in skip]
    in_vintage = st.selectbox('Loads year:', standards_registry_list, standards_registry_list.index(st.session_state.vintage_loads)if st.session_state.vintage_loads else standards_registry_list.index(filter_array_by_keywords(standards_registry_list, ["2016"])[0]), key = f"construction_period_{key_}")
    if in_vintage != st.session_state.vintage_loads:
        st.session_state.vintage_loads = in_vintage
        st.session_state.sql_results = None  # reset to have results recomputed

def get_vintage_constructions():
    key_="constructions"
    # Use Streamlit's 'selectbox' to create a dropdown menu for selecting a construction period.
    # 'STANDARDS_REGISTRY' is a list containing different construction periods. The user's selection is stored in vintage.
    # The '6' at the end specifies the default selection index from the 'STANDARDS_REGISTRY' list, making the seventh item the default choice.
    standards_registry_list = list(STANDARDS_REGISTRY)
    in_vintage = st.selectbox('Construction Period:', standards_registry_list, standards_registry_list.index(st.session_state.vintage_constructions)if st.session_state.vintage_constructions else standards_registry_list.index(filter_array_by_keywords(standards_registry_list, ["1980_2004"])[0]), key = f"construction_period_{key_}")
    if in_vintage != st.session_state.vintage_constructions:
        st.session_state.vintage_constructions = in_vintage
        st.session_state.sql_results = None  # reset to have results recomputed

def get_building_type(key_):

    # Similarly, create another dropdown menu for selecting a building type.
    # 'BUILDING_TYPES' is a list of different types of buildings. The user's selection is stored in 'st.session_state.building_type'.
    # Again, '6' is the default selection index, making the seventh item in the 'BUILDING_TYPES' list the default choice.
    building_types_list = list(BUILDING_TYPES)
    in_building_type= st.selectbox('Building Type:', building_types_list, building_types_list.index(st.session_state.building_type)if st.session_state.building_type else 6, key = f"building_type_{key_}")
    if in_building_type != st.session_state.building_type:
        st.session_state.building_type = in_building_type
        st.session_state.sql_results = None  # reset to have results recomputed

def get_climate_zone(key_):

    # Similarly, create another dropdown menu for selecting a building type.
    # 'BUILDING_TYPES' is a list of different types of buildings. The user's selection is stored in 'st.session_state.building_type'.
    # Again, '6' is the default selection index, making the seventh item in the 'BUILDING_TYPES' list the default choice.
    climate_zones_list = list(CLIMATE_ZONES)
    in_climate_zone= st.selectbox('Climate Zone:', climate_zones_list, climate_zones_list.index(st.session_state.climate_zone)if st.session_state.climate_zone else 4, key = f"climate_zone_{key_}")
    if in_climate_zone != st.session_state.climate_zone:
        st.session_state.climate_zone = in_climate_zone
        st.session_state.sql_results = None  # reset to have results recomputed




"""
        if  st.session_state.hb_model and st.session_state.epw_path and st.session_state.ddy_path and not st.session_state.improved_sql_results:
            improved_button_holder = improved_col.empty()
            if improved_button_holder.button('Run Improved Simulation'):
                run_improved_simulation(
                    improved_button_holder,
                    st.session_state.target_folder, st.session_state.user_id,
                    st.session_state.hb_model,
                    st.session_state.epw_path, st.session_state.ddy_path, st.session_state.north
                )

        if st.session_state.appendix_g_summary:
            display_results(
                improved_col, st.session_state.improved_sql_results,
                st.session_state.heat_cop, st.session_state.cool_cop,
                st.session_state.ip_units, st.session_state.normalize,
                st.session_state.appendix_g_summary, "Appendix G summary"
            )
                
        """