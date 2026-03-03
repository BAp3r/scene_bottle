import os
import sys

from isaacsim import SimulationApp
app = SimulationApp({"headless": True})

from isaacsim.storage.native import get_assets_root_path
import omni.client

def list_nucleus_dir(url):
    print(f"Listing: {url}")
    result, entries = omni.client.list(url)
    if result != omni.client.Result.OK:
        print(f"Failed to list {url}, result: {result}")
        return
    for e in entries:
        print("  -", e.relative_path)

assets_root = get_assets_root_path()
if assets_root:
    print("Assets root:", assets_root)
    orbbec_url = assets_root + "/Isaac/Sensors/Orbbec"
    list_nucleus_dir(orbbec_url)
    list_nucleus_dir(orbbec_url + "/Gemini_330_Series")
else:
    print("Cannot find assets root.")

app.close()
