import streamlit as st
import requests
import urllib.parse

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
st.set_page_config(page_title="Graphhopper Route Finder", layout="centered")
st.title("🚗 Graphhopper Route Finder")

vehicle = st.selectbox("Choose vehicle:", ["car", "bike", "foot"])
start = st.text_input("Start Location", "")
dest = st.text_input("Destination", "")

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
            paths_url = route_url + urllib.parse.urlencode({"key": key, "vehicle": vehicle}) + op + dp

            response = requests.get(paths_url)
            data = response.json()

            if response.status_code == 200:
                km = data["paths"][0]["distance"] / 1000
                miles = km / 1.60934
                sec = int(data["paths"][0]["time"] / 1000 % 60)
                mins = int(data["paths"][0]["time"] / 1000 / 60 % 60)
                hrs = int(data["paths"][0]["time"] / 1000 / 60 / 60)

                st.subheader(f"Route from {loc1} to {loc2} by {vehicle}")
                st.info(f"**Distance:** {miles:.1f} miles / {km:.1f} km\n\n"
                        f"**Duration:** {hrs:02d}:{mins:02d}:{sec:02d}")

                st.subheader("🛣️ Turn-by-Turn Directions")
                for step in data["paths"][0]["instructions"]:
                    text = step["text"]
                    dist = step["distance"] / 1000
                    st.write(f"- {text} ({dist:.1f} km)")
            else:
                st.error("Routing Error: " + data.get("message", "Unknown error"))
