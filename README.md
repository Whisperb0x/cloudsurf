# CloudPass for Microsoft Flight Simulator 2024

Fly *through* clouds instead of sitting in a static fog. While your aircraft is
inside a cloud, CloudPass places small, soft clouds ahead of you at fixed spots
in the world, so they come at you, sweep over the windows and wings, and fall
behind. How many there are, how dense and how dark they look follows the sim's
own cloud density and the time of day. At night, clouds near your strobes,
beacon and landing lights glow, and the landing lights draw a beam into the
cloud.

It works with any aircraft and any weather source (live weather, presets,
ActiveSky, StrataWx …): CloudPass never changes the weather, it only reads it.

- Standalone package with its own toolbar panel.
- Own visual effects, material and textures.
- WASM module, no external app needed while flying.

## Install (users)

1. Download a release and copy the `whisperb0x-cloudpass` folder into your
   Community folder.
2. Start the sim and open **CloudPass** from the toolbar. If the button does not
   show, enable it in the toolbar settings.
3. If you use GFX, switch its *Wing Fade* off; otherwise you get both effects.

## Settings

The panel shows these controls; everything else is under **Show debug tools**.

| Setting | Default | What it does |
|---|---|---|
| Clouds passing by | on | CloudPass on/off |
| Cloud density | 1.0x | overall opacity and darkness of the clouds |
| Cloud size | 1.0x | size of all clouds |
| Glow from aircraft lights | 1.0x | how strongly clouds near your lights glow (0 = off) |
| Landing light beam in cloud | on | beam of light in front of the aircraft, in cloud |

Debug tools: effect choice (`Cloudpass` with the sim's smoke material,
`CloudpassAtlas` with 16 cloud wisps), test mode (spawns in clear sky), spawn
and clear buttons, live values, a log, and advanced settings: distance ahead
(600–800 m), spacing, clouds per step, spread, share over the wings, clear zone
around the flight path, max clouds alive (45), density mapping (cloud density
for full effect 25 %, minimum 0.3 %), beam position and direction.

All settings are `L:CLOUDPASS_*` variables, so other tools (MobiFlight,
SPAD.neXt, …) can drive them too. See `kConfigVars` in `src/CloudPass.cpp`.

## How it works

- **`src/CloudPass.cpp`** (WASM module): every frame it reads position,
  velocity, `AMBIENT IN CLOUD`, `ENV CLOUD DENSITY` and the lights, spawns
  effects with `fsVfxSpawnInWorld` ahead of the aircraft and stops them once
  behind. Each cloud gets graph parameters: density, size, shade and opacity by
  time of day, and glow. The glow parameters are RPN expressions with the
  cloud's own position baked in; the sim evaluates them every frame, so only
  clouds near the lights light up.
- **Effects** (`msfs-project/PackageSources/VisualEffectLibs`): written as VFX
  editor XML by `tools/make_cloud_vfx.py`. Modelled on how the sim's own steam
  and smoke effects are built: few large soft particles, growing with √age,
  fading in and out, random position, rotation and size per particle, drifting
  with the wind.
- **Light:** in MSFS, particles are not lit by aircraft lights (only the sim's
  own volumetric clouds and fog are). CloudPass therefore makes the clouds glow
  themselves, falling off with distance, and adds a separate beam effect.

## Build from source

Requirements: MSFS 2024 with Developer Mode, the MSFS 2024 SDK (for the WASM
toolchain), Python 3.

```
python tools/make_cloud_vfx.py   # only when you change the effects
python build.py                  # module + panel into msfs-project/
```

Then in the sim: **Dev Mode → open `msfs-project/CloudPass.xml` → Build All**,
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
| `tools/live_monitor.py` | logs CloudPass and sim values every frame via SimConnect (read-only) |
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
