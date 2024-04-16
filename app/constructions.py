
import streamlit as st
from utils import get_vintage_constructions, get_climate_zone, update_properties_dict
from honeybee.search import filter_array_by_keywords
from honeybee_energy.lib.constructionsets import CONSTRUCTION_SETS
from honeybee_energy.lib.constructionsets import construction_set_by_identifier
import random
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
    
    get_vintage_constructions()
    get_climate_zone("constructions")

    trimmed_zone = "ClimateZone" + st.session_state.climate_zone[0]
    room_construction_set = filter_array_by_keywords(CONSTRUCTION_SETS, [st.session_state.vintage_constructions,trimmed_zone ], False)
    # Iterate over each room in the Honeybee model.
    # 'st.session_state.hb_model.rooms' contains a list of rooms in the model. For each room, various properties will be displayed and can be modified.
    # Display each room's properties using expanders.
    for room in st.session_state.hb_model.rooms:
        with st.expander(f"Room identifier: {room.identifier}"):

            # Generate a unique key for the room program selectbox using the room's identifier.
            # This ensures that each selectbox in the loop is treated as a distinct widget by Streamlit.
            selectbox_key = f"room_construction_set_{room.identifier}"
            # Determine the current index of the room's program type in the 'room_prog' list to set it as the default selection in the selectbox.
            # If the room's program type identifier is not in 'room_prog', default to the first item (index 0).
            current_construction_set_index = room_construction_set.index(room.properties.energy.construction_set.identifier) if room.properties.energy.construction_set.identifier in room_construction_set else room_construction_set.index(filter_array_by_keywords(room_construction_set, ["Mass"])[0])#0
            # Create a selectbox for changing the room's program type, with the current program type pre-selected.
            new_construction_set = st.selectbox("Construction set", room_construction_set, index=current_construction_set_index, key=selectbox_key)
            
            # Check if the user has selected a different program type from the dropdown.
            # If so, update the room's program type to the new selection. Otherwise, keep it unchanged.
            if new_construction_set != room.properties.energy.construction_set.identifier:
                new_construction_set = construction_set_by_identifier(new_construction_set)
                room.properties.energy.construction_set = new_construction_set
                st.session_state.sql_results = None  # reset to have results recomputed
            else:
                # Duplicate the program type to ensure any modifications are made on a new instance, preserving the original object's state.
                new_construction_set = room.properties.energy.construction_set
            
            new_construction_set = room.properties.energy.construction_set.duplicate()
            
            # Check if the new program type has a lighting object associated with it.
            if new_construction_set.wall_set:
                construction_set_name = "wall_set"
                st.divider() 
                st.subheader("Wall Set") 
                st.write("Exterior construction")
                exterior_construction = new_construction_set.wall_set.exterior_construction.duplicate() 
                st.text_input("Display name",exterior_construction.display_name, disabled = True, key = f"{construction_set_name}_exterior_construction_display_name_{room.identifier}")
                st.text_input("U-value",exterior_construction.u_value, disabled = True, key = f"{construction_set_name}_exterior_construction_u_value_{room.identifier}" )
                exterior_construction_dict = exterior_construction.to_dict()
                updated_exterior_construction_dict = update_properties_dict(room, exterior_construction_dict, "exterior_construction")
                #new_construction_set.wall_set.exterior_construction = updated_exterior_construction_dict
                
                st.divider() 
                st.write("Interior construction")
                interior_construction = new_construction_set.wall_set.interior_construction.duplicate()
                st.text_input("Display name",interior_construction.display_name, disabled = True, key = f"{construction_set_name}_interior_construction_display_name_{room.identifier}")
                st.text_input("U-value",interior_construction.u_value, disabled = True, key = f"{construction_set_name}_interior_construction_u_value_{room.identifier}" )
                interior_construction_dict = interior_construction.to_dict()
                updated_interior_construction_dict = update_properties_dict(room, interior_construction_dict, "{construction_set_name}_interior_construction")
                #new_construction_set.interior_construction = updated_interior_construction_dict

            if new_construction_set.floor_set:
                construction_set_name = "floor_set"
                st.divider() 
                st.subheader("Floor Set") 
                st.write("Ground construction")
                ground_construction = new_construction_set.floor_set.ground_construction.duplicate()
                st.text_input("Display name",ground_construction.display_name, disabled = True, key = f"{construction_set_name}_ground_construction_display_name_{room.identifier}")
                st.text_input("U-value",ground_construction.u_value, disabled = True, key = f"{construction_set_name}_ground_construction_u_value_{room.identifier}" )
                ground_construction_dict = ground_construction.to_dict()
                updated_ground_construction_dict = update_properties_dict(room, ground_construction_dict, "{construction_set_name}_ground_construction")
                #new_construction_set.floor_set.ground_construction = updated_ground_construction_dict
            
            if new_construction_set.roof_ceiling_set:
                construction_set_name = "roof_ceiling_set"
                st.divider() 
                st.subheader("Roof Ceiling Set") 
                st.write("Exterior construction")
                exterior_construction = new_construction_set.roof_ceiling_set.exterior_construction.duplicate() 
                st.text_input("Display name",exterior_construction.display_name, disabled = True, key = f"{construction_set_name}_exterior_construction_display_name_{room.identifier}")
                st.text_input("U-value",exterior_construction.u_value, disabled = True, key = f"{construction_set_name}_exterior_construction_u_value_{room.identifier}" )
                exterior_construction_dict = exterior_construction.to_dict()
                updated_exterior_construction_dict = update_properties_dict(room, exterior_construction_dict, "exterior_construction")
                #new_construction_set.roof_ceiling_set.exterior_construction = updated_exterior_construction_dict
                
                
            if new_construction_set.aperture_set:
                construction_set_name = "aperture_set"
                st.divider() 
                st.subheader("Aperture Set") 
                st.write("Exterior construction")
                window_construction = new_construction_set.aperture_set.window_construction.duplicate() 
                st.text_input("Display name",window_construction.display_name, disabled = True, key = f"{construction_set_name}_window_construction_display_name_{room.identifier}")
                st.text_input("U-value",window_construction.u_value, disabled = True, key = f"{construction_set_name}_window_construction_u_value_{room.identifier}" )
                window_construction_dict = window_construction.to_dict()
                updated_window_construction_dict = update_properties_dict(room, window_construction_dict, "window_construction")
                #new_construction_set.aperture_set.window_construction = updated_exterior_construction_dict
                
                
           

            # Assign the updated program type back to the original ProgramType
            if room.properties.energy.construction_set != new_construction_set:
                room.properties.energy.construction_set = new_construction_set
                st.session_state.sql_results = None  # reset to have results recomputed
