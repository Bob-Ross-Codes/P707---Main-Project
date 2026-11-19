# Raadhuspladsen Modern — generators

Blender scripts that build the models in `Assets/3D Assets/Raadhuspladsen Modern/`, in Unity scene
coordinates (exported FBX lands 1:1; City Hall is placed at (0.5, 0, 93.8), yaw 2°).

- `osm/scene_features.json` — OpenStreetMap features (© OpenStreetMap contributors, ODbL) converted to
  scene metres by `osm2scene.py` (tower spire = OSM Rådhustårnet is the anchor).
- `build_ground.py`, `build_cityhall.py`, `build_props.py` — run in Blender 4.2; each re-exports its FBX.
- `placements.py` — OSM trees/lamps/benches/bins/bollards/racks visible through the window → text list
  used to scatter prefabs in the scene.
