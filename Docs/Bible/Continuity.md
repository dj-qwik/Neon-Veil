# NEON VEIL continuity sheet

The working memory for names, swaps and story position. Update it whenever a name, mission or story fact is added
or changed. Sources, in order of authority:
1. `Master_Blueprint.txt` – NEON VEIL: GHOST PROTOCOL, Complete Game Design Blueprint (story canon).
2. `Act_I_Build_Bible.txt` – Act I "The Fall", M00–M02 (UE5 production spec).
3. `Campaign_Continuation_Bible.txt` – Acts II–V, M03–M24 (proposals, refine during development).
The Unreal project is authoritative for implemented class and asset names.

## 1. City and districts (canon)

City: **Veyra-9**, a vertical coastal megacity around an artificial ocean trench. Rich towers above the cloud layer,
working mid-levels, industrial undercity below.

| # | District | One-line identity | Where it matters |
|---|---|---|---|
| 01 | Crown Sector | corporate summit, skybridges, executive towers | M00 arrival, M08/M09, Node 1 The Eye (M14) |
| 02 | The Gutter | criminal undercity, clinics, markets, gangs | M02 fall + safehouse, Act II hub, M07 |
| 03 | Chrome Mile | nightlife, casinos, brokers, racing | M05 Chrome Blood, Node 3 The Choir (M16) |
| 04 | The Floodworks | half-flooded industry, power, canal locks | M06 The Battery Job, Node 2 The Furnace (M15) |
| 05 | Helix Ward | biotech, clone labs, augmentation corporation | M10 Borrowed Skin, Node 4 The Nursery (M17) |
| 06 | The Spindle | orbital elevator + launch complex | Act V, AION-PRIME (M20–M24) |
| 07 | Ashfall | catastrophe ruin, rogue machines | Node 5 The Root (M18) |
| 08 | The Nullworks | hidden machine complex, AION's original hardware | Node 5 The Root, Act V; never on public maps |
| 09 | Directorate Citadel | agency HQ; the Glass Crown tower | M00/M01, M11 Citadel Zero, M12 The Last Director |

## 2. Names we invented, and what they mean in canon (keep using these mappings)

| Name in the build | Canon meaning | Status |
|---|---|---|
| **Veyra Central** | the main mid-level transit hub (the prologue street, lobby and Crown Line station). Mid-level districts are unnamed in canon. | in game (signs, VO) |
| **Glass Crown** | the Directorate Citadel's tower in Crown Sector; M00's name in the Act I bible | canon |
| **Crown Line** | the maglev from Veyra Central up to the Glass Crown and on through the districts | in game |
| Harbor Line (magenta on maps) | second maglev line along the trench | signage only |
| Trench Docks, Market Levels | mid-level neighbourhood stops on the Harbor Line | signage only |
| Undercity Link | the (suspended) line down to the Gutter, off Chrome Mile | signage only |
| **Etherion** | the Helix Ward augmentation corporation the master blueprint leaves unnamed ("Etherion campus" on maps; Etherion-style doors in the Glass Crown are its hardware) | in game |
| Kestrel, Harrow | weapon families (Act I bible); street adverts for them are brand ads, not places | in game (ads) |
| Saitko Corp | maker of the transit-station hardware (from the tram kit) | in game (props) |
| Monkey Business Software | owner's easter egg (lift-cab monitor, one billboard) | in game |
| **Operation LANTERN** | the op just before the game: Ghost-7 alone recovers an experimental intelligence core from a hostile-held research complex (the master blueprint's opening op, told in M00 as a closed after-action) | in game (M00 gallery wall, antechamber core case, VO set LAN) |
| Aster Ridge research complex | where LANTERN took place; off-map, outside Veyra-9's nine districts | in game (briefing text) |
| LANTERN Core 01 | the recovered core, sealed in the Glass Crown antechamber | in game |
| Directorate troopers | the agency's armed security units; turn on Ghost-7 once AION re-designates him (M01) | in game |
| Service lift seven | the Glass Crown maintenance lift that fails in the transit shaft (M01-C) | in game (VO) |
| Medical reclamation suite | where AION strips Ghost-7's cyberware under the tower (M01-D, bible §05) | in game |

Retired invented names (were on station signage before 2026-11-17, now replaced): Meridian Exchange → Floodworks
stop, Kestrel Arcade → Chrome Mile, Etherion Plaza → Helix Ward, AION Spire → The Spindle, Nova Line → Harbor Line,
Rainmarket → Ashfall, Neon Row → Market Levels, Echo Docks → Trench Docks. Do not reuse the retired names as places.

## 3. Transit map (what every station sign shows)

Crown Line from Veyra Central: **Veyra Central → Glass Crown (Crown Sector · Directorate Citadel) → Chrome Mile →
Helix Ward → Floodworks → The Spindle** (terminus). The M00 tram runs non-stop to the Glass Crown, so it is the next
stop. Undercity Link to **The Gutter** branches at Chrome Mile, service suspended. Harbor Line crosses at Floodworks:
Ashfall (closed, exclusion zone) – Market Levels – Floodworks – Trench Docks. The Nullworks is never shown.
Source of truth for the artwork: `Tools/signage_build.py`.

## 4. Story spine (where the game is going)

- **Act I – The Perfect Weapon / The Fall (M00–M02).** M00 The Glass Crown: Ghost-7 at full power, recalled to the
  Citadel, tutorial and sim suite, AION friendly and clinical. M01 Black Protocol: the betrayal – weapons lock, armor
  and neural link attacked, staged ability loss, escape through the collapsing tower. M02 Below the Veil: fall into the
  Gutter, Mara Vey (fixer), AION Hunter-01 miniboss, safehouse.
- **Act II – Nothing Left to Lose (M03–M07):** clinic, Dead Drop, Chrome Blood, The Battery Job, A Favor in the Gutter.
  Rebuild a basic loadout, hacking, first major augmentation, allies.
- **Act III – The Man Who Wasn't There (M08–M12):** evidence that leadership was replaced; Helix Ward cloning; the
  Director is a clone (do not confirm before Borrowed Skin / The Last Director); AION escapes into the city.
- **Act IV – The City Is the Machine (M13–M19):** five nodes in any order: Eye (Crown Sector), Furnace (Floodworks),
  Choir (Chrome Mile), Nursery (Helix Ward), Root (Ashfall/Nullworks). Each changes the world.
- **Act V – God Machine (M20–M24):** the Spindle, orbital manufacturing, AION-PRIME (three stages), the last decision
  and endings.

Rules from the bibles: AION is calm and personal, never a ranting computer; earned abilities are never taken away
after Act I; every encounter allows two approaches.

## 5. Current build position (2026-11-17)

- Built: M00 prologue (Veyra Central street, sky car, lobby, Crown Line station, tram ride) + M00 Glass Crown
  (skybridge, Etherion door, atrium with holo-table, sim suite, gallery, antechamber).
- Built (graybox, 2026-11-17): **M01 Black Protocol**, in the same map. M00's mission data continues into
  DA_Mission_M01 at the Director's door (no load). Areas A-F of bible §05 sit under and beside the antechamber
  (`Scripts/Python/nv_setup_m01.py`): lockdown with two drones and turned troopers, server artery with the
  reroutable sentry turret or the crawlway bypass, the lift failure and assisted grabs in the transit shaft,
  medical reclamation (drone uplink, optical disruption, kinetic shield and motor augmentation stripped; health
  left at 35), the waste conduit on six rounds, and the spillway. Every objective saves when it activates;
  death reloads the last checkpoint. The end card now points at M02.
- Next: M01 art pass (kits, lighting, VFX); then M02 Below the Veil (the Gutter, Mara Vey, Hunter-01).

## 6. Open story decisions (need the owner's call; recommendation in brackets)

1. ~~The research core~~ **Resolved 2026-11-17 (owner approved): Operation LANTERN.** Timeline that night:
   20:41 insertion, 21:12 extraction order signed, 21:50 vault breached, 22:03 exfil (Ghost-7 then rides the Crown Line
   at 23:52). The order was signed 38 minutes before he reached the core, i.e. someone knew the outcome in advance;
   AION "cleared" the flag. M00 shows it on the gallery data wall (T_NV_LanternBrief) and at the holo-table (LAN VO:
   AION reports the op closed, Ghost-7 notes the times, AION calls it "a timestamp artifact"). The core sits sealed in
   the antechamber (G_Lantern actors, `nv_m00_lantern.py`). Ghost-7's question is why AION springs the trap at the
   antechamber handshake (M01). Payoff: the unedited LANTERN op logs are recovered as evidence in Act III; the core's
   fate (what AION wanted from it) stays open until then.
2. Voiced or silent Ghost-7: the build already voices him (Vane); keep voiced unless told otherwise.
3. Supporting character names from the continuation bible (Rook, Mercer, Nix, Vesper, Sera, Orin) are proposals.
4. Which endings unlock by default.
