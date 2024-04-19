from ladybug_geometry.geometry3d import Point3D, Face3D, Polyface3D, Vector3D
import streamlit as st
from honeybee.model import Model,Room
import tempfile
from pathlib import Path
from honeybee_energy.hvac.idealair import IdealAirSystem
from honeybee.boundarycondition import Outdoors
from honeybee.facetype import RoofCeiling
from honeybee.room import Room
from honeybee.face import Face

def clear_temp_folder(full_clean = True):
    st.session_state.temp_folder = Path(tempfile.mkdtemp())
    st.session_state.vtk_path = None
    if full_clean:
        st.session_state.hb_model = None
        st.session_state.valid_report = None
        st.session_state.building_geometry = None
    


def geometry_parameters(container):
    #col1, col2 = container.columns(2)
    width_ = container.number_input("Building Width [m]",min_value=0.0,max_value=50.0,value=10.0,help="This is the width of the building in meters")
    lenght_ = container.number_input("Building Lenght [m]",min_value=0.0,max_value=50.0,value=20.0,help="This is the lenght of the building in meters")        
    no_of_floors_ = container.number_input("Number of floors",min_value=0, max_value=10,value=2,step=1,help="This is the lenght of the building in meters")
    floor_height_ = container.number_input("Building Floor height [m]",min_value=2.0,max_value=10.0,value=3.0,help="This is the height of the building floor in meters")       
    wwr_ =  container.number_input("Window to wall ratio",min_value=0.0,max_value=0.99,value=0.4,help="This is the window to wall ratio for all the rooms")
   

    lower_left = Point3D(0, 0, 0)
    lower_right = Point3D(width_, 0, 0)
    upper_right = Point3D(width_, lenght_, 0)
    upper_left = Point3D(0, lenght_, 0)

    st.session_state.footprint = [lower_left, lower_right, upper_right, upper_left]
    st.session_state.no_of_floors = no_of_floors_
    st.session_state.floor_height = floor_height_
    st.session_state.wwr = wwr_



def generate_building(footprint, floor_height, num_floors):
    all_floors = []

    for i in range(num_floors):
        faces = []
        base_height = i * floor_height
        upper_height = (i + 1) * floor_height

        # Bottom face for every floor (also serves as ceiling for the floor below)
        faces.append(Face3D([pt.move(Vector3D(0, 0, base_height)) for pt in footprint]))

        # Side faces for the current floor
        for j in range(len(footprint)):
            start_point = footprint[j]
            end_point = footprint[(j + 1) % len(footprint)]

            lower_left = Point3D(start_point.x, start_point.y, base_height)
            lower_right = Point3D(end_point.x, end_point.y, base_height)
            upper_right = Point3D(end_point.x, end_point.y, upper_height)
            upper_left = Point3D(start_point.x, start_point.y, upper_height)

            face = Face3D([lower_left, lower_right, upper_right, upper_left])
            faces.append(face)

        # Top face for every floor including the very bottom one
        faces.append(Face3D([pt.move(Vector3D(0, 0, upper_height)) for pt in footprint]))

        floor_geometry = Polyface3D.from_faces(faces, 0.01)
        all_floors.append(floor_geometry)

    st.session_state.building_geometry = all_floors  # Store the list of Polyface3D geometries for each floor



def can_host_apeture(face):
    """Test if a face is intended to host apertures (according to this component)."""
    return isinstance(face.boundary_condition, Outdoors) and \
        isinstance(face.type, RoofCeiling)


def assign_apertures(face, rat, xd, yd, op):
    """Assign apertures to a Face based on a set of inputs."""
    face.apertures_by_ratio_gridded(rat, xd, yd)

    # try to assign the operable property
    if op:
        for ap in face.apertures:
            ap.is_operable = op

# add skylights

def create_skylights(_hb_objs, _ratio,_y_dim_, _x_dim_=None, operable_ = False):
    # duplicate the initial objects
    #hb_objs = [obj.duplicate() for obj in _hb_objs]

    # set defaults for any blank inputs
    if _x_dim_ is None and _x_dim_ is None:
        _x_dim_ = _x_dim_ if _x_dim_ is None else 3.0 
    elif _x_dim_ is None:
        _x_dim_ == _y_dim_

    # loop through the input objects and add apertures
    for obj in _hb_objs:
        if isinstance(obj, Room):
            for face in obj.faces:
                if can_host_apeture(face):
                    assign_apertures(face, _ratio, _x_dim_, _y_dim_, operable_)
        elif isinstance(obj, Face):
            if can_host_apeture(obj):
                assign_apertures(obj, _ratio, _x_dim_, _y_dim_, operable_)
        else:
            raise TypeError(
                'Input _hb_objs must be a Room or Face. Not {}.'.format(type(obj)))


def generate_honeybee_model():
    """Type of building: Polyface3D"""
    """This function will convert the building into a Honeybee JSON"""

    st.session_state.hb_model = Model("shoeBox_wizard")  # instantiate a model
    rooms = []  # to store all rooms for adjacency check

    for i, floor_geometry in enumerate(st.session_state.building_geometry):
        room = Room.from_polyface3d(f"room_{i}", floor_geometry)  # creating a room
        room.wall_apertures_by_ratio(st.session_state.wwr)  # add a window

        rooms.append(room)  # append room to the list
        st.session_state.hb_model.add_room(room)  # adding a room to the model

    # Solve adjacency between rooms
    Room.solve_adjacency(st.session_state.hb_model.rooms, 0.01)

    # Add ideal air system
    for room in st.session_state.hb_model.rooms:
        identifier = f"IdealAirSystem-{room.identifier}"
        if not room.properties.energy.hvac:
            room.properties.energy.hvac = IdealAirSystem(identifier)

        # Skylights
        create_skylights(room, st.session_state.skylight_ratio ,st.session_state.skylight_y_dimension,  operable_=st.session_state.skylight_operable)
