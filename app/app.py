"""The Pollination Annual Loads App."""
import streamlit as st
from pollination_streamlit_io import get_host

from inputs import initialize, get_sim_inputs, get_model_inputs, geometry_wizard,get_ee_inputs
from constructions import assign_constructions
from loads import iterate_rooms_and_display_properties
from hvac import iterate_rooms_hvac
from weather import get_weather_inputs
from simulation import run_simulation
from outputs import display_results



st.set_page_config(
    page_title='Annual Loads Simulation (E+)',
    page_icon='https://github.com/ladybug-tools/artwork/raw/master/icons_components'
    '/honeybee/png/loadbalance.png',
    initial_sidebar_state='expanded',
)  # type: ignore


def main(platform):
    """Perform the main calculation of the App."""
    # title
    st.header('Annual Loads Simulation (E+)')
    #st.markdown("""---""")  # horizontal divider line between title and input

    # initialize the app and load up all of the inputs
    initialize()
    in_container = st.container()  # container to hold the inputs
    out_container = st.container()  # container to eventually hold the results
    sidebar_container = st.sidebar.container()

    in_model_source = sidebar_container.radio("Select model source:", ("Geometry wizard","HBJSON"))
    if in_model_source == "Geometry wizard":
        geometry_wizard(sidebar_container)
    else:
        get_model_inputs(platform, sidebar_container)


    if st.session_state.hb_model:
        tab1, tab2, tab3, tab4, tab5, tab6  = in_container.tabs(["Constructions","Loads", "HVAC", "Weather", "Energy Efficiency","Simulation"])

        with tab1:
            st.header("Constructions")
            assign_constructions(tab1)

        with tab2:
            st.header("Loads")
            iterate_rooms_and_display_properties()

        with tab3:
            st.header("HVAC")
            iterate_rooms_hvac(st)

        with tab4:
            st.header("Weather")
            get_weather_inputs(platform, st)
        
        with tab5:
            st.header("Energy Efficiency Measures")
            get_ee_inputs(platform, st)
        
        with tab6:
            st.header("Simulation Settings")
            get_sim_inputs(platform, st)
        
        out_container.markdown("""---""")  # horizontal divider line between input and output
            
        # preview the model and/or run the simulation
        run_simulation(
            st.session_state.target_folder, st.session_state.user_id,
            st.session_state.hb_model,
            st.session_state.epw_path, st.session_state.ddy_path, st.session_state.north
        )

        # create the resulting charts
        display_results(
            out_container, st.session_state.sql_results,
            st.session_state.heat_cop, st.session_state.cool_cop,
            st.session_state.ip_units, st.session_state.normalize
        )


if __name__ == '__main__':
    # get the platform from the query uri
    query = st.query_params
    platform = get_host() or 'web'
    main(platform)
