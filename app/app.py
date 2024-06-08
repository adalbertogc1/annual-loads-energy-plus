"""The Pollination Annual Loads App."""
import streamlit as st
from pollination_streamlit_io import get_host

from inputs import initialize, get_model_inputs, geometry_wizard
from constructions import assign_constructions
from loads import iterate_rooms_and_display_properties
from hvac import iterate_rooms_hvac
from weather import get_weather_inputs
from simulation import run_baseline_simulation, get_sim_inputs, run_improved_simulation
from outputs import display_baseline_results, display_improved_results
from datetime import datetime
import json
from honeybee_energy.baseline.create import model_to_baseline
from honeybee_energy.baseline.result import appendix_g_summary


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
        tab1, tab2, tab3, tab4, tab5  = in_container.tabs(["Weather", "Constructions", "Loads", "HVAC","Simulation"])

        with tab1:
            st.header("Weather")
            get_weather_inputs(platform, st)

        with tab2:
            st.header("Constructions")
            assign_constructions()
        with tab3:
            st.header("Loads")
            iterate_rooms_and_display_properties()

        with tab4:
            st.header("HVAC")
            iterate_rooms_hvac(st)
        
        with tab5:
            st.header("Simulation Settings")
            get_sim_inputs(platform, st)
        
        out_container.markdown("""---""")  # horizontal divider line between input and output
            
        # preview the model and/or run the simulation
        # simulate the model if the button is pressed
        baseline_col, improved_col = out_container.columns(2)
        # Convert to baseline :
        st.session_state.hb_model_baseline = st.session_state.hb_model.duplicate()
        model_to_baseline(st.session_state.hb_model_baseline ,st.session_state.climate_zone, building_type=st.session_state.building_type, lighting_by_building= st.session_state.lighting_by_building)

        with baseline_col:
            run_baseline_simulation(
                st,
                st.session_state.target_folder, st.session_state.user_id,
                st.session_state.hb_model_baseline,
                st.session_state.epw_path, st.session_state.ddy_path,
                st.session_state.north)
            # create the resulting charts

            display_baseline_results(
                st, st.session_state.baseline_sql_results,
                st.session_state.ip_units, st.session_state.normalize
            )

            #if st.session_state.hb_model_baseline:
            dt = datetime.now().strftime("%Y_%m_%d-%I_%M_%S_%p")
            baseline_col.download_button(label="Download baseline HBJSON",data=json.dumps(st.session_state.hb_model_baseline.to_dict()),file_name=f"HBmodel_{dt}.json",mime="application/json")
        
        with improved_col:
            run_improved_simulation(
                st,
                st.session_state.target_folder, st.session_state.user_id,
                st.session_state.hb_model,
                st.session_state.epw_path, st.session_state.ddy_path,
                st.session_state.north)


            display_improved_results(
                st, 
                st.session_state.improved_sql_results,
                st.session_state.ip_units, st.session_state.normalize
            )

            #if st.session_state.hb_model:
            dt = datetime.now().strftime("%Y_%m_%d-%I_%M_%S_%p")
            improved_col.download_button(label="Download improved HBJSON",data=json.dumps(st.session_state.hb_model.to_dict()),file_name=f"HBmodel_{dt}.json",mime="application/json")

        if st.session_state.improved_sql_results and st.session_state.baseline_sql_results:
            out_container.write('Appendix G summary ({})'.format('kBtu/ft2' if st.session_state.ip_units else 'kWh/m2'))
            st.session_state.appendix_g_summary =appendix_g_summary(st.session_state.sql_improved, st.session_state.sql_baseline,st.session_state.climate_zone,building_type=st.session_state.building_type,electricity_cost=st.session_state.electricity_cost, natural_gas_cost=st.session_state.natural_gas_cost)
            out_container.json(st.session_state.appendix_g_summary)
            

if __name__ == '__main__':
    # get the platform from the query uri
    query = st.query_params
    platform = get_host() or 'web'
    main(platform)

