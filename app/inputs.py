"""Functions for initializing inputs and formatting them for simulation"""
import os
import uuid
from pathlib import Path

import streamlit as st

from ladybug.epw import EPW
from honeybee.model import Model
from honeybee_vtk.model import Model as VTKModel

from pollination_streamlit_viewer import viewer
from pollination_streamlit_io import get_hbjson
from utils import get_weather_files_from_url
from honeybee_energy.lib.programtypes import STANDARDS_REGISTRY
from honeybee_energy.lib.programtypes import PROGRAM_TYPES
from honeybee_energy.lib.programtypes import program_type_by_identifier
from honeybee_energy.lib.programtypes import BUILDING_TYPES
from honeybee.search import filter_array_by_keywords
import random
import uuid
import copy
import tempfile
from geometry import geometry_parameters, generate_building, generate_honeybee_model, clear_temp_folder


def initialize():
    """Initialize any of the session state variables if they don't already exist."""
    # user session
    if 'user_id' not in st.session_state:
        st.session_state.user_id = str(uuid.uuid4())[:8]
    if 'target_folder' not in st.session_state:
        st.session_state.target_folder = Path(__file__).parent
    # sim session
    if 'hb_model' not in st.session_state:
        st.session_state.hb_model = None
    if 'vtk_path' not in st.session_state:
        st.session_state.vtk_path = None
    if 'valid_report' not in st.session_state:
        st.session_state.valid_report = None
    if 'epw_path' not in st.session_state:
        st.session_state.epw_path = None
    if 'ddy_path' not in st.session_state:
        st.session_state.ddy_path = None
    if 'north' not in st.session_state:
        st.session_state.north = None
    if 'terrain_type' not in st.session_state:
        st.session_state.terrain_type = None
    if 'timestep' not in st.session_state:
        st.session_state.timestep = None
    if 'solar_distribution' not in st.session_state:
        st.session_state.solar_distribution = None
    if 'calculation_frequency' not in st.session_state:
        st.session_state.calculation_frequency = None
    # loads session
    if 'vintage' not in st.session_state:
        st.session_state.vintage = None
    if 'building_type' not in st.session_state:
        st.session_state.building_type = None

    # geometry wizard
    if "temp_folder" not in st.session_state: 
        st.session_state.temp_folder = Path(tempfile.mkdtemp()) #not going to generate a local file, just creates a temporary file in memory
    if "footprint" not in st.session_state: 
        st.session_state.footprint = None
    if "no_of_floors" not in st.session_state: 
        st.session_state.no_of_floors = None
    if "floor_height" not in st.session_state: 
        st.session_state.floor_height = None      
    if "wwr" not in st.session_state: 
        st.session_state.wwr = None
    if "building_geometry" not in st.session_state: 
        st.session_state.building_geometry = None  

    # output session
    if 'heat_cop' not in st.session_state:
        st.session_state.heat_cop = None
    if 'cool_cop' not in st.session_state:
        st.session_state.cool_cop = None
    if 'ip_units' not in st.session_state:
        st.session_state.ip_units = False
    if 'upload_ddy' not in st.session_state:
        st.session_state.upload_ddy = False
    if 'normalize' not in st.session_state:
        st.session_state.normalize = True
    if 'sql_results' not in st.session_state:
        st.session_state.sql_results = None


def new_weather_file():
    """Process a newly-uploaded EPW file."""
    # reset the simulation results and get the file data
    st.session_state.sql_results = None
    epw_file = st.session_state.epw_data
    if epw_file:
        # save EPW in data folder
        epw_path = Path(
            f'./{st.session_state.target_folder}/data/'
            f'{st.session_state.user_id}/{epw_file.name}'
        )
        epw_path.parent.mkdir(parents=True, exist_ok=True)
        epw_path.write_bytes(epw_file.read())
        # create a DDY file from the EPW
        ddy_file = epw_path.as_posix().replace('.epw', '.ddy')
        epw_obj = EPW(epw_path.as_posix())
        epw_obj.to_ddy(ddy_file)
        ddy_path = Path(ddy_file)
        # set the session state variables
        st.session_state.epw_path = epw_path
        st.session_state.ddy_path = ddy_path
    else:
        st.session_state.epw_path = None
        st.session_state.ddy_path = None


def new_design_file():
    """Process a newly-uploaded DDY file."""
    # reset the simulation results and get the file data
    st.session_state.sql_results = None
    ddy_file = st.session_state.ddy_data
    if ddy_file:
        # save DDY in data folder
        ddy_path = Path(
            f'./{st.session_state.target_folder}/data/'
            f'{st.session_state.user_id}/{ddy_file.name}'
        )
        ddy_path.parent.mkdir(parents=True, exist_ok=True)
        ddy_path.write_bytes(ddy_file.read())
        # set the session state variables
        st.session_state.ddy_path = ddy_path

def get_weather_file(column):
    """Get the EPW weather file from the App input."""
    # upload weather file
    column.file_uploader(
        'Weather file (EPW)', type=['epw'],
        on_change=new_weather_file, key='epw_data',
        help='Select an EPW weather file to be used in the simulation.'
    )
    if st.session_state.epw_path:
        if column.checkbox(label= 'Upload DDY (optional)', value=False):
                column.file_uploader(
            'Design weather (DDY)', type=['ddy'],
            on_change=new_design_file, key='ddy_data',
            help='Select an DDY weather file to be used for sizing components.'
        )


def new_model():
    """Process a newly-uploaded Honeybee Model file."""
    # reset the simulation results and get the file data
    st.session_state.vtk_path = None
    st.session_state.valid_report = None
    st.session_state.sql_results = None
    # load the model object from the file data
    if 'hbjson' in st.session_state['hbjson_data']:
        hbjson_data = st.session_state['hbjson_data']['hbjson']
        st.session_state.hb_model = Model.from_dict(hbjson_data)


def get_model(column):
    """Get the Model input from the App input."""
    # load the model object from the file data
    with column:
        hbjson_data = get_hbjson(key='hbjson_data', on_change=new_model)
    if st.session_state.hb_model is None and hbjson_data is not None \
            and 'hbjson' in hbjson_data:
        st.session_state.hb_model = Model.from_dict(hbjson_data['hbjson'])


def generate_vtk_model(hb_model: Model, container):
    """Generate a VTK preview of an input model."""
    if not st.session_state.vtk_path:
        directory = os.path.join(
            st.session_state.target_folder.as_posix(),
            'data', st.session_state.user_id
        )
        if not os.path.isdir(directory):
            os.makedirs(directory)
        hbjson_path = hb_model.to_hbjson(hb_model.identifier, directory)
        vtk_model = VTKModel.from_hbjson(hbjson_path)
        vtk_path = vtk_model.to_vtkjs(folder=directory, name=hb_model.identifier)
        st.session_state.vtk_path = vtk_path
    vtk_path = st.session_state.vtk_path
    with container:
        viewer(content=Path(vtk_path).read_bytes(), key='vtk_preview_model')


def generate_model_validation(hb_model: Model, container):
    """Generate a Model validation report from an input model."""
    if not st.session_state.valid_report:
        report = hb_model.check_all(raise_exception=False, detailed=False)
        st.session_state.valid_report = report
    report = st.session_state.valid_report
    if report == '':
        container.success('Congratulations! Your Model is valid!')
    else:
        container.warning('Your Model is invalid for the following reasons:')
        container.code(report, language='console')


def get_model_info(hb_model: Model, container):
    col1,col2,col3 = container.columns(3)
    with col1:
        if st.session_state.ip_units:
            st.metric(label=f"Total Volume (ft3)",value=round(35.3147*hb_model.volume,1))
        else:
            st.metric(label=f"Total Volume (m3)",value=hb_model.volume)
    with col2:
        if st.session_state.ip_units:
            st.metric(label="Total area (ft2)",value=round(10.7639*hb_model.floor_area, 1))
        else:
            st.metric(label="Total area (m2)",value=hb_model.floor_area)
    with col3:
        if st.session_state.ip_units:
            st.metric(label="Total glazing area (ft2)",value=round(10.7639*hb_model.exterior_aperture_area,1))
        else:
            st.metric(label="Total glazing area (m2)",value=round(hb_model.exterior_aperture_area,1))


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

def update_room_program_types(hb_model, vintage, building_type):
    room_prog = filter_array_by_keywords(PROGRAM_TYPES, [vintage, building_type], False)
    for room in hb_model.rooms:
        if 'room_prog' not in room.user_data or room.user_data['room_prog'] not in room_prog:
            room.user_data['room_prog'] = random.choice(room_prog)
            room.properties.energy.program_type = program_type_by_identifier(room.user_data['room_prog'])

def iterate_rooms_and_display_properties():
    """Iterates through rooms in a Honeybee model, displaying and allowing the modification of various properties such as lighting, 
    people gains, equipment gains, service hot water, infiltration, ventilation, and setpoints. It requires a valid Honeybee model object 
    stored in the session state and uses Streamlit UI elements to interactively display and update room properties based on user input.
    
    The function first checks if the provided model is a valid Honeybee Model object. Then, it allows the user to select construction 
    period and building type from predefined lists, which are used to filter applicable room programs. Each room's properties are 
    displayed within a Streamlit expander, allowing for modifications to attributes such as display name, room program, and various 
    gains (lighting, people, electric equipment, gas equipment, service hot water, infiltration, and ventilation). The modifications are 
    applied to the model in real-time, enabling dynamic updates based on user interaction.
    
    Parameters: None
    Returns: None - This function directly modifies the session state and uses Streamlit components to display UI elements. """
    

    # Use Streamlit's 'selectbox' to create a dropdown menu for selecting a construction period.
    # 'STANDARDS_REGISTRY' is a list containing different construction periods. The user's selection is stored in 'st.session_state.vintage'.
    # The '6' at the end specifies the default selection index from the 'STANDARDS_REGISTRY' list, making the seventh item the default choice.
    in_vintage = st.selectbox('Construction Period:', list(STANDARDS_REGISTRY), 6)
    if in_vintage != st.session_state.vintage:
        st.session_state.vintage = in_vintage
        #st.session_state.sql_results = None  # reset to have results recomputed

    # Similarly, create another dropdown menu for selecting a building type.
    # 'BUILDING_TYPES' is a list of different types of buildings. The user's selection is stored in 'st.session_state.building_type'.
    # Again, '6' is the default selection index, making the seventh item in the 'BUILDING_TYPES' list the default choice.
    in_building_type= st.selectbox('Building Type:', list(BUILDING_TYPES), 6)
    if in_building_type != st.session_state.building_type:
        st.session_state.building_type = in_building_type
        #st.session_state.sql_results = None  # reset to have results recomputed

    # Filter room programs based on the selected construction period and building type.
    # 'filter_array_by_keywords' is a function that likely takes a list of items ('PROGRAM_TYPES') and a list of keywords (selected vintage and building type)
    # and returns a subset of 'PROGRAM_TYPES' that match the keywords. The 'False' parameter might control the filtering behavior or case sensitivity.
    room_prog = filter_array_by_keywords(PROGRAM_TYPES, [st.session_state.vintage, st.session_state.building_type], False)
    
    # Iterate over each room in the Honeybee model.
    # 'st.session_state.hb_model.rooms' contains a list of rooms in the model. For each room, various properties will be displayed and can be modified.
    # Display each room's properties using expanders.
    for room in st.session_state.hb_model.rooms:
        with st.expander(f"Room identifier: {room.identifier}"):
            st.write("Floor area")
            st.code(room.floor_area)

            # Create a text input field for editing the room's display name.
            # A unique key for the input field is generated using the room's identifier to ensure that the input field's state is maintained uniquely across different rooms.
            room.display_name = st.text_input(f"Display name for {room.identifier}", value=room.display_name, key=f"display_name_{room.identifier}")

            # Generate a unique key for the room program selectbox using the room's identifier.
            # This ensures that each selectbox in the loop is treated as a distinct widget by Streamlit.
            selectbox_key = f"room_prog_{room.identifier}"
            # Determine the current index of the room's program type in the 'room_prog' list to set it as the default selection in the selectbox.
            # If the room's program type identifier is not in 'room_prog', default to the first item (index 0).
            current_prog_index = room_prog.index(room.properties.energy.program_type.identifier) if room.properties.energy.program_type.identifier in room_prog else room_prog.index(random.choice(room_prog))#0
            # Create a selectbox for changing the room's program type, with the current program type pre-selected.
            new_room_prog = st.selectbox("Room Program", room_prog, index=current_prog_index, key=selectbox_key)
            
            # Check if the user has selected a different program type from the dropdown.
            # If so, update the room's program type to the new selection. Otherwise, keep it unchanged.
            if new_room_prog != room.properties.energy.program_type.identifier:
                new_program_type = program_type_by_identifier(new_room_prog)
                room.properties.energy.program_type = new_program_type
                st.session_state.sql_results = None  # reset to have results recomputed
            else:
                # Duplicate the program type to ensure any modifications are made on a new instance, preserving the original object's state.
                new_program_type = room.properties.energy.program_type
            
            new_program_type = room.properties.energy.program_type.duplicate()
            
            # Check if the new program type has a lighting object associated with it.
            if new_program_type.lighting:
                st.divider() # Add a visual divider in the Streamlit interface to separate this section.
                st.write("Lighting gains") # Display a header or title for this section.
                # Duplicate the lighting object from the new program type. This is done to avoid modifying the original object directly.
                # Modifying a duplicate allows changes to be made safely without affecting other parts of the program that might be using the original object.
                lighting = new_program_type.lighting.duplicate()  # Duplicate the lighting object
                # Convert the lighting object's properties to a dictionary for easier manipulation.
                # This allows us to access and modify its properties as key-value pairs, which is more straightforward than dealing with the object's methods and attributes directly.
                lighting_dict = lighting.to_dict()
                # Update the lighting properties based on user input or some other logic.
                # 'update_properties_dict' is a function that takes the room object, the current lighting properties as a dictionary, and a string indicating the type of properties being updated ("lighting").
                # This function modify the properties based on user input collected elsewhere in the application.
                updated_lighting_dict = update_properties_dict(room, lighting_dict, "lighting")
                # Check if 'watts_per_area' is a key in the updated dictionary of lighting properties.
                # If it is, update the 'watts_per_area' property of the lighting object with the new value.
                if 'watts_per_area' in updated_lighting_dict:
                    lighting.watts_per_area = updated_lighting_dict['watts_per_area']
                    #st.session_state.sql_results = None  # reset to have results recomputed
                if 'return_air_fraction' in updated_lighting_dict:
                    lighting.return_air_fraction = updated_lighting_dict['return_air_fraction']
                    #st.session_state.sql_results = None  # reset to have results recomputed
                if 'radiant_fraction' in updated_lighting_dict:
                    lighting.radiant_fraction = updated_lighting_dict['radiant_fraction']
                    #st.session_state.sql_results = None  # reset to have results recomputed
                if 'visible_fraction' in updated_lighting_dict:
                    lighting.visible_fraction = updated_lighting_dict['visible_fraction']
                    #st.session_state.sql_results = None  # reset to have results recomputed
                if 'baseline_watts_per_area' in updated_lighting_dict:
                    lighting.baseline_watts_per_area = updated_lighting_dict['baseline_watts_per_area']
                    #st.session_state.sql_results = None  # reset to have results recomputed
                
                # After updating the lighting object with new properties, assign it back to the new program type.
                # This ensures that the program type uses the updated lighting configuration.
                new_program_type.lighting = lighting

            if new_program_type.people:
                st.divider()
                st.write("People gains")
                people = new_program_type.people.duplicate()  # Duplicate the people object
                people_dict = people.to_dict()
                updated_people_dict = update_properties_dict(room, people_dict, "people")

                if 'people_per_area' in updated_people_dict:
                    people.people_per_area = updated_people_dict['people_per_area']
                    #st.session_state.sql_results = None  # reset to have results recomputed
                if 'radiant_fraction' in updated_people_dict:
                    people.radiant_fraction = updated_people_dict['radiant_fraction']
                    #st.session_state.sql_results = None  # reset to have results recomputed
                
                new_program_type.people = people

                if new_program_type.electric_equipment:
                    st.divider()
                    st.write("electric_equipment gains")
                    electric_equipment = new_program_type.electric_equipment.duplicate()  # Duplicate the electric_equipment object
                    electric_equipment_dict = electric_equipment.to_dict()
                    updated_electric_equipment_dict = update_properties_dict(room, electric_equipment_dict, "electric_equipment")

                    if 'watts_per_area' in updated_electric_equipment_dict:
                        electric_equipment.watts_per_area = updated_electric_equipment_dict['watts_per_area']
                        #st.session_state.sql_results = None  # reset to have results recomputed
                    if 'radiant_fraction' in updated_electric_equipment_dict:
                        electric_equipment.radiant_fraction = updated_electric_equipment_dict['radiant_fraction']
                        #st.session_state.sql_results = None  # reset to have results recomputed
                    if 'latent_fraction' in updated_electric_equipment_dict:
                        electric_equipment.latent_fraction = updated_electric_equipment_dict['latent_fraction']
                        #st.session_state.sql_results = None  # reset to have results recomputed
                    if 'lost_fraction' in updated_electric_equipment_dict:
                        electric_equipment.lost_fraction = updated_electric_equipment_dict['lost_fraction']
                        #st.session_state.sql_results = None  # reset to have results recomputed
                   
                    new_program_type.electric_equipment = electric_equipment
           
            if new_program_type.gas_equipment:
                st.divider()
                st.write("gas_equipment gains")
                gas_equipment = new_program_type.gas_equipment.duplicate()  # Duplicate the gas_equipment object
                gas_equipment_dict = gas_equipment.to_dict()
                updated_gas_equipment_dict = update_properties_dict(room, gas_equipment_dict, "gas_equipment")

                if 'watts_per_area' in updated_gas_equipment_dict:
                    gas_equipment.watts_per_area = updated_gas_equipment_dict['watts_per_area']
                    #st.session_state.sql_results = None  # reset to have results recomputed
                if 'radiant_fraction' in updated_gas_equipment_dict:
                    gas_equipment.radiant_fraction = updated_gas_equipment_dict['radiant_fraction']
                    #st.session_state.sql_results = None  # reset to have results recomputed
                if 'latent_fraction' in updated_gas_equipment_dict:
                    gas_equipment.latent_fraction = updated_gas_equipment_dict['latent_fraction']
                    #st.session_state.sql_results = None  # reset to have results recomputed
                if 'lost_fraction' in updated_gas_equipment_dict:
                    gas_equipment.lost_fraction = updated_gas_equipment_dict['lost_fraction']
                    #st.session_state.sql_results = None  # reset to have results recomputed

                
                new_program_type.gas_equipment = gas_equipment

            if new_program_type.service_hot_water:
                st.divider()
                st.write("service_hot_water gains")
                service_hot_water = new_program_type.service_hot_water.duplicate()  # Duplicate the service_hot_water object
                service_hot_water_dict = service_hot_water.to_dict()
                updated_service_hot_water_dict = update_properties_dict(room, service_hot_water_dict, "service_hot_water")

                if 'service_hot_water_per_area' in updated_service_hot_water_dict:
                    service_hot_water.service_hot_water_per_area = updated_service_hot_water_dict['service_hot_water_per_area']
                    #st.session_state.sql_results = None  # reset to have results recomputed
                if 'flow_per_area' in updated_service_hot_water_dict:
                    service_hot_water.flow_per_area = updated_service_hot_water_dict['flow_per_area']
                    #st.session_state.sql_results = None  # reset to have results recomputed
                if 'target_temperature' in updated_service_hot_water_dict:
                    service_hot_water.target_temperature = updated_service_hot_water_dict['target_temperature']
                    #st.session_state.sql_results = None  # reset to have results recomputed
                if 'sensible_fraction' in updated_service_hot_water_dict:
                    service_hot_water.sensible_fraction = updated_service_hot_water_dict['sensible_fraction']
                    #st.session_state.sql_results = None  # reset to have results recomputed
                if 'latent_fraction' in updated_service_hot_water_dict:
                    service_hot_water.latent_fraction = updated_service_hot_water_dict['latent_fraction']
                    #st.session_state.sql_results = None  # reset to have results recomputed
                
                new_program_type.service_hot_water = service_hot_water

            if new_program_type.infiltration:
                st.divider()
                st.write("infiltration gains")
                infiltration = new_program_type.infiltration.duplicate()  # Duplicate the infiltration object
                infiltration_dict = infiltration.to_dict()
                updated_infiltration_dict = update_properties_dict(room, infiltration_dict, "infiltration")

                if 'flow_per_exterior_area' in updated_infiltration_dict:
                    infiltration.flow_per_exterior_area = updated_infiltration_dict['flow_per_exterior_area']
                    #st.session_state.sql_results = None  # reset to have results recomputed
                new_program_type.infiltration = infiltration    
            
            if new_program_type.ventilation:
                st.divider()
                st.write("ventilation gains")
                ventilation = new_program_type.ventilation.duplicate()  # Duplicate the ventilation object
                ventilation_dict = ventilation.to_dict()
                updated_ventilation_dict = update_properties_dict(room, ventilation_dict, "ventilation")

                if 'flow_per_person' in updated_ventilation_dict:
                    ventilation.flow_per_person = updated_ventilation_dict['flow_per_person']
                    #st.session_state.sql_results = None  # reset to have results recomputed
                if 'flow_per_area' in updated_ventilation_dict:
                    ventilation.flow_per_area = updated_ventilation_dict['flow_per_area']
                    #st.session_state.sql_results = None  # reset to have results recomputed
                
                new_program_type.ventilation = ventilation
            
            if new_program_type.setpoint:
                st.divider()
                st.write("setpoint gains")
                setpoint = new_program_type.setpoint.duplicate()  # Duplicate the setpoint object
                setpoint_dict = setpoint.to_dict()
                updated_setpoint_dict = update_properties_dict(room, setpoint_dict, "setpoint")

                if 'setpoint_per_area' in updated_setpoint_dict:
                    setpoint.setpoint_per_area = updated_setpoint_dict['setpoint_per_area']
                    #st.session_state.sql_results = None  # reset to have results recomputed
                
                new_program_type.setpoint = setpoint

            # Assign the updated lighting object back to the new ProgramType
            if room.properties.energy.program_type != new_program_type:
                room.properties.energy.program_type = new_program_type
                st.session_state.sql_results = None  # reset to have results recomputed




def get_model_inputs(host: str, container):
    """Get all of the inputs for the simulation."""
    # get the input model
    m_col_1, m_col_2 = container.columns([2, 1])
    get_model(m_col_1)
    # add options to preview the model in 3D and validate it
    if st.session_state.hb_model:
        if m_col_2.checkbox(label='Preview Model', value=False):
            generate_vtk_model(st.session_state.hb_model, container)
        if m_col_2.checkbox(label='Validate Model', value=False):
            generate_model_validation(st.session_state.hb_model, container)
        if m_col_2.checkbox(label='Model info', value=False):
            get_model_info(st.session_state.hb_model, container)





def get_sim_inputs(host: str, container):

    w_col_1, w_col_2 = container.columns([2, 1])

    # get the input EPW and DDY files
    weather_method_in = w_col_1.radio("Weather data source:", ("EPW Map", "EPW File"))
    if weather_method_in == "EPW Map":
        url = "https://www.ladybug.tools/epwmap/"
        w_col_1.markdown("*Go to [EPW Map](%s) and copy the URL of any weather station.*" % url)
        weather_url_ = w_col_1.text_input('EPW Map URL', 'https://climate.onebuilding.org/WMO_Region_4_North_and_Central_America/MEX_Mexico/CMX_Cuidad_de_Mexico/MEX_CMX_Cuidad.Mexico-Mexico.City.Intl.AP-Juarez.Intl.AP.766793_TMYx.2004-2018.zip')
        # simulate the model if the button is pressed
        button_holder = w_col_1.empty()
        if button_holder.button('Download weather file'):
            get_weather_files_from_url(weather_url_)
            st.session_state.sql_results = None  # reset to have results recomputed
    else:
        
        get_weather_file(w_col_1)

    # set up inputs for north
    in_north = w_col_2.number_input(label='North',step= 10, min_value=0, max_value=360, value=0)
    if in_north != st.session_state.north:
        st.session_state.north = in_north
        st.session_state.sql_results = None  # reset to have results recomputed

    if w_col_2.checkbox(label='Advanced simulation settings', value=False):
        in_terrain_type = w_col_2.selectbox("Terrain type", ['Ocean', 'Country', 'Suburbs', 'Urban', 'City'], index=4)
        if in_terrain_type != st.session_state.terrain_type:
            st.session_state.terrain_type = in_terrain_type
            st.session_state.sql_results = None  # reset to have results recomputed

        in_timestep = w_col_2.selectbox("Timesteps per hour",[1, 2, 6, 12,60],index=0)
        if in_timestep != st.session_state.timestep:
            st.session_state.timestep = in_timestep
            st.session_state.sql_results = None  # reset to have results recomputed
        
        in_solar_distribution = w_col_2.selectbox("Solar distribution",options=('MinimalShadowing', 'FullExterior', 'FullInteriorAndExterior', 'FullExteriorWithReflections', 'FullInteriorAndExteriorWithReflections'), 
            index=1,  # Default to 'FullExterior'
            help="Describes how EnergyPlus treats beam solar radiation and reflections from surfaces."
        )
        if in_solar_distribution != st.session_state.solar_distribution:
            st.session_state.solar_distribution = in_solar_distribution
            st.session_state.sql_results = None  # reset to have results recomputed

        in_calculation_frequency = w_col_2.selectbox("Calculation frequency",options=('1', '30'), index=1,  # Default to '30'
            help="Integer for the number of days in each period for which a unique shadow calculation will be performed. ."
        )
        if in_calculation_frequency != st.session_state.calculation_frequency:
            st.session_state.calculation_frequency = in_calculation_frequency
            st.session_state.sql_results = None  # reset to have results recomputed



    # get the inputs that only affect the display and do not require re-simulation
    col1, col2, col3 = container.columns(3)
    in_heat_cop = col1.number_input(
        label='Heating COP', min_value=0.0, max_value=6.0, value=1.0, step=0.05)
    if in_heat_cop != st.session_state.heat_cop:
        st.session_state.heat_cop = in_heat_cop
    in_cool_cop = col2.number_input(
        label='Cooling COP', min_value=0.0, max_value=6.0, value=1.0, step=0.05)
    if in_cool_cop != st.session_state.cool_cop:
        st.session_state.cool_cop = in_cool_cop
    ip_help = 'Display output units in kBtu and ft2 instead of kWh and m2.'
    in_ip_units = col3.checkbox(label='IP Units', value=False, help=ip_help)
    if in_ip_units != st.session_state.ip_units:
        st.session_state.ip_units = in_ip_units
    norm_help = 'Normalize all energy values by the gross floor area.'
    in_normalize = col3.checkbox(label='Floor Normalize', value=True, help=norm_help)
    if in_normalize != st.session_state.normalize:
        st.session_state.normalize = in_normalize


def geometry_wizard(container):
    container.markdown("Generate the model based on the following inputs:" )
    g_col_1, g_col_2 = container.columns([2, 1])
    geometry_parameters(g_col_1)
    # load the just designed model if the button is pressed
    button_holder = container.empty()
    if button_holder.button('Comfirm model geometry'):
        clear_temp_folder()
        generate_building(st.session_state.footprint, st.session_state.floor_height, st.session_state.no_of_floors)
        generate_honeybee_model()
        st.session_state.sql_results = None  # reset to have results recomputed
    # add options to preview the model in 3D and validate it
    if st.session_state.hb_model:
        if g_col_2.checkbox(label='Preview Model', value=False):
            generate_vtk_model(st.session_state.hb_model, container)
        if g_col_2.checkbox(label='Validate Model', value=False):
            generate_model_validation(st.session_state.hb_model, container)
        if g_col_2.checkbox(label='Model info', value=False):
            get_model_info(st.session_state.hb_model, container)
    