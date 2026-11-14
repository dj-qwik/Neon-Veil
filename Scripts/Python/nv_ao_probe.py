"""Probe the template aim offsets and idle poses. Report: Saved/NV_ao_probe.txt"""
import unreal
OUT = []
R = "/Game/Characters/Mannequins/Anims/"
for p in ["Rifle/AIM/AO_Rifle", "Pistol/Aim/AO_Pistol"]:
    bs = unreal.load_asset(R + p)
    OUT.append(f"== {p} {bs.get_class().get_name()}")
    for i in range(2):
        try:
            prm = bs.get_editor_property("blend_parameters")[i]
            OUT.append(f"  param{i}: {prm.get_editor_property('display_name')} {prm.get_editor_property('min')}..{prm.get_editor_property('max')}")
        except Exception as e:
            OUT.append(f"  param{i}: ? {e}")
    try:
        for s in bs.get_editor_property("sample_data"):
            a = s.get_editor_property("animation")
            OUT.append(f"  sample {s.get_editor_property('sample_value')} {a.get_name() if a else None} additive={a.get_editor_property('additive_anim_type') if a else None} base={a.get_editor_property('ref_pose_type') if a else None} refseq={a.get_editor_property('ref_pose_seq').get_name() if a and a.get_editor_property('ref_pose_seq') else None}")
    except Exception as e:
        OUT.append(f"  samples ? {e}")
for p in ["Rifle/MF_Rifle_Idle_ADS", "Pistol/MF_Pistol_Idle_ADS", "Rifle/MM_Rifle_Fire", "Rifle/Jog/MF_Rifle_Jog_Fwd", "Rifle/MM_Rifle_Reload", "Rifle/MM_Rifle_Equip", "Pistol/MM_Pistol_Reload", "Pistol/MM_Pistol_Equip", "Pistol/MM_Pistol_Fire", "Unarmed/Attack/MM_Attack_01"]:
    a = unreal.load_asset(R + p)
    rs = a.get_editor_property('ref_pose_seq')
    OUT.append(f"   refpose={a.get_editor_property('ref_pose_type')} {rs.get_name() if rs else None}")
    OUT.append(f"{p}: len={a.get_play_length():.2f} additive={a.get_editor_property('additive_anim_type')} rootmotion={a.get_editor_property('enable_root_motion')} rootlock={a.get_editor_property('force_root_lock')}")
open(unreal.Paths.project_saved_dir() + "NV_ao_probe.txt", "w").write("\n".join(str(x) for x in OUT))
