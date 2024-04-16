
from ladybug.epw import EPW
from pathlib import Path
import streamlit as st
from utils import get_weather_files_from_url

def new_weather_file():
    """Process a newly-uploaded EPW file."""
    # reset the simulation results and get the file data
    st.session_state.sql_results = None
    st.session_state.epw_path = None
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
                


def load_epw(epw_file):
    epw = EPW(epw_file.as_posix())
    return epw

def create_charts(epw,container):
    
    location = epw.location
    # # write the information to the app
    container.write(f'#### City: {location.city}')
    container.write(f'#### Latitude: {location.latitude}, Longitude: {location.longitude}')
    container.write(f'#### Climate Zone: {epw.ashrae_climate_zone}')

    dbt = epw.dry_bulb_temperature.heat_map()
    diurnal_chart = epw.diurnal_average_chart()

    return dbt, diurnal_chart

def visualize_weather(epw,container):
    dbt, diurnal_chart = create_charts(epw,container)

    container.plotly_chart(diurnal_chart, use_container_width=True)
    container.plotly_chart(dbt, use_container_width=True)



def get_weather_inputs(host: str, container):

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
            st.session_state.epw_path = None
            get_weather_files_from_url(weather_url_)
            st.session_state.sql_results = None  # reset to have results recomputed
    else:
        get_weather_file(w_col_1)

    if st.session_state.epw_path:
        epw = load_epw(epw_file=st.session_state.epw_path)
        st.session_state.climate_zone = epw.ashrae_climate_zone
        if container.checkbox(label='Weather insights', value=False):
            visualize_weather(epw,container)





