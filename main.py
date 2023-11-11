import folium
import streamlit as st
from folium.plugins import Draw
from streamlit_folium import st_folium
from flights import Flight
import logging
import traceback

logging.basicConfig(level=logging.INFO)


# Function to create and return a Folium map
def create_map():
    # Only create a new map if it's not already in the session state
    if "map" not in st.session_state:
        m = folium.Map(location=[39.949610, -75.150282], zoom_start=5)
        draw_options = {"draw": {"marker": True}, "edit": {"remove": True}}
        Draw(export=True, draw_options=draw_options).add_to(m)
        st.session_state.map = m
    return st.session_state.map


# Cached function to get closest flights
@st.cache_data
def get_closest_flights(lat, lng, number_of_flights=2):
    try:
        flight_instance = Flight(lat, lng)
    except Exception as e:
        logging.info("Error while calling the api: %s", e)
    return flight_instance.get_closest_flights(number_of_flights)


def display_flight_info(flights):
    if flights:
        identifiers, destinations, origins = [], [], []
        for flight in flights:
            print(flight)
            try:
                identifiers.append(flight["identification"]["callsign"])
            except:
                identifiers.append("N/A")
            try:
                destinations.append(flight["airport"]["destination"]["name"])
            except:
                destinations.append("N/A")
            try:
                origins.append(flight["airport"]["origin"]["name"])
            except:
                origins.append("N/A")
            # Add code to extract origins
        st.write(f"Identifiers: {identifiers}")
        st.write(f"Destinations: {destinations}")
        st.write(f"Origins: {origins}")
        st.write(flights)
    else:
        st.write("No flights found.")


def update_map_with_flights(flights):
    map_object = st.session_state.map  # Use the map from session state
    if flights:
        for flight in flights:
            folium.Marker(
                location=[flight["trail"][0]["lat"], flight["trail"][0]["lng"]],
                popup=flight["identification"]["callsign"],
                icon=folium.Icon(color="red", icon="plane"),
            ).add_to(map_object)


# Main app function
def main():
    m = create_map()
    c1, c2 = st.columns(2)

    with c1:
        output = st_folium(st.session_state.map, width=1000, height=800)
        # output = st_folium(m, width=1000, height=800)

    with c2:
        if output and "last_object_clicked" in output:
            if output["last_object_clicked"]:
                try:
                    st.write(output)
                    lat, lng = (
                        round(output["last_object_clicked"]["lat"], 3),
                        round(output["last_object_clicked"]["lng"], 3),
                    )
                    st.write(
                        f"Selected coordinates: {lat}, {lng}"
                    )  # Logging the coordinates
                    if st.button("Get Closest Flights"):
                        closest_flights = get_closest_flights(lat, lng)
                        display_flight_info(closest_flights)
                        update_map_with_flights(closest_flights)
                        # Rerender the map
                        # st_folium(m, width=1000, height=800)
                except Exception as e:
                    st.error("An error occurred: " + str(e))
                    st.text("Traceback:")
                    st.text(traceback.format_exc())


if __name__ == "__main__":
    main()
