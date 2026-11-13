# Build Bible addendum A1: licensed music

**Status:** approved by the project owner on 2026-11-13. This supersedes one line of the Build Bible v1.0.

## What changes

§14 *Music and sonic direction* currently reads:

> Score palette: industrial breaks, dark neuro-electronic pulse, restrained atmospheric drones, tense percussive layers. **Original compositions only.**

From now on, replace the last sentence with:

> **Original compositions and properly licensed library music are both permitted.** Every licensed track must be credited in the game's credits (see `Docs/Credits.md`) and must fit the score palette and music states above.

Everything else in §14 still applies:
- The palette and the music states (Explore, Suspicion, Combat, Escape, Boss, Aftermath).
- Dialogue stays intelligible, with separate music, SFX and VO sliders.
- Enemy tells must cut through the music.
- M00 music drops out before the Director handshake (§4).

## Rules for licensed music

1. **Source:** only from a licence that covers use in a commercial game, such as Fab Standard License content in the project's own library. Keep the licence or listing link in `Docs/Credits.md`.
2. **No redistribution:** the source packs stay gitignored and local, the same as other Fab content. Only our own assets and wiring are committed.
3. **Credit:** every track used in a shipped build gets a credit line with track title, artist/seller, pack name and source, both in the in-game credits and in `Docs/Credits.md`. Add the credit when the track is first wired in, not at ship time.
4. **Naming:** in-project imports carry `Fab` in the asset name (for example `MUS_M00_SimSuite_FabCyberPunk06`). That makes licensed music easy to find, audit or swap for an original cue later.
5. **Mixing:** licensed tracks are usually mastered loud (the Cyber Punk v11 pack measures about -9 LUFS). Set volume in-engine so the music sits under VO (VO is normalised to -18 LUFS).
6. **Fit:** the music state still decides the energy. High-energy or metal tracks belong to Combat, Escape and Boss states, not Explore.
