
import streamlit as st
from utils import get_vintage_constructions, update_properties_dict
from honeybee.search import filter_array_by_keywords
from honeybee_energy.lib.constructionsets import CONSTRUCTION_SETS
from honeybee_energy.lib.constructionsets import construction_set_by_identifier
from honeybee_energy.construction.window import WindowConstruction
from honeybee_energy.constructionset import ApertureConstructionSet
from honeybee_energy.constructionset import WallConstructionSet,RoofCeilingConstructionSet
from honeybee_energy.constructionset import ConstructionSet
from honeybee_energy.construction.opaque import OpaqueConstruction

def update_room_construction_set():
    new_construction_set = construction_set_by_identifier(st.session_state.selected_construction_set)
    for room in st.session_state.hb_model.rooms:
        room.properties.energy.construction_set = new_construction_set
    st.session_state.improved_sql_results = None
    st.session_state.baseline_sql_results = None


def assign_constructions():
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


    trimmed_zone = "ClimateZone" + st.session_state.climate_zone[0]
    #building_construction_set = filter_array_by_keywords(CONSTRUCTION_SETS, [st.session_state.vintage_constructions,trimmed_zone ], False)
    building_construction_set = filter_array_by_keywords(CONSTRUCTION_SETS, [trimmed_zone], False)

    if st.checkbox("Import constructions from building code?",value=False):
        # Generate a unique key for the room program selectbox using the room's identifier.
        # This ensures that each selectbox in the loop is treated as a distinct widget by Streamlit.
        #if 'selected_construction_set' not in st.session_state:
        if not st.session_state.selected_construction_set:
            st.session_state.selected_construction_set = filter_array_by_keywords(building_construction_set, ["Mass"])[0]
 
        # Create the selectbox with the session state key
        st.selectbox(
            "Construction set", 
            building_construction_set, 
            index=building_construction_set.index(st.session_state.selected_construction_set), 
            key='selected_construction_set', 
            on_change=update_room_construction_set
        )
        
    # Iterate over each room in the Honeybee model.
    # 'st.session_state.hb_model.rooms' contains a list of rooms in the model. For each room, various properties will be displayed and can be modified.
    # Display each room's properties using expanders.
    for room in st.session_state.hb_model.rooms:
        with st.expander(f"Room identifier: {room.identifier}"):
            
            # Check if the new program type has a lighting object associated with it.
            if room.properties.energy.construction_set.wall_set:
                construction_set_name = "wall_set"
                st.divider() 
                st.subheader("Wall Set") 
                st.write("Exterior construction")

                with st.container():
                    st.write("Update External Wall Construction:")
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        new_r_value = st.number_input("New R value",min_value=0.001 ,value= 1.0, key=f"new_r_value_{room.identifier}")
                    with col2:
                        new_thermal_absorptance = st.number_input("New Thermal Absorptance", min_value= 0.1, max_value=1.0,value=0.9, key=f"new_ta_{room.identifier}")
                    with col3:
                        new_solar_absorptance = st.number_input("New Solar Absorptance", min_value= 0.1, max_value=1.0,value=0.7, key=f"new_sa_{room.identifier}")
                    

                    if st.button("Update external wall construction", key=f"update_external_wall_construction_{room.identifier}"):
                        new_exterior_wall_construction = OpaqueConstruction.from_simple_parameters(
                            f"new_opaque_construction_{room.identifier}",
                            new_r_value,
                            roughness='MediumRough',
                            thermal_absorptance=new_thermal_absorptance,
                            solar_absorptance=new_solar_absorptance
                        )

                        current_construction_set = room.properties.energy.construction_set

                        new_wall_set = WallConstructionSet(
                            exterior_construction=new_exterior_wall_construction,
                            interior_construction=current_construction_set.wall_set.interior_construction,
                            ground_construction=current_construction_set.wall_set.ground_construction
                        )

                        new_construction_set = ConstructionSet(
                            "new_construction_set",
                            wall_set=new_wall_set,
                            floor_set=current_construction_set.floor_set,
                            roof_ceiling_set=current_construction_set.roof_ceiling_set,
                            aperture_set=current_construction_set.aperture_set,
                            door_set=current_construction_set.door_set,
                            shade_construction=current_construction_set.shade_construction,
                            air_boundary_construction=current_construction_set.air_boundary_construction
                        )

                        room.properties.energy.construction_set = new_construction_set
                        st.success("External wall constructions updated successfully!")

                exterior_construction = room.properties.energy.construction_set.wall_set.exterior_construction
                st.text_input("Display name",exterior_construction.display_name, disabled = True, key = f"{construction_set_name}_exterior_construction_display_name_{room.identifier}")
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.text_input("Current U-value",exterior_construction.u_value, disabled = True,  key = f"{construction_set_name}_wall_set_u_value_{room.identifier}" )
                with col2:
                    st.text_input("Current Solar Reflectance",exterior_construction.outside_solar_reflectance, disabled = True,  key = f"{construction_set_name}_wall_set_construction_outside_solar_reflectance_{room.identifier}" )
                with col3:
                    st.text_input("Current Outside Emissivity",exterior_construction.outside_emissivity, disabled = True,  key = f"{construction_set_name}_wall_set_outside_emissivity_{room.identifier}" )

                exterior_construction_dict = exterior_construction.to_dict()
                update_properties_dict(room, exterior_construction_dict, "exterior_construction")
                
                

                st.divider() 
                st.write("Interior construction")
                
                with st.container():
                    st.write("Update Internal Wall Construction:")
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        new_r_value = st.number_input("New R value",min_value=0.001 ,value= 1.0, key=f"new_interior_wall_r_value_{room.identifier}")
                    with col2:
                        new_thermal_absorptance = st.number_input("New Thermal Absorptance", min_value= 0.1, max_value=1.0,value=0.9, key=f"new_interior_wall_ta_{room.identifier}")
                    with col3:
                        new_solar_absorptance = st.number_input("New Solar Absorptance", min_value= 0.1, max_value=1.0,value=0.7, key=f"new_interior_wall_sa_{room.identifier}")
                    

                    if st.button("Update internal wall construction", key=f"update_internal_wall_construction_{room.identifier}"):
                        new_interior_wall_construction = OpaqueConstruction.from_simple_parameters(
                            f"new_interior_opaque_construction_{room.identifier}",
                            new_r_value,
                            roughness='MediumRough',
                            thermal_absorptance=new_thermal_absorptance,
                            solar_absorptance=new_solar_absorptance
                        )

                        current_construction_set = room.properties.energy.construction_set

                        new_wall_set = WallConstructionSet(
                            exterior_construction=current_construction_set.wall_set.exterior_construction,
                            interior_construction=new_interior_wall_construction,
                            ground_construction=current_construction_set.wall_set.ground_construction
                        )

                        new_construction_set = ConstructionSet(
                            "new_construction_set",
                            wall_set=new_wall_set,
                            floor_set=current_construction_set.floor_set,
                            roof_ceiling_set=current_construction_set.roof_ceiling_set,
                            aperture_set=current_construction_set.aperture_set,
                            door_set=current_construction_set.door_set,
                            shade_construction=current_construction_set.shade_construction,
                            air_boundary_construction=current_construction_set.air_boundary_construction
                        )

                        room.properties.energy.construction_set = new_construction_set
                        st.success("Internal wall constructions updated successfully!")

                interior_construction = room.properties.energy.construction_set.wall_set.interior_construction
                st.text_input("Display name",interior_construction.display_name, disabled = True, key = f"{construction_set_name}_interior_construction_display_name_{room.identifier}")
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.text_input("Current U-value",interior_construction.u_value, disabled = True,  key = f"{construction_set_name}_interior_wall_set_u_value_{room.identifier}" )
                with col2:
                    st.text_input("Current Solar Reflectance",interior_construction.outside_solar_reflectance, disabled = True,  key = f"{construction_set_name}_interior_wall_set_construction_outside_solar_reflectance_{room.identifier}" )
                with col3:
                    st.text_input("Current Outside Emissivity",interior_construction.outside_emissivity, disabled = True,  key = f"{construction_set_name}_interior_wall_set_outside_emissivity_{room.identifier}" )

                interior_construction_dict = interior_construction.to_dict()
                update_properties_dict(room, interior_construction_dict, "interior_construction")
                
            
            if room.properties.energy.construction_set.floor_set:
                construction_set_name = "floor_set"
                st.divider() 
                st.subheader("Floor Set") 
                st.write("Ground construction")
                ground_construction = room.properties.energy.construction_set.floor_set.ground_construction
                st.text_input("Display name",ground_construction.display_name, disabled = True, key = f"{construction_set_name}_ground_construction_display_name_{room.identifier}")
                st.text_input("U-value",ground_construction.u_value, disabled = True, key = f"{construction_set_name}_ground_construction_u_value_{room.identifier}" )
                ground_construction_dict = ground_construction.to_dict()
                update_properties_dict(room, ground_construction_dict, "{construction_set_name}_ground_construction")
                

            if room.properties.energy.construction_set.roof_ceiling_set:
                construction_set_name = "roof_ceiling_set"
                st.divider() 
                st.subheader("Roof Ceiling Set") 
                st.write("Exterior construction")

                if st.button("Need help understanding the inputs?",key=f"roof_ceiling_set_info_{room.identifier}"):
                    st.info(
                        "Here's a quick guide to the key terms:\n\n"
                        "**R-value**: The R-value measures a material's resistance to heat flow. A higher R-value "
                        "means better insulation. It's calculated as the inverse of the U-value: R = 1/U.\n\n"
                        "**U-value**: This describes how much heat passes through a material. A lower U-value indicates "
                        "better insulation. It's calculated as the inverse of the R-value: U = 1/R.\n\n"
                        "**Solar Absorptance (α)**: The fraction of solar energy absorbed by the material. High "
                        "absorptance means more heat is absorbed, contributing to a warmer surface.\n\n"
                        "**Solar Reflectance (ρ)**: The fraction of solar energy reflected by the material. It’s related "
                        "to solar absorptance as: Reflectance = 1 - Absorptance. Higher reflectance means the material stays cooler.\n\n"
                        "**Thermal Absorptance (αᵗ)**: This is the fraction of long-wave (thermal) radiation absorbed by the surface. "
                        "It shows how well the material retains heat from surrounding surfaces.\n\n"
                        "**Outside Emissivity (ε)**: Emissivity describes how effectively a surface emits absorbed heat as thermal radiation. "
                        "For opaque materials, emissivity is usually similar to thermal absorptance, meaning that materials with high absorptance "
                        "also tend to radiate heat efficiently."
                    )
                
                '''exterior_construction = room.properties.energy.construction_set.roof_ceiling_set.exterior_construction
                st.text_input("Display name",exterior_construction.display_name, disabled = True, key = f"{construction_set_name}_exterior_construction_display_name_{room.identifier}")
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.text_input("U-value",exterior_construction.u_value, disabled = True,  key = f"{construction_set_name}_roof_construction_u_value_{room.identifier}" )
                with col2:
                    st.text_input("Solar Reflectance",exterior_construction.outside_solar_reflectance, disabled = True,  key = f"{construction_set_name}_roof_construction_outside_solar_reflectance_{room.identifier}" )
                with col3:
                    st.text_input("Outside Emissivity",exterior_construction.outside_emissivity, disabled = True,  key = f"{construction_set_name}_roof_construction_outside_emissivity_{room.identifier}" )
                exterior_construction_dict = exterior_construction.to_dict()
                update_properties_dict(room, exterior_construction_dict, "exterior_construction")'''
                
                with st.container():
                    st.write("Update Exterior Roof Construction:")
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        new_r_value = st.number_input("New R value",min_value=0.001 ,value= 1.0, key=f"new_exterior_roof_r_value_{room.identifier}")
                    with col2:
                        new_thermal_absorptance = st.number_input("New Thermal Absorptance", min_value= 0.1, max_value=1.0,value=0.9, key=f"new_exterior_roof_ta_{room.identifier}")
                    with col3:
                        new_solar_absorptance = st.number_input("New Solar Absorptance", min_value= 0.1, max_value=1.0,value=0.7, key=f"new_exterior_roof_sa_{room.identifier}")
                    

                    if st.button("Update exterior roof construction", key=f"update_exterior_roof_construction_{room.identifier}"):
                        new_exerior_roof_construction = OpaqueConstruction.from_simple_parameters(
                            f"new_exterior_roof_construction_{room.identifier}",
                            new_r_value,
                            roughness='MediumRough',
                            thermal_absorptance=new_thermal_absorptance,
                            solar_absorptance=new_solar_absorptance
                        )

                        current_construction_set = room.properties.energy.construction_set

                        new_roof_ceiling_set = RoofCeilingConstructionSet(
                            exterior_construction=new_exerior_roof_construction,
                            interior_construction=current_construction_set.roof_ceiling_set.interior_construction,
                            ground_construction=current_construction_set.roof_ceiling_set.ground_construction
                        )

                        new_construction_set = ConstructionSet(
                            "new_construction_set",
                            wall_set=current_construction_set.wall_set,
                            floor_set=current_construction_set.floor_set,
                            roof_ceiling_set=new_roof_ceiling_set,
                            aperture_set=current_construction_set.aperture_set,
                            door_set=current_construction_set.door_set,
                            shade_construction=current_construction_set.shade_construction,
                            air_boundary_construction=current_construction_set.air_boundary_construction
                        )

                        room.properties.energy.construction_set = new_construction_set
                        st.success("Exterior Roof constructions updated successfully!")

                exterior_construction = room.properties.energy.construction_set.roof_ceiling_set.exterior_construction
                st.text_input("Display name",exterior_construction.display_name, disabled = True, key = f"{construction_set_name}_exterior_roof_construction_display_name_{room.identifier}")
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.text_input("Current U-value",exterior_construction.u_value, disabled = True,  key = f"{construction_set_name}_roof_set_u_value_{room.identifier}" )
                with col2:
                    st.text_input("Current Solar Reflectance",exterior_construction.outside_solar_reflectance, disabled = True,  key = f"{construction_set_name}_roof_set_construction_outside_solar_reflectance_{room.identifier}" )
                with col3:
                    st.text_input("Current Outside Emissivity",exterior_construction.outside_emissivity, disabled = True,  key = f"{construction_set_name}_roof_set_outside_emissivity_{room.identifier}" )

                exterior_construction_dict = exterior_construction.to_dict()
                update_properties_dict(room, exterior_construction_dict, "exterior_construction")
                
                
            if room.properties.energy.construction_set.aperture_set:
                construction_set_name = "aperture_set"
                st.divider() 
                st.subheader("Aperture Set") 
                st.write("Window construction")

                with st.container():
                    st.write("Update Window Construction:")
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        new_u_value = st.number_input("New U-factor", value=1.0, min_value=0.0, max_value=3.0, key=f"new_u_value_{room.identifier}")
                    with col2:
                        new_shgc = st.number_input("New SHGC", value=0.5, key=f"new_shgc_{room.identifier}")
                    with col3:
                        new_vt = st.number_input("New Visible Transmittance", value=0.6, key=f"new_vt_{room.identifier}")

                    if st.button("Update window construction", key=f"update_window_construction_{room.identifier}"):
                        new_window_construction = WindowConstruction.from_simple_parameters(
                            f"new_window_construction_{room.identifier}",
                            u_factor=float(new_u_value),
                            shgc=float(new_shgc),
                            vt=float(new_vt)
                        )

                        current_construction_set = room.properties.energy.construction_set

                        new_aperture_set = ApertureConstructionSet(
                            window_construction=new_window_construction,
                            skylight_construction=current_construction_set.aperture_set.skylight_construction,
                            operable_construction=current_construction_set.aperture_set.operable_construction
                        )

                        new_construction_set = ConstructionSet(
                            "new_construction_set",
                            wall_set=current_construction_set.wall_set,
                            floor_set=current_construction_set.floor_set,
                            roof_ceiling_set=current_construction_set.roof_ceiling_set,
                            aperture_set=new_aperture_set,
                            door_set=current_construction_set.door_set,
                            shade_construction=current_construction_set.shade_construction,
                            air_boundary_construction=current_construction_set.air_boundary_construction
                        )

                        room.properties.energy.construction_set = new_construction_set
                        st.success("Window construction updated successfully!")

                window_construction = room.properties.energy.construction_set.aperture_set.window_construction
                st.text_input("Display name",window_construction.display_name, disabled = True, key = f"{construction_set_name}_window_construction_display_name_{room.identifier}")
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.text_input("Current U-value",window_construction.u_value, disabled = True,  key = f"{construction_set_name}_window_construction_u_value_{room.identifier}" )
                with col2:
                    st.text_input("Current SHGC",window_construction.shgc, disabled = True,  key = f"{construction_set_name}_window_construction_SHGC_{room.identifier}" )
                with col3:
                    st.text_input("Current Visible Transmittance",window_construction.visible_transmittance, disabled = True,  key = f"{construction_set_name}_window_construction_visible_transmittance_{room.identifier}" )

                
                window_construction_dict = room.properties.energy.construction_set.aperture_set.window_construction.to_dict()
                update_properties_dict(room, window_construction_dict, "window_construction")

                
                    


