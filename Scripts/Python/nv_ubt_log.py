"""Tail the UBT log. Report: Saved/NV_ubt.txt"""
import os, unreal
p = os.path.expandvars(r"%LOCALAPPDATA%\UnrealBuildTool\Log.txt")
t = open(p, encoding="utf-8", errors="replace").read().splitlines()
open(unreal.Paths.project_saved_dir() + "NV_ubt.txt", "w").write("\n".join(t[-40:]))
