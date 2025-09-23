import requests
import urllib.parse
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox

route_url = "https://graphhopper.com/api/1/route?"
key = "571cae75-8241-46bb-af7f-62d0eaa4bc96"  # <-- replace or load from env

def geocoding(location, key):
    if location.strip() == "":
        return None, None, "Invalid location"

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

def get_route():
    vehicle = vehicle_var.get()
    start = start_entry.get()
    dest = dest_entry.get()

    lat1, lng1, loc1 = geocoding(start, key)
    lat2, lng2, loc2 = geocoding(dest, key)

    if not lat1 or not lat2:
        messagebox.showerror("Error", f"Failed to geocode:\n{loc1}\n{loc2}")
        return

    op = "&point=" + str(lat1) + "%2C" + str(lng1)
    dp = "&point=" + str(lat2) + "%2C" + str(lng2)
    paths_url = route_url + urllib.parse.urlencode({"key": key, "vehicle": vehicle}) + op + dp

    response = requests.get(paths_url)
    data = response.json()

    output_box.delete(1.0, tk.END)  # clear old text

    if response.status_code == 200:
        km = data["paths"][0]["distance"] / 1000
        miles = km / 1.60934
        sec = int(data["paths"][0]["time"] / 1000 % 60)
        mins = int(data["paths"][0]["time"] / 1000 / 60 % 60)
        hrs = int(data["paths"][0]["time"] / 1000 / 60 / 60)

        output_box.insert(tk.END, f"Route from {loc1} to {loc2} by {vehicle}\n")
        output_box.insert(tk.END, f"Distance: {miles:.1f} miles / {km:.1f} km\n")
        output_box.insert(tk.END, f"Duration: {hrs:02d}:{mins:02d}:{sec:02d}\n\n")

        for step in data["paths"][0]["instructions"]:
            text = step["text"]
            dist = step["distance"] / 1000
            output_box.insert(tk.END, f"- {text} ({dist:.1f} km)\n")
    else:
        output_box.insert(tk.END, "Routing Error: " + data.get("message", "Unknown error"))

# --- GUI setup ---
root = tk.Tk()
root.title("Graphhopper Route Finder")

frame = ttk.Frame(root, padding="10")
frame.grid(row=0, column=0, sticky="nsew")

# Inputs
ttk.Label(frame, text="Vehicle:").grid(row=0, column=0, sticky="w")
vehicle_var = tk.StringVar(value="car")
vehicle_menu = ttk.Combobox(frame, textvariable=vehicle_var, values=["car", "bike", "foot"], state="readonly")
vehicle_menu.grid(row=0, column=1)

ttk.Label(frame, text="Start:").grid(row=1, column=0, sticky="w")
start_entry = ttk.Entry(frame, width=40)
start_entry.grid(row=1, column=1)

ttk.Label(frame, text="Destination:").grid(row=2, column=0, sticky="w")
dest_entry = ttk.Entry(frame, width=40)
dest_entry.grid(row=2, column=1)

ttk.Button(frame, text="Get Route", command=get_route).grid(row=3, column=0, columnspan=2, pady=10)

# Output box
output_box = scrolledtext.ScrolledText(frame, width=60, height=20, wrap=tk.WORD)
output_box.grid(row=4, column=0, columnspan=2, pady=5)

root.mainloop()
