
import streamlit as st
from utils import get_vintage_constructions, get_climate_zone, update_properties_dict
from honeybee.search import filter_array_by_keywords
from honeybee_energy.lib.constructionsets import CONSTRUCTION_SETS
from honeybee_energy.lib.constructionsets import construction_set_by_identifier
from honeybee_energy.construction.window import WindowConstruction
from honeybee_energy.constructionset import ApertureConstructionSet
from honeybee_energy.constructionset import ConstructionSet
    

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
    
    #get_vintage_constructions(st,key_="constructions_tab")
    #get_climate_zone(st,key_="constructions_tab")

    trimmed_zone = "ClimateZone" + st.session_state.climate_zone[0]
    room_construction_set = filter_array_by_keywords(CONSTRUCTION_SETS, [st.session_state.vintage_constructions,trimmed_zone ], False)
    # Iterate over each room in the Honeybee model.
    # 'st.session_state.hb_model.rooms' contains a list of rooms in the model. For each room, various properties will be displayed and can be modified.
    # Display each room's properties using expanders.
    for room in st.session_state.hb_model.rooms:
        with st.expander(f"Room identifier: {room.identifier}"):
            key_= f"{room.identifier}_constructions_tab"
            get_vintage_constructions(st,key_)
            #get_climate_zone(st,key_) - comment out for now

            # Generate a unique key for the room program selectbox using the room's identifier.
            # This ensures that each selectbox in the loop is treated as a distinct widget by Streamlit.
            selectbox_key = f"room_construction_set_{room.identifier}"
            # Determine the current index of the room's program type in the 'room_prog' list to set it as the default selection in the selectbox.
            # If the room's program type identifier is not in 'room_prog', default to the first item (index 0).
            current_construction_set_index = room_construction_set.index(room.properties.energy.construction_set.identifier) if room.properties.energy.construction_set.identifier in room_construction_set else room_construction_set.index(filter_array_by_keywords(room_construction_set, ["Mass"])[0])#0
            # Create a selectbox for changing the room's program type, with the current program type pre-selected.
            new_construction_set = st.selectbox("Construction set", room_construction_set, index=current_construction_set_index, key=selectbox_key)
            new_construction_set = construction_set_by_identifier(new_construction_set)
            # Check if the user has selected a different program type from the dropdown.
            """
            # If so, update the room's program type to the new selection. Otherwise, keep it unchanged.
            if new_construction_set != room.properties.energy.construction_set.identifier:
                new_construction_set = construction_set_by_identifier(new_construction_set)
                room.properties.energy.construction_set = new_construction_set
                #st.session_state.baseline_sql_results = None
                #st.session_state.improved_sql_results = None
            else:
                # Duplicate the program type to ensure any modifications are made on a new instance, preserving the original object's state.
                #new_construction_set = room.properties.energy.construction_set
                new_construction_set = room.properties.energy.construction_set.duplicate()
            """
            
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
                window_construction = new_construction_set.aperture_set.window_construction#.duplicate() 
                st.text_input("Display name",window_construction.display_name, disabled = True, key = f"{construction_set_name}_window_construction_display_name_{room.identifier}")
                new_u_value = st.text_input("U-value",window_construction.u_value, disabled = False,  key = f"{construction_set_name}_window_construction_u_value_{room.identifier}" )
                if new_u_value != window_construction.u_value:  
                    if st.button("Update u value", key = f"update_u_value_{room.identifier}"):
                        new_window_construction = WindowConstruction.from_simple_parameters(window_construction.identifier, new_u_value, shgc=0.5, vt=0.6)
                        new_aperture_set = ApertureConstructionSet(window_construction=new_window_construction)
                        new_construction_set =ConstructionSet("new_construction_set", wall_set= new_construction_set.wall_set, floor_set=new_construction_set.floor_set, roof_ceiling_set=new_construction_set.roof_ceiling_set, aperture_set=new_aperture_set, door_set=new_construction_set.door_set, shade_construction=new_construction_set.shade_construction, air_boundary_construction=new_construction_set.air_boundary_construction)
                        room.properties.energy.construction_set = new_construction_set
                        st.session_state.improved_sql_results = None
                window_construction_dict = new_construction_set.aperture_set.window_construction.to_dict()
                updated_window_construction_dict = update_properties_dict(room, window_construction_dict, "window_construction")
                #if updated_window_construction_dict != window_construction_dict:
                

                
           

            # Assign the updated construction type back to the original cosntructionType
            #if room.properties.energy.construction_set != new_construction_set:
            # Button to apply the update
            #if st.button("Update constructions", key = f"update_constructions_{room.identifier}"):
                #room.properties.energy.construction_set = new_construction_set
                #st.session_state.baseline_sql_results = None
                #st.session_state.improved_sql_results = None
                #st.json(new_construction_set.aperture_set.window_construction.to_dict())
                
