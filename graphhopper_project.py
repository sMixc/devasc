
import streamlit as st
import requests
import urllib.parse
import folium
import os
import json
from streamlit_folium import st_folium
import sqlite3

# --- Database Setup ---
DB_FILE = "routes.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS saved_routes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            start_location TEXT,
            destination TEXT,
            vehicle TEXT,
            distance REAL,
            duration REAL,
            data TEXT
        )
    """)
    conn.commit()
    conn.close()

def save_route_to_db(start, dest, vehicle, distance, duration, data):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute(
        "INSERT INTO saved_routes (start_location, destination, vehicle, distance, duration, data) VALUES (?, ?, ?, ?, ?, ?)",
        (start, dest, vehicle, distance, duration, json.dumps(data))
    )
    conn.commit()
    conn.close()

def load_routes_from_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT id, start_location, destination, vehicle, distance, duration FROM saved_routes")
    rows = c.fetchall()
    conn.close()
    return rows

def get_route_data_by_id(route_id):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT data FROM saved_routes WHERE id = ?", (route_id,))
    row = c.fetchone()
    conn.close()
    if row:
        return json.loads(row[0])
    return None

# Initialize database
init_db()


# --- CONFIG ---
st.set_page_config(page_title="RouteMatch", layout="wide", initial_sidebar_state="expanded")
route_url = "https://graphhopper.com/api/1/route?"
key = os.environ['GRAPH_HOPPER_KEY']

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

# --- CSS for Navbar Design ---
st.markdown("""
<style>
/* Hide default Streamlit elements */
header[data-testid="stHeader"] { display: none; }
.stDeployButton { display: none; }
#MainMenu { visibility: hidden; }
footer { visibility: hidden; }

/* Main app container */
.main .block-container { 
    padding-top: 0rem !important; 
    padding-bottom: 0rem; 
    max-width: 100%; 
}

/* Additional padding removal */
.block-container {
    padding-top: 0rem !important;
}

/* Ensure no top spacing on first element */
.main .block-container > div:first-child {
    margin-top: 0 !important;
    padding-top: 0 !important;
}

/* Navbar styling */

.navbar h1 {
    color: white;
    margin: 0;
    text-align: center;
    font-size: 24px;
    font-weight: 600;
    margin-bottom: 20px;
}

/* Navbar form container */
.navbar-form {
    display: flex;
    gap: 15px;
    align-items: end;
    flex-wrap: wrap;
}

/* Navbar form styling */
.navbar .stSelectbox > label,
.navbar .stTextInput > label {
    color: white !important;
    font-weight: 500 !important;
    margin-bottom: 5px !important;
}

.navbar .stSelectbox > div > div,
.navbar .stTextInput > div > div > input {
    background: rgba(255, 255, 255, 0.9) !important;
    border: 1px solid rgba(255, 255, 255, 0.3) !important;
    border-radius: 8px !important;
}

.navbar .stTextInput > div > div > input {
    padding: 8px 12px !important;
}

.navbar .stButton > button {
    background: rgba(255, 255, 255, 0.2) !important;
    color: white !important;
    border: 2px solid rgba(255, 255, 255, 0.3) !important;
    border-radius: 8px !important;
    padding: 10px 24px !important;
    font-weight: 600 !important;
    transition: all 0.3s ease !important;
    backdrop-filter: blur(10px) !important;
    height: 40px !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    min-height: 40px !important;
}

/* Fix button container alignment */
.navbar .stButton {
    display: flex !important;
    flex-direction: column !important;
    height: 100% !important;
    justify-content: space-between !important;
}

.navbar .stButton > div {
    width: 100% !important;
    height: 100% !important;
    display: flex !important;
    flex-direction: column !important;
}

.navbar .stButton > div > div {
    flex-grow: 1 !important;
    display: flex !important;
    align-items: flex-end !important;
}

.navbar .stButton > button:hover {
    background: rgba(255, 255, 255, 0.3) !important;
    border-color: rgba(255, 255, 255, 0.5) !important;
    transform: translateY(-2px) !important;
    box-shadow: 0 4px 15px rgba(255, 255, 255, 0.2) !important;
}

/* Map container */
.map-container { 
    width: 100%; 
    height: 650px; 
    margin-top: 0px;
}

/* Sidebar route details */
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
            
/* Remove sidebar padding */
.stSidebar .css-1d391kg {
    padding-top: 0rem !important;
}

/* Responsive navbar */
@media (max-width: 768px) {
    .navbar-form {
        flex-direction: column;
        gap: 10px;
    }
    
    .navbar-form > div {
        width: 100% !important;
    }
}

/* Form columns for better layout */
.form-row {
    display: grid;
    grid-template-columns: 150px 1fr 1fr 150px;
    gap: 15px;
    align-items: end;
    width: 100%;
}

@media (max-width: 768px) {
    .form-row {
        grid-template-columns: 1fr;
        gap: 10px;
    }
}
            
 /* Make sidebar wider */
    [data-testid="stSidebar"] {
            width: 400px;   /* change to whatever size you like */
    }

/* Hide Streamlit heading anchor link (the link icon on hover) */
[data-testid="stHeadingWithAnchorLink"] {
    display: none !important;
}
</style>
""", unsafe_allow_html=True)

st.markdown(
    """
    <div style="color: white; font-weight: 600;">
        <span style="font-size: 45px;">RouteMatch</span>
        <span style="font-size: 16px; margin-left: 8px; font-weight: 400;">
            Powered by GraphHopper
        </span>
    </div>
    """,
    unsafe_allow_html=True
)

with st.form("route_form", clear_on_submit=False):

    col1, col2, col3, col4 = st.columns([1.5, 3, 3, 1.5])
    
    with col1:
        vehicle = st.selectbox("🚗 Mode", ["car", "bike", "foot"], key="vehicle_form")

    with col2:
        start = st.text_input("📍 Start Location", key="start", placeholder="starting point")

    with col3:
        dest = st.text_input("🏁 Destination", key="dest", placeholder="destination")

    with col4:
        st.markdown(
            '<div style="font-size: 0.875rem; font-weight: 500; line-height: 1.6; color: white; margin-bottom: 4px;">&nbsp;</div>',
            unsafe_allow_html=True
        )
        submitted = st.form_submit_button("🔍 Match Route", use_container_width=True)

    
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
                        st.rerun()
         
                    else:
                        st.error("Routing failed: " + data.get("message", "Unknown error"))

st.markdown('</div>', unsafe_allow_html=True)

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

        # Distance
        km = data["paths"][0]["distance"] / 1000
        miles = km / 1.60934

        # Base time in seconds from API
        base_seconds = data["paths"][0]["time"] / 1000  

        # --- Add buffer/prolongation ---
        buffer_seconds = 10 * 60  # 10 minutes buffer

        factor = 1.2

        # Final total seconds (apply both buffer + factor)
        total_seconds = base_seconds * factor + buffer_seconds

        # Break into hrs, mins, secs
        hrs = int(total_seconds // 3600)
        mins = int((total_seconds % 3600) // 60)
        sec = int(total_seconds % 60)
        
        # Route summary
        st.markdown(f"""
            <div class="route-summary">
                <h4 style="color: #666;">📍 {loc1}</h4>
                <h4 style="color: #666;">🏁 {loc2}</h4>
                <p style="color: #666;"><strong>Mode:</strong> {vehicle.title()}</p>
            </div>
        """, unsafe_allow_html=True)
        
        # Route summary
        st.markdown(f"""
            <div class="route-summary">
                <h4 style="color: #666;">📍 {loc1}</h4>
                <h4 style="color: #666;">🏁 {loc2}</h4>
                <p style="color: #666;"><strong>Mode:</strong> {vehicle.title()}</p>
            </div>
        """, unsafe_allow_html=True)
        
        
        # --- Save to SQLite Button ---
        if st.button("💾 Save This Route"):
            save_route_to_db(loc1, loc2, vehicle, km, total_seconds, st.session_state.route_data)
            st.success("✅ Route saved to database!")


        
        # Distance and duration
        col1, col2 = st.columns(2)
        with col1:
            st.metric("📏Distance", f"{miles:.1f} mi", f"{km:.1f} km")
        with col2:
            st.metric("⏱️Estimated Duration", f"{hrs:02d}:{mins:02d}:{sec:02d}")
        
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
            
        st.markdown("---")
        st.markdown("### 💼 Saved Routes")

        saved_routes = load_routes_from_db()
        if saved_routes:
            for route_id, start, dest, veh, dist, dur in saved_routes:
                hrs = int(dur // 3600)
                mins = int((dur % 3600) // 60)
                st.markdown(f"**{start} ➜ {dest}** ({veh}) — {dist:.1f} km, {hrs:02d}:{mins:02d}")
                if st.button(f"🗺️ Load Route {route_id}", key=f"load_{route_id}"):
                    route_data = get_route_data_by_id(route_id)
                    if route_data:
                        st.session_state.route_data = route_data
                        st.rerun()
        else:
            st.info("No saved routes yet.")


# --- Map Display ---
map_container = st.container()
with map_container:
    TOMTOM_API_KEY = os.environ["TOMTOM_KEY"]

    if st.session_state.route_data:
        route_info = st.session_state.route_data
        data = route_info["data"]
        lat1, lng1 = route_info["lat1"], route_info["lng1"]
        lat2, lng2 = route_info["lat2"], route_info["lng2"]
        coords = data["paths"][0]["points"]["coordinates"]

        # Base map
        m = folium.Map(location=[lat1, lng1], zoom_start=13)

        # Draw route polyline
        folium.PolyLine(
            locations=[(lat, lon) for lon, lat in coords],
            color="blue",
            weight=5,
            opacity=0.8
        ).add_to(m)

        # Add start and destination markers
        folium.Marker(
            [lat1, lng1],
            popup=f"Start: {route_info['loc1']}",
            icon=folium.Icon(color="green", icon="play")
        ).add_to(m)

        folium.Marker(
            [lat2, lng2],
            popup=f"Destination: {route_info['loc2']}",
            icon=folium.Icon(color="red", icon="stop")
        ).add_to(m)

        # Fit map bounds to route
        m.fit_bounds([(lat, lon) for lon, lat in coords])

        # ✅ Add optional TomTom live traffic overlay
        if TOMTOM_API_KEY:
            folium.TileLayer(
                tiles=f"https://api.tomtom.com/traffic/map/4/tile/flow/relative/{{z}}/{{x}}/{{y}}.png?key={TOMTOM_API_KEY}",
                attr="TomTom Traffic",
                name="Traffic Flow",
                overlay=True,
                control=True,
                opacity=0.8
            ).add_to(m)

            # Add a toggle control for traffic
            folium.LayerControl().add_to(m)

        # Render map in Streamlit
        st_folium(m, width="100%", height=650, key="route_map")

    else:
        # Default view (no route yet)
        m = folium.Map(location=[14.5995, 120.9842], zoom_start=12)

        # ✅ Still add traffic overlay even without a route
        TOMTOM_API_KEY = os.getenv("TOMTOM_KEY", "")
        if TOMTOM_API_KEY:
            folium.TileLayer(
                tiles=f"https://api.tomtom.com/traffic/map/4/tile/flow/relative/{{z}}/{{x}}/{{y}}.png?key={TOMTOM_API_KEY}",
                attr="TomTom Traffic",
                name="Traffic Flow",
                overlay=True,
                control=True,
                opacity=0.8
            ).add_to(m)
            folium.LayerControl().add_to(m)

        st_folium(m, width="100%", height=650, key="default_map")


# --- Saved Routes Dropdown (below the map) ---
def delete_route_by_id(route_id):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("DELETE FROM saved_routes WHERE id = ?", (route_id,))
    conn.commit()
    conn.close()

# Load saved routes for the dropdown
saved_routes = load_routes_from_db()  # returns list of tuples (id, start, dest, veh, dist, dur)

if saved_routes:
    # Build options and a mapping from label -> id
    options = []
    label_to_id = {}
    for route_id, start, dest, veh, dist, dur in saved_routes:
        hrs = int(dur // 3600)
        mins = int((dur % 3600) // 60)
        label = f"{start} ➜ {dest} ({veh}) — {dist:.1f} km, {hrs:02d}:{mins:02d}"
        options.append(label)
        label_to_id[label] = route_id

    st.markdown("---")
    st.markdown("### 💾 Saved routes")

    # Dropdown
    chosen_label = st.selectbox("Choose a saved route to preview or load:", ["-- Select a saved route --"] + options, key="saved_route_select")

    if chosen_label and chosen_label != "-- Select a saved route --":
        chosen_id = label_to_id[chosen_label]
        # fetch the full route data (the JSON you stored)
        route_data = get_route_data_by_id(chosen_id)

        if route_data:
            # route_data might be either the full 'route_info' dict or just GraphHopper response
            data = route_data["data"] if isinstance(route_data, dict) and "data" in route_data else route_data

            # Show a lightweight preview: start/dest/metrics
            try:
                km = data["paths"][0]["distance"] / 1000
                base_seconds = data["paths"][0]["time"] / 1000
                total_seconds = base_seconds * 1.2 + 600
                hrs = int(total_seconds // 3600)
                mins = int((total_seconds % 3600) // 60)
                sec = int(total_seconds % 60)
                st.write(f"**Distance:** {km:.1f} km")
                st.write(f"**Estimated duration:** {hrs:02d}:{mins:02d}:{sec:02d}")
            except Exception:
                st.write("Preview: route metrics unavailable")

            # Two action buttons: Load and Delete
            col_load, col_del = st.columns([1, 1])
            with col_load:
                if st.button("🗺️ Load selected route", key=f"load_selected_{chosen_id}"):
                    # When loading, we set session_state.route_data to the same shape your app expects.
                    # If the stored item is already a 'route_info' dict (has lat/lng etc.) use it directly,
                    # otherwise wrap the GraphHopper response into the expected structure as best as possible.
                    if isinstance(route_data, dict) and ("lat1" in route_data or "loc1" in route_data):
                        st.session_state.route_data = route_data
                    else:
                        # attempt to reconstruct minimal route_info
                        # try to extract first path coords or at least keep the data
                        lat1 = route_data.get("paths", [{}])[0].get("points", {}).get("coordinates", [[None, None]])[0][1] if isinstance(route_data, dict) else None
                        lng1 = route_data.get("paths", [{}])[0].get("points", {}).get("coordinates", [[None, None]])[0][0] if isinstance(route_data, dict) else None
                        st.session_state.route_data = {
                            "data": route_data,
                            "lat1": lat1 or 0,
                            "lng1": lng1 or 0,
                            "loc1": "Saved start",
                            "lat2": 0,
                            "lng2": 0,
                            "loc2": "Saved dest",
                            "vehicle": "car"
                        }
                    st.success("Loaded saved route into map")
                    st.rerun()

            with col_del:
                if st.button("🗑️ Delete selected route", key=f"delete_selected_{chosen_id}"):
                    delete_route_by_id(chosen_id)
                    st.success("Deleted saved route")
                    st.rerun()

        else:
            st.error("Failed to load saved route data.")
else:
    st.markdown("---")
    st.info("No saved routes yet. Use the sidebar 'Save This Route' button to persist routes.")
