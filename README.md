# CloudSurf for Microsoft Flight Simulator 2024

Fly *through* clouds instead of sitting in a static fog. While your aircraft is
inside a cloud, CloudSurf places small, soft clouds ahead of you at fixed spots
in the world, so they come at you, sweep over the windows and wings, and fall
behind. How many there are, how dense and how dark they look follows the sim's
own cloud density and the time of day. At night, clouds near your strobes,
beacon and landing lights glow, and the landing lights draw a beam into the
cloud.

It works with any aircraft and any weather source (live weather, presets,
ActiveSky, StrataWx …): CloudSurf never changes the weather, it only reads it.

- Standalone package with its own toolbar panel.
- Own visual effects, material and textures.
- WASM module, no external app needed while flying.

## Install (users)

1. Download a release and copy the `whisperb0x-cloudsurf` folder into your
   Community folder.
2. Start the sim and open **CloudSurf** from the toolbar. If the button does not
   show, enable it in the toolbar settings.
   **Open the panel once after loading a flight**: it reads the cloud layers of
   the active weather, so CloudSurf knows where decks start and end even the
   first time you climb or descend through one. They stay known after you close
   the panel. Without that, CloudSurf learns each deck as you fly through it.
3. If another add-on also adds a wing fade or in-cloud effect, switch that off;
   otherwise you get both effects.

## Settings

The panel opens with a status line (in cloud with its density and how many
clouds are around you, leaving cloud, clear air, paused) and a few controls:

| Setting | Default | What it does |
|---|---|---|
| Fly through clouds | on | CloudSurf on/off |
| Performance | Balanced | **Performance** 35 clouds at once, 6 per step; **Balanced** 60, 8 per step; **Quality** 100, 10 per step |
| Clouds around you | 60 | how many clouds exist at once; moving it makes the preset "custom" |
| Thickness | 2.0x | how opaque and dark the clouds get (they also follow the sim's cloud density) |
| Size | 1.65x | size of all clouds |
| Brightness | 1.0x | cloud brightness, to match the sim's own cloud around you |
| Wing fade | 1.0x | small cloud flakes streaming over the wings in cloud (0 = off) |
| Glow from aircraft lights | 0.85x | how strongly clouds near your lights glow (0 = off) |
| Landing light beam in cloud | on | beam of light in front of the aircraft, in cloud |

Clouds come in random sizes and orientations and come at you from far ahead,
many of them, spread evenly through a box 120 m either side and 50 m above
and below your path by default. They are a neutral light
grey lit by the sim's own light, so the sim decides how dark they are; the
Brightness slider matches them to the sim's cloud. (Advanced has an
experimental unlit look.) The
wing fade is a stream of small cloud flakes flying along with the aircraft,
sent backwards over the wings in a 3 m tube, as many and as dense as the
cloud you are in, with a slow gusty swing.

Most of CloudSurf follows the sim on its own: when clouds start and stop,
how thick, dark and many they are (the sim's cloud density), how close new
clouds come (near cloud edges and in steep climbs or descents), staying inside
the cloud layer (its real top and base are learned as you fly through them),
which clouds stay or fade out when you leave a cloud, and the light from your
aircraft.

**Advanced** shows what is automatic with live values, the few fixed
settings (cloud style, including the experimental wisps made from cloud photo
textures; distance ahead where new clouds appear, 1200 m and never closer than
500 m; sideways and vertical
spread; clouds per step; sim density for full thickness, 10 %; beam position
and direction) and debug tools (test mode, spawn and clear, live values, a log).

All settings are `L:CLOUDSURF_*` variables, so other tools (MobiFlight,
SPAD.neXt, …) can drive them too. See `kConfigVars` in `src/CloudSurf.cpp`.

## How it works

- **`src/CloudSurf.cpp`** (WASM module): every frame it reads position,
  velocity, `AMBIENT IN CLOUD`, `ENV CLOUD DENSITY` and the lights, spawns
  effects with `fsVfxSpawnInWorld` ahead of the aircraft and stops them once
  behind. Each cloud gets graph parameters: density, size, shade and opacity by
  time of day, the light strengths, and the aircraft position and landing light
  direction in the cloud's own frame. Those are RPN expressions with the
  cloud's position baked in, which the sim evaluates every frame; the effect
  then lights each particle on its own, so only the part of a cloud inside the
  landing light cone or near the strobes, beacon, nav and wing lights glows.
- **Effects** (`msfs-project/PackageSources/VisualEffectLibs`): written as VFX
  editor XML by `tools/make_cloud_vfx.py`. Modelled on how the sim's own steam
  and smoke effects are built: few large soft particles, growing with √age,
  fading in and out, random position, rotation and size per particle, drifting
  with the wind.
- **Light:** in MSFS, particles are not lit by aircraft lights (only the sim's
  own volumetric clouds and fog are). CloudSurf therefore makes the clouds glow
  themselves, falling off with distance, and adds a separate beam effect.

## Build from source

Requirements: MSFS 2024 with Developer Mode, the MSFS 2024 SDK (for the WASM
toolchain), Python 3.

```
python tools/make_cloud_vfx.py   # only when you change the effects
python build.py                  # module + panel into msfs-project/
```

Then in the sim: **Dev Mode → open `msfs-project/CloudSurf.xml` → Build All**,
and

```
python build.py --install        # copies the built package to Community
```

Restart the sim. `python build.py --uninstall` removes it again.

### Tools

| Tool | What it does |
|---|---|
| `tools/make_cloud_vfx.py` | writes the effect XML (tunables at the top) |
| `tools/spb_dump.py` | dumps any compiled `.spb` effect as a tree with field names (reads the sim's Propdefs) |
| `tools/live_monitor.py` | logs CloudSurf and sim values every frame via SimConnect (read-only) |
| `tools/dashboard.py` | live dashboard in your browser for that log (`http://localhost:8765`) |
| `tools/CloudConvert.cs`, `tools/CloudAtlas.cs` | turn cloud photos on black into particle textures and atlases |
| `tools/make_cloud_texture.py` | procedural cloud puff texture |

## Contributing

Ideas and pull requests are welcome. Good starting points: better textures,
per-aircraft light positions, a softer beam, performance tuning (see
`MAX_ALIVE`).

## License

CC BY-NC-SA 4.0: share and adapt, with credit, not for commercial use, and
under the same license. See [LICENSE.md](LICENSE.md) and [CREDITS.md](CREDITS.md).

Not affiliated with Microsoft, Asobo or any add-on developer.
