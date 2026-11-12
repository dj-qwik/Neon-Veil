"""Probe the MetaHuman Creator Python API in this engine build. Report: Saved/NV_mh_probe.txt"""
import unreal
out = []
names = [n for n in dir(unreal) if "MetaHuman" in n]
out.append("classes: " + ", ".join(names))
for n in names:
    if "Subsystem" in n or "Library" in n or n.endswith("Character") or "Assembl" in n or "Preset" in n:
        c = getattr(unreal, n)
        out.append(f"--- {n}: " + ", ".join(m for m in dir(c) if not m.startswith("_") and m not in dir(unreal.Object)))
with open(unreal.Paths.project_saved_dir() + "NV_mh_probe.txt", "w", encoding="utf-8") as fh:
    fh.write("\n".join(out))
