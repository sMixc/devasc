import streamlit as st
import requests
import urllib.parse
import folium
from streamlit_folium import st_folium

# --- CONFIG ---
st.set_page_config(page_title="Graphhopper Route Finder", layout="wide", initial_sidebar_state="expanded")
route_url = "https://graphhopper.com/api/1/route?"
key = "571cae75-8241-46bb-af7f-62d0eaa4bc96"  # replace with your Graphhopper API key

# --- Geocoding Function ---
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

# --- Session State ---
if "route_data" not in st.session_state:
    st.session_state.route_data = None

# --- Original CSS ---
st.markdown("""
<style>
/* Hide default Streamlit elements */
header[data-testid="stHeader"] { display: none; }
.stDeployButton { display: none; }
#MainMenu { visibility: hidden; }
footer { visibility: hidden; }

/* Main app container */
.main .block-container { padding-top: 1rem; padding-bottom: 0rem; max-width: 100%; }

/* Map container */
.map-container { position: relative; width: 100%; height: 700px; z-index: 1 !important; }

/* Sidebar route details */

/* Route summary gradient */
.route-summary {
    background: linear-gradient(135deg, #e3f2fd 0%, #bbdefb 100%);
    padding: 16px;
    border-radius: 10px;
    margin: 16px 0;
}

/* Turn-by-turn direction box */
.direction-item {
    background: #f8f9fa;
    padding: 12px;
    margin: 8px 0;
    border-radius: 6px;
    border-left: 4px solid #007bff;
    font-size: 14px;
}
            
/* Hide sidebar header */
    div[data-testid="stSidebarHeader"] {
        display: none;
    }
            
/* Remove top margin/padding from main content and sidebar */
.block-container {
    padding-top: 0rem !important;
}

.stSidebar .css-1d391kg {
    padding-top: 0rem !important;
}

/* Optional: ensure map container fills the remaining space */
.map-container {
    height: 700px;
}
</style>
""", unsafe_allow_html=True)


# --- Sidebar Route Details ---
if st.session_state.route_data:
    with st.sidebar:

        st.markdown("""
        <style>
        /* Hide Streamlit sidebar collapse/expand button */
        [data-testid="stSidebarCollapseButton"] {
            display: none !important;
        }
        </style>
        """, unsafe_allow_html=True)
        
        route_info = st.session_state.route_data
        data = route_info["data"]
        loc1 = route_info["loc1"]
        loc2 = route_info["loc2"]
        vehicle = route_info["vehicle"]

        km = data["paths"][0]["distance"] / 1000
        miles = km / 1.60934
        sec = int(data["paths"][0]["time"] / 1000 % 60)
        mins = int(data["paths"][0]["time"] / 1000 / 60 % 60)
        hrs = int(data["paths"][0]["time"] / 1000 / 60 / 60)
        
        # Route summary
        st.markdown(f"""
            <div class="route-summary">
                <h4 style="color: #666;">📍 {loc1}</h4>
                <h4 style="color: #666;">🏁 {loc2}</h4>
                <p style="color: #666;"><strong>Vehicle:</strong> {vehicle.title()}</p>
            </div>
        """, unsafe_allow_html=True)
        
        # Distance and duration
        col1, col2 = st.columns(2)
        with col1:
            st.metric("📏 Distance", f"{miles:.1f} mi", f"{km:.1f} km")
        with col2:
            st.metric("⏱️ Duration", f"{hrs:02d}:{mins:02d}:{sec:02d}")
        
        st.markdown("---")
        st.markdown("### 📋 Directions")
        
        # Turn-by-turn directions
        if "instructions" in data["paths"][0]:
            for i, step in enumerate(data["paths"][0]["instructions"], 1):
                text = step["text"]
                dist = step["distance"] / 1000
                st.markdown(f"""
                    <div class="direction-item">
                        <strong style="color: #000000;">{i}. {text}</strong>
                        <br><small style="color: #666;">📏 {dist:.1f} km</small>
                    </div>
                """, unsafe_allow_html=True)
        else:
            st.write("No detailed directions available")
        
        st.markdown('</div>', unsafe_allow_html=True)

# --- Main Form ---
with st.container():
    st.markdown("**🗺️ Route Planner**")
    with st.form("route_form", clear_on_submit=False):
        vehicle = st.selectbox("🚗 Vehicle", ["car", "bike", "foot"], key="vehicle_form")
        start = st.text_input("📍 Start Location", key="start", placeholder="Enter starting point")
        dest = st.text_input("🏁 Destination", key="dest", placeholder="Enter destination")
        submitted = st.form_submit_button("🔍 Get Route", use_container_width=True)
        
        if submitted:
            if not start or not dest:
                st.error("Please enter both start and destination.")
            else:
                with st.spinner("Finding route..."):
                    lat1, lng1, loc1 = geocoding(start, key)
                    lat2, lng2, loc2 = geocoding(dest, key)

                    if not lat1 or not lat2:
                        st.error(f"Failed to geocode locations")
                    else:
                        op = "&point=" + str(lat1) + "%2C" + str(lng1)
                        dp = "&point=" + str(lat2) + "%2C" + str(lng2)
                        params = {"key": key, "vehicle": vehicle, "points_encoded": "false"}
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
                            st.success("Route found!")
             
                        else:
                            st.error("Routing failed: " + data.get("message", "Unknown error"))

# --- Map Display ---
map_container = st.container()
with map_container:
    if st.session_state.route_data:
        route_info = st.session_state.route_data
        data = route_info["data"]
        lat1, lng1 = route_info["lat1"], route_info["lng1"]
        lat2, lng2 = route_info["lat2"], route_info["lng2"]
        coords = data["paths"][0]["points"]["coordinates"]

        m = folium.Map(location=[lat1, lng1], zoom_start=13)
        folium.PolyLine(locations=[(lat, lon) for lon, lat in coords], color="blue", weight=5, opacity=0.8).add_to(m)
        folium.Marker([lat1, lng1], popup=f"Start: {route_info['loc1']}", icon=folium.Icon(color="green", icon="play")).add_to(m)
        folium.Marker([lat2, lng2], popup=f"Destination: {route_info['loc2']}", icon=folium.Icon(color="red", icon="stop")).add_to(m)
        m.fit_bounds([(lat, lon) for lon, lat in coords])
        st_folium(m, width="100%", height=700, key="route_map")
    else:
        m = folium.Map(location=[14.5995, 120.9842], zoom_start=12)
        st_folium(m, width="100%", height=700, key="default_map")
