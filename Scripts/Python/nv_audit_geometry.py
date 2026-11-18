"""Whole-level geometry pass for the open map: z-fighting and collision problems. Finds, fixes (unless arg "report"),
saves, and writes Saved/NV_geom_<map>.txt.

Z-fighting
  dup     same mesh, same transform twice: the extra copy is moved to folder _NV_Removed and hidden (not deleted)
  flat    a flat sheet (plane / sign / decal mesh, < 1 cm thick) lying in another surface: pushed 0.6 cm out of it
  cop     two solid pieces whose faces share a plane and overlap (floor tiles, wall panels, trim): the smaller piece
          (a graybox cube always yields to an art piece) is sunk 0.5 cm under a shared top, or thinned 0.8-2.3 cm on the shared axis (faces recede, centre stays). Confirmed with traces where both pieces collide; engine cubes
          (flat by construction) are trusted on bounds alone.
Collision
  walk    a floor-standing prop you would walk straight through (collision off, or its mesh has no collision shape):
          collision on (BlockAll), and meshes with no shape get "use complex as simple"
  float   a floor prop (crate, bench, bin, planter...) hovering 1.5-15 cm above the floor: dropped onto it
  ghost   hidden actors that still block the player outside any visible geometry: listed only (may be intended)
"""
import unreal, math, sys, re
EAS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
W = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
REPORT = "report" in sys.argv
V = unreal.Vector
TQ = unreal.TraceTypeQuery.TRACE_TYPE_QUERY1
out, fixes = [], {"dup": 0, "flat": 0, "cop": 0, "walk": 0, "walkmesh": 0, "float": 0}
CUBE = "/Engine/BasicShapes/Cube"
PLANE = "/Engine/BasicShapes/Plane"
SKIP = re.compile(r"rain|fx|holo(?!screen_.*frame)|glow|beam|light|decal|volume|fog|plant|leaf|grass|cable|wire|cloud|sky|"
                  r"npc|crowd|citizen|reflection|mirror|nav|arrow|trigger|blocker|_lod|sun|moon|window|glass|water|puddle", re.I)
PROP = re.compile(r"crate|box(?!ing)|barrel|bin|chair|bench|stool|table|planter|vending|locker|cart|trolley|case|desk|"
                  r"cabinet|drum|cone|bollard|kiosk|bag|container|pallet|seat|sofa|couch", re.I)

def tr(s, e, ignore=()):
    h = unreal.SystemLibrary.line_trace_single(W, s, e, TQ, True, list(ignore), unreal.DrawDebugTrace.NONE, True)
    if not h:
        return None
    t = h.to_tuple()
    return (t[9], t[4], (t[4] - s).length())

def comp(a):
    try:
        return a.static_mesh_component
    except Exception:
        return None

def axis_aligned(r):
    return all(abs(((x + 360.0) % 90.0) - 0) < 0.5 or abs(((x + 360.0) % 90.0) - 90.0) < 0.5 for x in (r.roll, r.pitch, r.yaw))

def is_hidden(a):
    try:
        return bool(a.get_editor_property("hidden")) or not comp(a).is_visible()
    except Exception:
        return False

items = []
for a in EAS.get_all_level_actors():
    if not isinstance(a, unreal.StaticMeshActor):
        continue
    c = comp(a)
    m = c.static_mesh if c else None
    if not m:
        continue
    o, e = a.get_actor_bounds(False)
    items.append(dict(a=a, c=c, m=m, mp=m.get_path_name().split(".")[0], lab=a.get_actor_label(), o=o, e=e,
                      lo=(o.x - e.x, o.y - e.y, o.z - e.z), hi=(o.x + e.x, o.y + e.y, o.z + e.z),
                      hidden=is_hidden(a),
                      aligned=axis_aligned(a.get_actor_rotation()),
                      coll=c.get_collision_enabled() != unreal.CollisionEnabled.NO_COLLISION))
out.append("%d static mesh actors" % len(items))

# spatial hash on 4 m cells
CELL = 400.0
grid = {}
for i, it in enumerate(items):
    if it["hidden"] or max(it["e"].x, it["e"].y, it["e"].z) > 6000:
        continue
    for gx in range(int(math.floor(it["lo"][0] / CELL)), int(math.floor(it["hi"][0] / CELL)) + 1):
        for gy in range(int(math.floor(it["lo"][1] / CELL)), int(math.floor(it["hi"][1] / CELL)) + 1):
            for gz in range(int(math.floor(it["lo"][2] / CELL)), int(math.floor(it["hi"][2] / CELL)) + 1):
                grid.setdefault((gx, gy, gz), []).append(i)
pairs = set()
for ids in grid.values():
    if len(ids) > 400:
        ids = ids[:400]
    for x in range(len(ids)):
        for y in range(x + 1, len(ids)):
            pairs.add((ids[x], ids[y]) if ids[x] < ids[y] else (ids[y], ids[x]))
out.append("%d nearby pairs" % len(pairs))

def overlap_area(A, B, ax):
    o = [k for k in range(3) if k != ax]
    w = [min(A["hi"][k], B["hi"][k]) - max(A["lo"][k], B["lo"][k]) for k in o]
    return (w[0] * w[1]) if w[0] > 0 and w[1] > 0 else 0.0, o, w

def face_area(A, ax):
    o = [k for k in range(3) if k != ax]
    return (A["hi"][o[0]] - A["lo"][o[0]]) * (A["hi"][o[1]] - A["lo"][o[1]])

def move(it, d):
    a = it["a"]
    a.modify()
    a.set_actor_location(a.get_actor_location() + d, False, False)

moved = set()
# ------------------------------------------------------------------ dup
seen = {}
for i, it in enumerate(items):
    if it["hidden"]:
        continue
    l, r, s = it["a"].get_actor_location(), it["a"].get_actor_rotation(), it["a"].get_actor_scale3d()
    key = (it["mp"], round(l.x), round(l.y), round(l.z), round(r.roll), round(r.pitch), round(r.yaw), round(s.x, 2), round(s.y, 2), round(s.z, 2))
    if key in seen:
        out.append("dup   %-34s same as %s" % (it["lab"], items[seen[key]]["lab"]))
        if not REPORT:
            a = it["a"]; a.modify()
            a.set_folder_path("_NV_Removed"); a.set_actor_hidden_in_game(True); a.set_is_temporarily_hidden_in_editor(True)
            it["c"].set_collision_profile_name("NoCollision")
            it["hidden"] = True
        fixes["dup"] += 1
        moved.add(i)
    else:
        seen[key] = i

# ------------------------------------------------------------------ flat + cop
for i, j in pairs:
    A, B = items[i], items[j]
    if A["hidden"] or B["hidden"] or i in moved or j in moved:
        continue
    for ax in range(3):
        tA = A["hi"][ax] - A["lo"][ax]; tB = B["hi"][ax] - B["lo"][ax]
        area, o, w = overlap_area(A, B, ax)
        if area <= 0:
            continue
        # flat sheet against a face
        for F, S, tF in ((A, B, tA), (B, A, tB)):
            if tF >= 1.0 or (S["hi"][ax] - S["lo"][ax]) < 1.0:
                continue
            if area < 0.2 * face_area(F, ax):
                continue
            p = (F["lo"][ax] + F["hi"][ax]) / 2
            for face, sign in ((S["hi"][ax], 1.0), (S["lo"][ax], -1.0)):
                if abs(p - face) > 0.25:
                    continue
                # where it is a real surface: both a trace from outside hits S at the sheet's plane
                cen = [ (max(A["lo"][k], B["lo"][k]) + min(A["hi"][k], B["hi"][k])) / 2 for k in range(3)]
                n = [0.0, 0.0, 0.0]; n[ax] = sign
                s = V(*[cen[k] + n[k] * 10 for k in range(3)]); cen[ax] = face
                e = V(*[cen[k] - n[k] * 10 for k in range(3)])
                h = tr(s, e, [F["a"]])
                real = (h and h[0] == S["a"] and abs(h[2] - 10.0) < 0.4) or S["mp"] == CUBE or not S["coll"]
                if not real:
                    continue
                out.append("flat  %-34s in %-30s axis %s" % (F["lab"], S["lab"], "XYZ"[ax]))
                if not REPORT:
                    d = V(0, 0, 0); setattr(d, "xyz"[ax], sign * 0.6 + (face - p))
                    move(F, d)
                fixes["flat"] += 1
                moved.add(items.index(F))
                break
        if i in moved or j in moved:
            break
    # (coplanar solids handled below)

# ------------------------------------------------------------------ coplanar solids
def coplanar_faces(A, B):
    faces = []
    for ax in range(3):
        if (A["hi"][ax] - A["lo"][ax]) < 1.0 or (B["hi"][ax] - B["lo"][ax]) < 1.0:
            return []
        depth = min(A["hi"][ax], B["hi"][ax]) - max(A["lo"][ax], B["lo"][ax])
        if depth <= 0.5:
            return []            # they only touch: no shared visible face
    for ax in range(3):
        area, o, w = overlap_area(A, B, ax)
        if area < 100.0:
            continue
        for k, sign in ((1, 1.0), (0, -1.0)):
            if ax == 2 and sign < 0:
                continue         # undersides: never seen
            fa = (A["hi"] if k else A["lo"])[ax]; fb = (B["hi"] if k else B["lo"])[ax]
            if abs(fa - fb) <= 0.2:
                faces.append((ax, sign, fa, area))
    return faces

for i, j in pairs:
    A, B = items[i], items[j]
    if A["hidden"] or B["hidden"] or i in moved or j in moved:
        continue
    faces = coplanar_faces(A, B)
    if not faces:
        continue
    small, big = (A, B) if (A["e"].x * A["e"].y * A["e"].z) <= (B["e"].x * B["e"].y * B["e"].z) else (B, A)
    if (A["mp"] == CUBE) != (B["mp"] == CUBE):
        # graybox cube vs art kit piece: the art must stay on top, the graybox yields whatever its size
        small, big = (A, B) if A["mp"] == CUBE else (B, A)
    confirmed = []
    for ax, sign, f, area in faces:
        ok = A["mp"] == CUBE and B["mp"] == CUBE and A["aligned"] and B["aligned"]
        if not ok and A["coll"] and B["coll"]:
            cen = [(max(A["lo"][q], B["lo"][q]) + min(A["hi"][q], B["hi"][q])) / 2 for q in range(3)]
            cen[ax] = f
            n = [0.0, 0.0, 0.0]; n[ax] = sign
            st = V(*[cen[q] + n[q] * 20 for q in range(3)]); en = V(*[cen[q] - n[q] * 5 for q in range(3)])
            h1 = tr(st, en)
            if h1 and h1[0] in (A["a"], B["a"]) and abs(h1[2] - 20) < 0.4:
                other = B["a"] if h1[0] == A["a"] else A["a"]
                h2 = tr(st, en, [h1[0]])
                ok = bool(h2 and h2[0] == other and abs(h2[2] - h1[2]) < 0.3)
        if ok:
            confirmed.append((ax, sign))
    if not confirmed:
        continue
    out.append("cop   %-34s / %-30s faces %s" % (small["lab"], big["lab"], " ".join(("+" if sg > 0 else "-") + "XYZ"[ax] for ax, sg in confirmed)))
    if not REPORT:
        a = small["a"]; a.modify()
        if (2, 1.0) in confirmed:
            # shared top (floors, ledges): sink the smaller one under the bigger one's surface
            a.set_actor_location(a.get_actor_location() - V(0, 0, 0.5), False, False)
        else:
            # thin the smaller piece on the shared axis so its faces sit behind the other's. The amount varies per
            # piece (0.8 - 2.3 cm) so rows of identical pieces (parapets, frame bars) don't end up level again.
            k = sum(ord(ch) for ch in small["lab"]) % 4
            for ax in sorted(set(ax for ax, sg in confirmed)):
                t = small["hi"][ax] - small["lo"][ax]
                th = 0.8 + 0.5 * k
                if t <= th + 1.0:
                    continue
                wv = [V(1, 0, 0), V(0, 1, 0), V(0, 0, 1)][ax]
                loc = [a.get_actor_forward_vector(), a.get_actor_right_vector(), a.get_actor_up_vector()]
                li = max(range(3), key=lambda q: abs(loc[q].dot(wv)))
                sc = a.get_actor_scale3d()
                f = (t - th) / t
                a.set_actor_scale3d(V(sc.x * (f if li == 0 else 1), sc.y * (f if li == 1 else 1), sc.z * (f if li == 2 else 1)))
                o2, e2 = a.get_actor_bounds(False)
                a.set_actor_location(a.get_actor_location() + (small["o"] - o2), False, False)
    fixes["cop"] += 1
    moved.add(items.index(small))

# ------------------------------------------------------------------ walk-through props
mesh_fixed = set()
for it in items:
    if it["hidden"] or SKIP.search(it["lab"]) or SKIP.search(it["mp"]):
        continue
    e = it["e"]
    if e.z * 2 < 50 or min(e.x, e.y) * 2 < 20 or max(e.x, e.y) * 2 > 800 or e.z * 2 > 600:
        continue
    bot = V(it["o"].x, it["o"].y, it["lo"][2] + 2)
    h = tr(bot, bot - V(0, 0, 40), [it["a"]])
    if not h:
        continue    # not standing on a floor
    m = it["m"]
    nshape = unreal.EditorStaticMeshLibrary.get_simple_collision_count(m)
    bs = m.get_editor_property("body_setup")
    ctf = bs.get_editor_property("collision_trace_flag") if bs else None
    complex_ok = ctf == unreal.CollisionTraceFlag.CTF_USE_COMPLEX_AS_SIMPLE
    if it["coll"]:
        continue   # collision on: kit meshes without counted shapes still collide (checked: they block box sweeps)
    if it["coll"]:
        # project default may still give it a shape: sweep a box through it on simple collision only
        mid = V(it["o"].x, it["o"].y, it["lo"][2] + min(60.0, e.z))
        hb = unreal.SystemLibrary.box_trace_single(W, mid + V(e.x + 40, 0, 0), mid, V(10, 10, 10), unreal.Rotator(), TQ, False, [], unreal.DrawDebugTrace.NONE, True)
        if hb and hb.to_tuple()[9] == it["a"]:
            continue
    why = "collision off" if not it["coll"] else "mesh has no collision shape"
    out.append("walk  %-34s %.0fx%.0fx%.0f %s (%s)" % (it["lab"], e.x*2, e.y*2, e.z*2, why, it["mp"]))
    if not REPORT:
        if not it["coll"]:
            it["c"].modify(); it["c"].set_collision_profile_name("BlockAll")
        if nshape == 0 and not complex_ok and it["mp"] not in mesh_fixed and bs and not it["mp"].startswith("/Engine"):
            bs.set_editor_property("collision_trace_flag", unreal.CollisionTraceFlag.CTF_USE_COMPLEX_AS_SIMPLE)
            m.modify(); unreal.EditorAssetLibrary.save_loaded_asset(m)
            mesh_fixed.add(it["mp"]); fixes["walkmesh"] += 1
    fixes["walk"] += 1

# ------------------------------------------------------------------ floating floor props
for it in items:
    if it["hidden"] or not PROP.search(it["lab"] + " " + it["mp"]) or max(it["e"].x, it["e"].y, it["e"].z) * 2 > 400:
        continue
    if re.search(r"plant\d|_plant|flower|foliage", it["lab"], re.I):
        continue
    under = V(it["o"].x, it["o"].y, it["lo"][2] - 1.0)
    if any(v is not it and not v["hidden"] and all(v["lo"][k] - 0.5 <= (under.x, under.y, under.z)[k] <= v["hi"][k] + 0.5 for k in range(3)) for v in items):
        continue
    bot = V(it["o"].x, it["o"].y, it["lo"][2] - 0.1)
    h = tr(bot, bot - V(0, 0, 60), [it["a"]])
    if not h or h[2] < 1.5 or h[2] > 15.0:   # bigger gaps are props resting on non-colliding furniture (checked by eye)
        continue
    # anything else touching its underside (shelf, another crate)? check the four corners too
    sup = False
    for dx, dy in ((-0.4, -0.4), (0.4, -0.4), (-0.4, 0.4), (0.4, 0.4)):
        p = V(it["o"].x + it["e"].x * dx * 2, it["o"].y + it["e"].y * dy * 2, it["lo"][2] - 0.1)
        hc = tr(p, p - V(0, 0, 60), [it["a"]])
        if hc and hc[2] < 1.5:
            sup = True
    if sup:
        continue
    out.append("float %-34s %.1f cm above %s" % (it["lab"], h[2], h[0].get_actor_label() if h[0] else "?"))
    if not REPORT:
        move(it, V(0, 0, -(h[2] - 0.1)))
    fixes["float"] += 1

# ------------------------------------------------------------------ invisible blockers
vis = [it for it in items if not it["hidden"] and it["coll"]]
for it in items:
    if not it["hidden"] or not it["coll"] or it["a"].get_folder_path() == "_NV_Removed":
        continue
    vol = max(1.0, it["e"].x * it["e"].y * it["e"].z * 8)
    cov = 0.0
    for v in vis:
        w = [min(it["hi"][k], v["hi"][k]) - max(it["lo"][k], v["lo"][k]) for k in range(3)]
        if min(w) > 0:
            cov += w[0] * w[1] * w[2]
    if cov / vol < 0.5:
        out.append("ghost %-34s %.0fx%.0fx%.0f at %.0f,%.0f,%.0f covered %.0f%%" % (it["lab"], it["e"].x*2, it["e"].y*2, it["e"].z*2, it["o"].x, it["o"].y, it["o"].z, 100*cov/vol))

out.insert(0, "fixes: " + ", ".join("%s %d" % kv for kv in fixes.items()) + ("  (report only)" if REPORT else ""))
if not REPORT and any(fixes.values()):
    unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).save_current_level()
open(unreal.Paths.project_saved_dir() + "NV_geom_%s.txt" % W.get_name(), "w").write("\n".join(out))
