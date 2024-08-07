
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
VINTAGE_HVAC_OPTIONS = ('DOE_Ref_Pre_1980', 'DOE_Ref_1980_2004', 'ASHRAE_2004', 'ASHRAE_2007', 'ASHRAE_2010', 'ASHRAE_2013', 'ASHRAE_2016', 'ASHRAE_2019')

# Function to delete a session state variable
def delete_session_state_variable(variable_name):
    if variable_name in st.session_state:
        del st.session_state[variable_name]


def find_partial_matches(data_list, keyword):
    # Convert keyword to lowercase to make the search case-insensitive
    keyword_lower = keyword.lower()
    # This function returns all elements containing the keyword as a substring, regardless of case
    return [item for item in data_list if keyword_lower in item.lower()]

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



def update_properties_dict(room, properties_dict, property_name, parent_key=''):
    updated_dict = copy.deepcopy(properties_dict)  # Use deepcopy to handle nested dicts correctly
    for key, value in updated_dict.items():
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



def get_vintage_loads(container,key_ = "loads"):
     
    # Use Streamlit's 'selectbox' to create a dropdown menu for selecting a construction period.
    # 'STANDARDS_REGISTRY' is a list containing different construction periods. The user's selection is stored in vintage.
    # The '6' at the end specifies the default selection index from the 'STANDARDS_REGISTRY' list, making the seventh item the default choice.
    standards_registry_list = list(STANDARDS_REGISTRY)
    #standards_registry_list = [x for x in standards_registry_list if x not in skip]
    in_vintage = container.selectbox('Loads year:', standards_registry_list, standards_registry_list.index(st.session_state.vintage_loads)if st.session_state.vintage_loads else standards_registry_list.index(filter_array_by_keywords(standards_registry_list, ["2016"])[0]), key = f"construction_period_{key_}")
    if in_vintage != st.session_state.vintage_loads:
        st.session_state.vintage_loads = in_vintage


def get_vintage_constructions(container,key_="constructions"):
    
    # Use Streamlit's 'selectbox' to create a dropdown menu for selecting a construction period.
    # 'STANDARDS_REGISTRY' is a list containing different construction periods. The user's selection is stored in vintage.
    # The '6' at the end specifies the default selection index from the 'STANDARDS_REGISTRY' list, making the seventh item the default choice.
    standards_registry_list = list(STANDARDS_REGISTRY)
    in_vintage = container.selectbox('Construction Period:', standards_registry_list, standards_registry_list.index(st.session_state.vintage_constructions)if st.session_state.vintage_constructions else standards_registry_list.index(filter_array_by_keywords(standards_registry_list, ["1980_2004"])[0]), key = f"construction_period_{key_}")
    if in_vintage != st.session_state.vintage_constructions:
        delete_session_state_variable("selected_construction_set")
        st.session_state.vintage_constructions = in_vintage
        

def get_building_code1(container,key_="building_code"):
    help = "Select the ASHRAE 90.1 version."
    # Similarly, create another dropdown menu for selecting a building type.
    # 'BUILDING_TYPES' is a list of different types of buildings. The user's selection is stored in 'st.session_state.building_type'.
    # Again, '6' is the default selection index, making the seventh item in the 'BUILDING_TYPES' list the default choice.
    vintage_hvac_list = list(VINTAGE_HVAC_OPTIONS)
    standards_registry_list = list(STANDARDS_REGISTRY)
    
    in_building_code= container.selectbox('Building Code:', standards_registry_list, standards_registry_list.index(st.session_state.vintage_loads)if st.session_state.vintage_loads else 6, key = f"building_code_{key_}",help=help)
    
    if in_building_code != st.session_state.vintage_loads:
        st.session_state.vintage_loads = in_building_code
        st.session_state.vintage_constructions = in_building_code
        st.session_state.vintage_hvac = find_partial_matches(vintage_hvac_list, in_building_code)[-1]
        #TODO fix the logic so if a vintage exists it does not change the current model
        #TODO check the need to select the same code 2x for change it on the app

def update_building_code():
    vintage_hvac_list = list(VINTAGE_HVAC_OPTIONS)
    in_building_code = st.session_state.building_code_selection
    if in_building_code != st.session_state.vintage_loads:
        st.session_state.vintage_loads = in_building_code
        st.session_state.vintage_constructions = in_building_code
        st.session_state.vintage_hvac = find_partial_matches(vintage_hvac_list, in_building_code)[-1]

def get_building_code(container, key_="building_code"):
    help = "Select the ASHRAE 90.1 version."
    standards_registry_list = list(STANDARDS_REGISTRY)

    if st.session_state.vintage_loads:
        default_value = st.session_state.vintage_loads
    else:
        default_value = standards_registry_list[1]  # Default to the seventh item if not set
        st.session_state.vintage_loads = default_value
        st.session_state.vintage_constructions =default_value
        st.session_state.vintage_hvac =find_partial_matches(list(VINTAGE_HVAC_OPTIONS), default_value)[-1]

    container.selectbox(
        'Building Code:', 
        standards_registry_list, 
        index=standards_registry_list.index(default_value),
        key="building_code_selection",
        on_change=update_building_code,
        help=help
    )


def get_building_type(container,key_="loads"):

    # Similarly, create another dropdown menu for selecting a building type.
    # 'BUILDING_TYPES' is a list of different types of buildings. The user's selection is stored in 'st.session_state.building_type'.
    # Again, '6' is the default selection index, making the seventh item in the 'BUILDING_TYPES' list the default choice.
    building_types_list = list(BUILDING_TYPES)
    in_building_type= container.selectbox('Building Type:', building_types_list, building_types_list.index(st.session_state.building_type)if st.session_state.building_type else 6, key = f"building_type_{key_}")
    if in_building_type != st.session_state.building_type:
        st.session_state.building_type = in_building_type
        #st.session_state.baseline_sql_results = None
        #st.session_state.improved_sql_results = None




def get_climate_zone_bkp(container,key_="construction"):

    # Similarly, create another dropdown menu for selecting a building type.
    # 'BUILDING_TYPES' is a list of different types of buildings. The user's selection is stored in 'st.session_state.building_type'.
    # Again, '6' is the default selection index, making the seventh item in the 'BUILDING_TYPES' list the default choice.
    climate_zones_list = list(CLIMATE_ZONES)
    in_climate_zone= container.selectbox('Climate Zone:', climate_zones_list, climate_zones_list.index(st.session_state.climate_zone)if st.session_state.climate_zone else 4, key = f"climate_zone_{key_}")
    if in_climate_zone != st.session_state.climate_zone:
        st.session_state.climate_zone = in_climate_zone
        #st.session_state.baseline_sql_results = None
        #st.session_state.improved_sql_results = None

def get_climate_zone(container,key_="construction"):

    # Similarly, create another dropdown menu for selecting a building type.
    # 'BUILDING_TYPES' is a list of different types of buildings. The user's selection is stored in 'st.session_state.building_type'.
    # Again, '6' is the default selection index, making the seventh item in the 'BUILDING_TYPES' list the default choice.
    #climate_zones_list = list(CLIMATE_ZONES)
    #in_climate_zone= container.selectbox('Climate Zone:', climate_zones_list, climate_zones_list.index(st.session_state.climate_zone)if st.session_state.climate_zone else 4, key = f"climate_zone_{key_}")
    if not st.session_state.climate_zone:
        st.session_state.climate_zone = '4A'
        #st.session_state.baseline_sql_results = None
        #st.session_state.improved_sql_results = None

###CHANGES MADE ALONE####

def serialize_model(model):
    # Convert the model to a serializable format (e.g., JSON)
    model_json = model.to_json()
    return model_json

def deserialize_model(model_json):
    # Convert the JSON back to a model
    model = model.from_json(model_json)
    return model


def save_model(model):
    model_json = serialize_model(model)
    with open("model.json", "w") as file:
        file.write(model_json)

def provide_download_link():
    save_model(st.session_state.hb_model)
    with open("model.json", "rb") as file:
        st.download_button(label="Download Model", data=file, file_name="model.json", mime="application/json")

def upload_model():
    uploaded_file = st.file_uploader("Upload Model", type=["json"])
    if uploaded_file is not None:
        model_json = uploaded_file.read().decode("utf-8")
        st.session_state.hb_model = deserialize_model(model_json)
        st.success("Model uploaded successfully.")
