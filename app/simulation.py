"""Functions for running the simulation and performing initial result postprocessing."""
import os
import subprocess

from ladybug.futil import write_to_file_by_name
from ladybug.sql import SQLiteResult
from ladybug.datacollection import MonthlyCollection
from ladybug.header import Header
from ladybug.analysisperiod import AnalysisPeriod
from ladybug.datatype.energyintensity import EnergyIntensity
from ladybug.color import Color
from honeybee.units import conversion_factor_to_meters
from honeybee_energy.baseline.create import model_to_baseline
from honeybee_energy.result.loadbalance import LoadBalance
from honeybee_energy.simulation.parameter import SimulationParameter
from honeybee_energy.result.err import Err
from honeybee_energy.run import prepare_idf_for_simulation, output_energyplus_files
from honeybee_energy.writer import energyplus_idf_version
from honeybee_energy.config import folders as energy_folders
import streamlit as st


VALIDTIMESTEPS = (1, 2, 3, 4, 5, 6, 10, 12, 15, 20, 30, 60)


REPORTINGFREQUENCIES = ("Annual", "Monthly")



# Names of EnergyPlus outputs that will be requested and parsed to make graphics
cool_out = 'Zone Ideal Loads Supply Air Total Cooling Energy'
heat_out = 'Zone Ideal Loads Supply Air Total Heating Energy'
light_out = 'Zone Lights Electricity Energy'
el_equip_out = 'Zone Electric Equipment Electricity Energy'
gas_equip_out = 'Zone Gas Equipment NaturalGas Energy'
process1_out = 'Zone Other Equipment Total Heating Energy'
process2_out = 'Zone Other Equipment Lost Heat Energy'
shw_out = 'Water Use Equipment Heating Energy'
gl_el_equip_out = 'Zone Electric Equipment Total Heating Energy'
gl_gas_equip_out = 'Zone Gas Equipment Total Heating Energy'
gl1_shw_out = 'Water Use Equipment Zone Sensible Heat Gain Energy'
gl2_shw_out = 'Water Use Equipment Zone Latent Gain Energy'


def simulate_idf(idf_file_path, epw_file_path=None, expand_objects=True):
    """Run an IDF file through EnergyPlus and report the STDOUT in the app.

    Args:
        idf_file_path: The full path to an IDF file.
        epw_file_path: The full path to an EPW file. Note that inputting None here
            is only appropriate when the simulation is just for design days and has
            no weather file run period. (Default: None).
        expand_objects: If True, the IDF run will include the expansion of any
            HVAC Template objects in the file before beginning the simulation.
            This is a necessary step whenever there are HVAC Template objects in
            the IDF but it is unnecessary extra time when they are not
            present. (Default: True).
    """
    # check and prepare the input files
    directory = prepare_idf_for_simulation(idf_file_path, epw_file_path)

    # run the simulation
    cmds = [energy_folders.energyplus_exe, '-i', energy_folders.energyplus_idd_path]
    if epw_file_path is not None:
        cmds.append('-w')
        cmds.append(os.path.abspath(epw_file_path))
    if expand_objects:
        cmds.append('-x')
    process = subprocess.Popen(cmds, cwd=directory, stdout=subprocess.PIPE)

    # print the stdout in the app
    stdout_style = '<style> .std {font-size: 1rem ; margin: 0rem ; ' \
        'padding: 0rem ; color: white ; background-color: black ;} </style>'
    st.markdown(stdout_style, unsafe_allow_html=True)
    with st.empty():
        current_stdout = []
        for line in iter(lambda: process.stdout.readline(), b""):
            std_line = line.decode("utf-8")
            current_stdout.append(std_line)
            stdout_lines = ['<p class="std">{}</p>'.format(li) for li in current_stdout]
            st.markdown(''.join(stdout_lines), unsafe_allow_html=True)
            if len(current_stdout) == 6:
                current_stdout.pop(0)
        st.write('')  # clear the EnergyPlus stdout

    # output the simulation files
    return output_energyplus_files(directory)


def data_to_load_intensity(room_dict, data_colls, floor_area, data_type, mults=None):
    """Convert data collections from EnergyPlus to a single load intensity collection.

    Args:
        data_colls: A list of monthly data collections for an energy term.
        floor_area: The total floor area of the rooms, used to compute EUI.
        data_type: Text for the data type of the collections (eg. "Cooling").
        mults: An optional dictionary of Room identifiers and integers for
            the multipliers of the honeybee Rooms.
    """
    if len(data_colls) != 0:
        # first try adding the data to the room dictionary
        rel_key = 'Zone' if 'Zone' in data_colls[0].header.metadata else 'System'
        for dat in data_colls:
            try:
                z_id = dat.header.metadata[rel_key]
                if rel_key == 'Zone':
                    r_prop = room_dict[z_id]
                elif ' IDEAL LOADS AIR SYSTEM' in z_id:  # E+ HVAC Templates
                    r_prop = room_dict[z_id.split(' IDEAL LOADS AIR SYSTEM')[0]]
                elif '..' in z_id:  # convention used for service hot water
                    r_prop = room_dict[z_id.split('..')[-1]]
                else:
                    r_prop = room_dict[z_id]
                r_prop[-1][data_type] = (dat.total * r_prop[2]) / r_prop[1]
            except KeyError:  # no results of this type for the Room
                pass
        # next, build up the monthly collection of total values
        if mults is not None:
            if rel_key == 'Zone':
                rel_mults = [mults[data.header.metadata['Zone']] for data in data_colls]
                data_colls = [dat * mul for dat, mul in zip(data_colls, rel_mults)]
        total_vals = [sum(month_vals) / floor_area for month_vals in zip(*data_colls)]
    else:  # just make a "filler" collection of 0 values
        total_vals = [0] * 12
    meta_dat = {'type': data_type}
    total_head = Header(EnergyIntensity(), 'kWh/m2', AnalysisPeriod(), meta_dat)
    return MonthlyCollection(total_head, total_vals, range(12))


def load_sql_data(sql_path, model):
    """Load and process the SQL data from the simulation and store it in memory.

    Args:
        sql_path: Path to the SQLite file output from an EnergyPlus simulation.
        model: The honeybee model object used to create the SQL results.
    """
    # load up the floor area, get the model units, and the room multipliers
    con_fac = conversion_factor_to_meters(model.units) ** 2
    floor_areas, rd = [], {}
    for room in model.rooms:
        if not room.exclude_floor_area:
            fa = room.floor_area * room.multiplier * con_fac
            floor_areas.append(fa)
            rd[room.identifier.upper()] = [room.display_name, fa, room.multiplier, {}]
    floor_area = sum(floor_areas)
    assert floor_area != 0, 'Model has no floors with which to compute EUI.'
    mults = {rm.identifier.upper(): rm.multiplier for rm in model.rooms}
    mults = None if all(mul == 1 for mul in mults.values()) else mults

    # get data collections for each energy use term
    sql_obj = SQLiteResult(sql_path)
    cool_init = sql_obj.data_collections_by_output_name(cool_out)
    heat_init = sql_obj.data_collections_by_output_name(heat_out)
    light_init = sql_obj.data_collections_by_output_name(light_out)
    elec_eq_init = sql_obj.data_collections_by_output_name(el_equip_out)
    gas_equip_init = sql_obj.data_collections_by_output_name(gas_equip_out)
    process1_init = sql_obj.data_collections_by_output_name(process1_out)
    process2_init = sql_obj.data_collections_by_output_name(process2_out)
    shw_init = sql_obj.data_collections_by_output_name(shw_out)

    # convert the results to a single monthly EUI data collection
    cooling = data_to_load_intensity(rd, cool_init, floor_area, 'Cooling')
    heating = data_to_load_intensity(rd, heat_init, floor_area, 'Heating')
    lighting = data_to_load_intensity(rd, light_init, floor_area, 'Lighting', mults)
    equip = data_to_load_intensity(
        rd, elec_eq_init, floor_area, 'Electric Equipment', mults)
    load_terms = [cooling, heating, lighting, equip]
    load_colors = [
        Color(4, 25, 145), Color(153, 16, 0), Color(255, 255, 0), Color(255, 121, 0)
    ]

    # add gas equipment if it is there
    if len(gas_equip_init) != 0:
        gas_equip = data_to_load_intensity(
            rd, gas_equip_init, floor_area, 'Gas Equipment', mults)
        load_terms.append(gas_equip)
        load_colors.append(Color(255, 219, 128))
    # add process load if it is there
    process = []
    if len(process1_init) != 0:
        process1 = data_to_load_intensity(
            rd, process1_init, floor_area, 'Process', mults)
        process2 = data_to_load_intensity(
            rd, process2_init, floor_area, 'Process', mults)
        process = process1 + process2
        load_terms.append(process)
        load_colors.append(Color(135, 135, 135))
    # add hot water if it is there
    hot_water = []
    if len(shw_init) != 0:
        hot_water = data_to_load_intensity(
            rd, shw_init, floor_area, 'Service Hot Water', mults)
        load_terms.append(hot_water)
        load_colors.append(Color(255, 0, 0))

    # create a monthly load balance
    bal_obj = LoadBalance.from_sql_file(model, sql_path)
    balance = bal_obj.load_balance_terms(True, True)

    # return a dictionary containing all relevant results of the simulation
    return {
        'room_results': rd,
        'floor_area': floor_area,
        'load_terms': load_terms,
        'load_colors': load_colors,
        'balance': balance
    }

def get_simulation_parameters(ddy_path = None):
    # create simulation parameters for the coarsest/fastest E+ sim possible
    sim_par = SimulationParameter()
    sim_par.timestep = sim_par.timestep = st.session_state.timestep if st.session_state.timestep else 1
    sim_par.shadow_calculation.solar_distribution = st.session_state.solar_distribution if st.session_state.solar_distribution else 'FullExterior' 
    sim_par.shadow_calculation.calculation_frequency = st.session_state.calculation_frequency if st.session_state.calculation_frequency else int(30)
    sim_par.terrain_type = str(st.session_state.terrain_type) if st.session_state.terrain_type else str("City")
    sim_par.output.add_zone_energy_use()
    sim_par.output.reporting_frequency = "Monthly" #st.session_state.reporting_frequency
    sim_par.output.add_output(gl_el_equip_out)
    sim_par.output.add_output(gl_gas_equip_out)
    sim_par.output.add_output(gl1_shw_out)
    sim_par.output.add_output(gl2_shw_out)
    sim_par.output.add_gains_and_losses('Total')
    sim_par.output.add_surface_energy_flow()
    # assign design days to the simulation parameters, if available
    if ddy_path:
        sim_par.sizing_parameter.add_from_ddy(ddy_path.as_posix())
    return sim_par

def simulation_job(sim_par, hb_model, target_folder,user_id, epw_path,sim_type, north =None):
    
    if north:
        sim_par.north_angle = float(north)
    # create the strings for simulation parameters and model
    ver_str = energyplus_idf_version() if energy_folders.energyplus_version \
        is not None else ''
    sim_par_str = sim_par.to_idf()
    model_str = hb_model.to.idf(hb_model, patch_missing_adjacencies=True)
    idf_str = '\n\n'.join([ver_str, sim_par_str, model_str])

    # write the final string into an IDF
    directory = os.path.join(target_folder, 'data', user_id,sim_type)
    idf = os.path.join(directory, 'in.idf')
    write_to_file_by_name(directory, 'in.idf', idf_str, True)

    # run the IDF through EnergyPlus
    sql, zsz, rdd, html, err = simulate_idf(idf, epw_path.as_posix())
    if html is None and err is not None:  # something went wrong; parse the errors
        err_obj = Err(err)
        print(err_obj.file_contents)
        for error in err_obj.fatal_errors:
            raise Exception(error)
        
    return sql


def run_baseline_simulation(container,target_folder, user_id, hb_model, epw_path, ddy_path):
    """Build the IDF file from a Model and run it through EnergyPlus.

    Args:
        target_folder: Text for the target folder out of which the simulation will run.
        user_id: A unique user ID for the session, which will be used to ensure
            other simulations do not overwrite this one.
        hb_model: A Honeybee Model object to be simulated.
        epw_path: Path to an EPW file to be used in the simulation.
        ddy_path: Path to a DDY file to be used in the simulation.
        north: Integer for the angle from the Y-axis where North is.
    """
    # check to be sure there is a model
    if not hb_model or not epw_path or not ddy_path:# or \
            #st.session_state.baseline_sql_results is not None:
        return

    #st.session_state.hb_model_baseline = hb_model.duplicate()

    baseline_button_holder = container.empty()
    if baseline_button_holder.button('Run Baseline Simulation'):
        # check to be sure that the Model has Rooms
        assert len(hb_model.rooms) != 0, \
            'Model has no Rooms and cannot be simulated in EnergyPlus.'

        # Convert to baseline if required:
        model_to_baseline(hb_model,st.session_state.climate_zone, building_type=st.session_state.building_type, lighting_by_building= st.session_state.lighting_by_building)

        # create simulation parameters for the coarsest/fastest E+ sim possible
        sim_par = get_simulation_parameters(ddy_path)

        st.session_state.sql_baseline  =  simulation_job(sim_par, hb_model, target_folder,user_id, epw_path,"baseline")
        
        if st.session_state.sql_baseline  is not None and os.path.isfile(st.session_state.sql_baseline ):
            st.session_state.baseline_sql_results = load_sql_data(st.session_state.sql_baseline , hb_model)
            #baseline_button_holder.write('')


def run_improved_simulation(container, target_folder, user_id, hb_model, epw_path, ddy_path, north):
    """Build the IDF file from a Model and run it through EnergyPlus.

    Args:
        target_folder: Text for the target folder out of which the simulation will run.
        user_id: A unique user ID for the session, which will be used to ensure
            other simulations do not overwrite this one.
        hb_model: A Honeybee Model object to be simulated.
        epw_path: Path to an EPW file to be used in the simulation.
        ddy_path: Path to a DDY file to be used in the simulation.
        north: Integer for the angle from the Y-axis where North is.
    """
    # check to be sure there is a model
    if not hb_model or not epw_path or not ddy_path:# or \
            #st.session_state.improved_sql_results is not None:
        return
    

    improved_button_holder = container.empty()
    if improved_button_holder.button('Run Improved Simulation'):
        #  if st.session_state.sql_baseline:
        
        # check to be sure that the Model has Rooms
        assert len(hb_model.rooms) != 0, \
            'Model has no Rooms and cannot be simulated in EnergyPlus.'

        # create simulation parameters for the coarsest/fastest E+ sim possible
        sim_par = get_simulation_parameters(ddy_path)
        st.session_state.sql_improved =  simulation_job(sim_par, hb_model, target_folder,user_id, epw_path,"improved", north)
        
        if st.session_state.sql_improved is not None and os.path.isfile(st.session_state.sql_improved):
            st.session_state.improved_sql_results = load_sql_data(st.session_state.sql_improved, hb_model)
            #improved_button_holder.write('')



def get_sim_inputs(host: str, container):
    s_col_1, s_col_2 = container.columns([2, 1])


    # set up inputs for north
    in_north = s_col_2.number_input(label='North',step= 10, min_value=0, max_value=360, value=0)
    if in_north != st.session_state.north:
        st.session_state.north = in_north
        st.session_state.improved_sql_results = None  # reset to have results recomputed
    
    ip_help = 'Display output units in kBtu and ft2 instead of kWh and m2.'
    in_ip_units = s_col_2.checkbox(label='IP Units', value=False, help=ip_help)
    if in_ip_units != st.session_state.ip_units:
        st.session_state.ip_units = in_ip_units
    norm_help = 'Normalize all energy values by the gross floor area.'
    in_normalize = s_col_2.checkbox(label='Floor Normalize', value=True, help=norm_help)
    if in_normalize != st.session_state.normalize:
        st.session_state.normalize = in_normalize

    in_reporting_frequency = s_col_2.radio("Reporting Frequency: ", REPORTINGFREQUENCIES, index =  0, horizontal= True, disabled= False)
    if in_reporting_frequency != st.session_state.reporting_frequency:
        st.session_state.reporting_frequency = in_reporting_frequency

    s_col_1.text("ASHRAE Baseline Settings:")
    in_lighting_by_building = s_col_1.checkbox(label='Use lighting by building?', value=False, help= "Assigns lighting gains for the entire building base solely on building type. Useful for quick assessments.")
    if in_lighting_by_building != st.session_state.lighting_by_building:
        st.session_state.in_lighting_by_building = in_lighting_by_building
        st.session_state.hb_model_baseline = None
        #st.session_state.improved_sql_results = None
    s_col_1_1,s_col_1_2 = s_col_1.columns(2)
    in_electricity_cost = s_col_1_1.number_input("Electricity cost",step= 0.01, min_value=0.0, max_value= 10.0, value=st.session_state.electricity_cost)
    if in_electricity_cost != st.session_state.electricity_cost:
        st.session_state.electricity_cost =in_electricity_cost
        st.session_state.pci_target = None
        st.session_state.appendix_g_summary = None

    in_natural_gas_cost = s_col_1_2.number_input("Electricity cost",step= 0.01, min_value=0.0, max_value= 10.0, value=st.session_state.natural_gas_cost)
    if in_natural_gas_cost != st.session_state.natural_gas_cost:
        st.session_state.natural_gas_cost =in_natural_gas_cost
        st.session_state.pci_target = None
        st.session_state.appendix_g_summary = None
    


    if s_col_1.checkbox(label='Advanced simulation settings', value=False, help = "Deafult settings are optimized for speed over fidelity. Change only for specific cases."):
        #
        
        in_terrain_type = s_col_1.selectbox("Terrain type", ['Ocean', 'Country', 'Suburbs', 'Urban', 'City'], index=4,  help="Text for the terrain type in which the model sits.")
        if in_terrain_type != st.session_state.terrain_type:
            st.session_state.terrain_type = in_terrain_type


        in_timestep = s_col_1.selectbox("Timesteps per hour",VALIDTIMESTEPS,index=0,  help="An integer for the number of timesteps per hour at which the calculation will be run.")
        if in_timestep != st.session_state.timestep:
            st.session_state.timestep = in_timestep

        
        in_solar_distribution = s_col_1.selectbox("Solar distribution",options=('MinimalShadowing', 'FullExterior', 'FullInteriorAndExterior', 'FullExteriorWithReflections', 'FullInteriorAndExteriorWithReflections'), 
            index=1,  # Default to 'FullExterior'
            help="Describes how EnergyPlus treats beam solar radiation and reflections from surfaces."
        )
        if in_solar_distribution != st.session_state.solar_distribution:
            st.session_state.solar_distribution = in_solar_distribution


        in_calculation_frequency = s_col_1.selectbox("Calculation frequency",options=('1', '30'), index=1,  # Default to '30'
            help="Integer for the number of days in each period for which a unique shadow calculation will be performed. ."
        )
        if in_calculation_frequency != st.session_state.calculation_frequency:
            st.session_state.calculation_frequency = in_calculation_frequency

    