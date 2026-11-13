# Sim drone prep (offline, Python + numpy/scipy)
Source: Fab "FREE SciFi Drone" (Oleg Ushenok), single untextured 1.3M-tri OBJ. Not redistributed;
re-export from Fab to Saved/Megascans/ and run:
1. parse.py <Drone.obj>  -> mesh.npz
2. comps.py              -> per-part labels (186 connected parts)
3. pal.py + split_materials.py -> SM_SimDrone_Body/Core.obj with 5 material slots
   (white paint, orange paint, dark metal, cyan glow, yellow glow; part IDs picked against the cover art)
4. Collision proxy: one convex hull per part (lens excluded), ~7k tris after import -> SM_SimDrone_BodyCol.obj
   (hulls.py; per-triangle collision on the 1.3M source froze the editor).
Editor: nv_drone_import.py, then nv_drone_shell.py (uses SM_SimDrone_Shell + BodyCol complex collision).
