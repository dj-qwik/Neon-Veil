import unreal
O = []
for n in ("GeometryScript_Primitives", "GeometryScript_AssetUtils", "GeometryScript_MeshTransforms", "GeometryScript_MeshMaterialFunctions", "DynamicMesh", "GeometryScriptPrimitiveOptions"):
    O.append(f"{n}: {hasattr(unreal, n)}")
if hasattr(unreal, "GeometryScript_Primitives"):
    O.append(" ".join(sorted(x for x in dir(unreal.GeometryScript_Primitives) if x.startswith("append"))))
m = unreal.load_asset("/Game/NeonVeil/Materials/FX/M_NV_TrafficCar")
O.append(f"car mat shading {m.get_editor_property('shading_model')} blend {m.get_editor_property('blend_mode')}")
try:
    O.append("exprs: " + ", ".join(sorted({type(e).__name__ for e in unreal.MaterialEditingLibrary.get_material_expressions(m)}) ) if hasattr(unreal.MaterialEditingLibrary, "get_material_expressions") else "no expr api")
except Exception as e: O.append(str(e))
open(unreal.Paths.project_saved_dir() + "NV_gs_check.txt", "w").write("\n".join(O))
