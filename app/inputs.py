"""Functions for initializing inputs and formatting them for simulation"""
import os
import uuid
import tempfile
from pathlib import Path

import streamlit as st
from honeybee.model import Model
from honeybee_vtk.model import Model as VTKModel
from pollination_streamlit_viewer import viewer
from pollination_streamlit_io import get_hbjson


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



def get_ee_inputs(host: str, container):
    # get the inputs that only affect the display and do not require re-simulation
    

    # Measure # 1
    col1, col2 = container.columns([1, 2])
    ee_heating_disabled= True
    ee_heating_value = 0.75
    if col1.checkbox(label='Heating system (heat pump)', value=False):
        ee_heating_disabled= False
        ee_heating_value = 2.5
    in_heat_cop = col2.number_input(label='Heating COP', min_value=0.0, max_value=6.0, value=ee_heating_value, step=0.05, disabled=ee_heating_disabled)
    if in_heat_cop != st.session_state.heat_cop:
        st.session_state.heat_cop = in_heat_cop
    
    # Measure # 2
    col1, col2 = container.columns([1, 2])
    ee_cooling_disabled= True
    ee_cooling_value = 2.5
    if col1.checkbox(label='Cooling system (inverter)', value=False):
        ee_cooling_disabled= False
        ee_cooling_value = 4.5
    in_cool_cop = col2.number_input(
        label='Cooling COP', min_value=0.0, max_value=6.0, value=ee_cooling_value, step=0.05, disabled = ee_cooling_disabled)
    if in_cool_cop != st.session_state.cool_cop:
        st.session_state.cool_cop = in_cool_cop
    

    # Measure # 3
    col1, col2 = container.columns([1, 2])
    ee_shading_disabled= True
    ee_shading_value = 2.5
    if col1.checkbox(label='Shading system (coming soon)', value=False):
        ee_shading_disabled= False
        ee_shading_value = 4.5



def get_sim_inputs(host: str, container):
    s_col_1, s_col_2 = container.columns([2, 1])

    # set up inputs for north
    in_north = s_col_2.number_input(label='North',step= 10, min_value=0, max_value=360, value=0)
    if in_north != st.session_state.north:
        st.session_state.north = in_north
        st.session_state.sql_results = None  # reset to have results recomputed
    
    ip_help = 'Display output units in kBtu and ft2 instead of kWh and m2.'
    in_ip_units = s_col_2.checkbox(label='IP Units', value=False, help=ip_help)
    if in_ip_units != st.session_state.ip_units:
        st.session_state.ip_units = in_ip_units
    norm_help = 'Normalize all energy values by the gross floor area.'
    in_normalize = s_col_2.checkbox(label='Floor Normalize', value=True, help=norm_help)
    if in_normalize != st.session_state.normalize:
        st.session_state.normalize = in_normalize

    if s_col_1.checkbox(label='Advanced simulation settings', value=False):
        in_terrain_type = s_col_1.selectbox("Terrain type", ['Ocean', 'Country', 'Suburbs', 'Urban', 'City'], index=4,  help="Text for the terrain type in which the model sits.")
        if in_terrain_type != st.session_state.terrain_type:
            st.session_state.terrain_type = in_terrain_type
            st.session_state.sql_results = None  # reset to have results recomputed

        in_timestep = s_col_1.selectbox("Timesteps per hour",[1, 2, 6, 12,60],index=0,  help="An integer for the number of timesteps per hour at which the calculation will be run.")
        if in_timestep != st.session_state.timestep:
            st.session_state.timestep = in_timestep
            st.session_state.sql_results = None  # reset to have results recomputed
        
        in_solar_distribution = s_col_1.selectbox("Solar distribution",options=('MinimalShadowing', 'FullExterior', 'FullInteriorAndExterior', 'FullExteriorWithReflections', 'FullInteriorAndExteriorWithReflections'), 
            index=1,  # Default to 'FullExterior'
            help="Describes how EnergyPlus treats beam solar radiation and reflections from surfaces."
        )
        if in_solar_distribution != st.session_state.solar_distribution:
            st.session_state.solar_distribution = in_solar_distribution
            st.session_state.sql_results = None  # reset to have results recomputed

        in_calculation_frequency = s_col_1.selectbox("Calculation frequency",options=('1', '30'), index=1,  # Default to '30'
            help="Integer for the number of days in each period for which a unique shadow calculation will be performed. ."
        )
        if in_calculation_frequency != st.session_state.calculation_frequency:
            st.session_state.calculation_frequency = in_calculation_frequency
            st.session_state.sql_results = None  # reset to have results recomputed



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
    