"""Runs another NeonVeil editor script and records any error to Saved/NV_last_run.txt.
Usage (Unreal console):  py "<project>/Scripts/Python/nv_run.py" nv_setup_m1
"""
import sys, os, traceback, runpy
import unreal

name = sys.argv[1] if len(sys.argv) > 1 else ""
here = os.path.dirname(os.path.abspath(__file__))
out = unreal.Paths.project_saved_dir() + "NV_last_run.txt"
try:
    runpy.run_path(os.path.join(here, name + ".py"), run_name="__main__")
    status = "OK " + name
except Exception:
    status = "FAILED " + name + "\n" + traceback.format_exc()
with open(out, "w", encoding="utf-8") as f:
    f.write(status)
unreal.log("[NV] " + status.splitlines()[0])
