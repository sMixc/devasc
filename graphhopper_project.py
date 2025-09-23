import streamlit as st
import requests
import urllib.parse
import folium
from streamlit_folium import st_folium

route_url = "https://graphhopper.com/api/1/route?"
key = "571cae75-8241-46bb-af7f-62d0eaa4bc96"   # ⚠️ replace with your Graphhopper key

# --- Geocoding ---
def geocoding(location, key):
    geocode_url = "https://graphhopper.com/api/1/geocode?"
    url = geocode_url + urllib.parse.urlencode({"q": location, "limit": "1", "key": key})
    replydata = requests.get(url)
    json_data = replydata.json()

    if replydata.status_code == 200 and len(json_data["hits"]) != 0:
        hit = json_data["hits"][0]
        lat, lng = hit["point"]["lat"], hit["point"]["lng"]
        name = hit["name"]
        state = hit.get("state", "")
        country = hit.get("country", "")
        new_loc = f"{name}, {state}, {country}".strip(", ")
        return lat, lng, new_loc
    else:
        return None, None, "Error: " + json_data.get("message", "Unknown error")

# --- Streamlit UI ---
st.set_page_config(page_title="Graphhopper Route Finder", layout="wide")
st.title("🚗 Graphhopper Route Finder")

vehicle = st.selectbox("Choose vehicle:", ["car", "bike", "foot"])
start = st.text_input("Start Location", "")
dest = st.text_input("Destination", "")

# Initialize session state
if "route_data" not in st.session_state:
    st.session_state.route_data = None

# Button action
if st.button("Get Route"):
    if not start or not dest:
        st.error("Please enter both start and destination.")
    else:
        lat1, lng1, loc1 = geocoding(start, key)
        lat2, lng2, loc2 = geocoding(dest, key)

        if not lat1 or not lat2:
            st.error(f"Failed to geocode: {loc1}, {loc2}")
        else:
            op = "&point=" + str(lat1) + "%2C" + str(lng1)
            dp = "&point=" + str(lat2) + "%2C" + str(lng2)
            params = {"key": key, "vehicle": vehicle, "points_encoded": "false"}  # decode polyline
            paths_url = route_url + urllib.parse.urlencode(params) + op + dp

            response = requests.get(paths_url)
            data = response.json()

            if response.status_code == 200:
                st.session_state.route_data = {
                    "data": data,
                    "lat1": lat1, "lng1": lng1, "loc1": loc1,
                    "lat2": lat2, "lng2": lng2, "loc2": loc2,
                    "vehicle": vehicle
                }
            else:
                st.error("Routing Error: " + data.get("message", "Unknown error"))

# Display results if available
if st.session_state.route_data:
    data = st.session_state.route_data["data"]
    lat1 = st.session_state.route_data["lat1"]
    lng1 = st.session_state.route_data["lng1"]
    loc1 = st.session_state.route_data["loc1"]
    lat2 = st.session_state.route_data["lat2"]
    lng2 = st.session_state.route_data["lng2"]
    loc2 = st.session_state.route_data["loc2"]
    vehicle = st.session_state.route_data["vehicle"]

    km = data["paths"][0]["distance"] / 1000
    miles = km / 1.60934
    sec = int(data["paths"][0]["time"] / 1000 % 60)
    mins = int(data["paths"][0]["time"] / 1000 / 60 % 60)
    hrs = int(data["paths"][0]["time"] / 1000 / 60 / 60)

    st.subheader(f"Route from {loc1} to {loc2} by {vehicle}")
    st.info(f"**Distance:** {miles:.1f} miles / {km:.1f} km\n\n"
            f"**Duration:** {hrs:02d}:{mins:02d}:{sec:02d}")

    # --- Two-column responsive layout ---
    col1, col2 = st.columns([1, 2])  # left narrower than right

    with col1:
        st.subheader("🛣️ Directions")
        for step in data["paths"][0]["instructions"]:
            text = step["text"]
            dist = step["distance"] / 1000
            st.write(f"- {text} ({dist:.1f} km)")

    with col2:
        st.subheader("🗺️ Route Map")
        coords = data["paths"][0]["points"]["coordinates"]
        m = folium.Map(location=[lat1, lng1], zoom_start=13)

        # Add route polyline
        folium.PolyLine(locations=[(lat, lon) for lon, lat in coords],
                        color="blue", weight=5, opacity=0.8).add_to(m)

        # Add start & end markers
        folium.Marker([lat1, lng1], popup="Start", icon=folium.Icon(color="green")).add_to(m)
        folium.Marker([lat2, lng2], popup="Destination", icon=folium.Icon(color="red")).add_to(m)

        # Auto fit map bounds to route
        m.fit_bounds([(lat, lon) for lon, lat in coords])

        st_folium(m, width="100%", height=700)
