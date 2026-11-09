# CloudSurf for Microsoft Flight Simulator 2020

This port targets MSFS 2020 and is built with the MSFS 2020 SDK. Aircraft-attached
wing and beam effects are currently disabled for compatibility; the world-space
cloud effects and toolbar panel remain enabled.

Fly *through* clouds instead of sitting in a static fog. While your aircraft is
inside a cloud, CloudSurf places small, soft clouds ahead of you at fixed spots
in the world, so they come at you, sweep over the windows and wings, and fall
behind. How many there are, how dense and how dark they look follows the sim's
own cloud density and the time of day. At night, clouds near your strobes,
beacon and landing lights glow: inside the landing lights' cone, the clouds
light up.

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
   **Open the panel once after loading a flight**, and again after the weather
   changes or on long flights (for example before descent): it reads the cloud
   layers of the active weather, so CloudSurf knows where decks start and end.
   After you close the panel CloudSurf keeps the last layers it got. Without
   them, CloudSurf only goes by being in cloud: clouds are not kept inside a
   deck, and the colour is not lighter near its top.
3. If another add-on also adds a wing fade or in-cloud effect, switch that off;
   otherwise you get both effects.

## Settings

The panel opens with a status line (in cloud with its density and how many
clouds are around you, leaving cloud, clear air, paused) and just a few
controls:

| Setting | Default | What it does |
|---|---|---|
| Fly through clouds | on | CloudSurf on/off |
| Performance | Auto | **Auto** picks the number of clouds (35 to 128, 8 per step) so your frame rate in cloud stays within 10 % of the frame rate just before it; **Performance** 35 clouds at once, 6 per step; **Balanced** 60, 8 per step; **Quality** 100, 10 per step |
| Wing fade | 1.0x | cloud flakes streaming over the wings in cloud (0 = off) |
| Cloud size | 1.65x | size of all clouds |
| Build-up after entering | 250 m | the metres you fly in a cloud over which the effect grows from 30 % to full |
| Spawn distance | 1000 m | how far ahead new clouds appear in thin cloud; in thick cloud half of it |
| Fade-out after leaving | 1.5 s | how fast the clouds still ahead of you fade when you leave a cloud (the ones around and behind you stay) |

**Advanced**, the fifth Performance button, shows every setting in place of
these five, with what is automatic, Calibrate and the debug tools. What you
set there is your own: a preset's clouds-and-steps values stay until you move
them, and moving them keeps you in Advanced.

**Hotkey:** Ctrl+Shift+C switches CloudSurf on and off (or bind `L:CLOUDSURF_ENABLE`).

Among the Advanced settings:

| Setting | Default | What it does |
|---|---|---|
| Cloud style | Classic + wisps | thin cloud mostly large, light wisps from cloud photos, thick cloud round clouds; or Classic only, or Wisps only |
| Intensity | 100 % | how strong the whole effect is: how dense the clouds and the wing fade are, and with that how many clouds come; 0 is practically off |
| Aircraft lights (beta) | 0.85x | how strongly clouds near your lights glow, up to 30x (0 = off); doesn't really work yet |
| Clouds around you | 128 | how many clouds exist at once (with Auto: at most); moving it makes the preset "custom" (Auto off) |
| Thickness | 2.0x | how opaque and dark the clouds get (they also follow the sim's cloud density) |
| Size | 1.65x | size of all clouds |
| Brightness | 1.0x | cloud brightness, times the automatic brightness (darker in denser cloud and thicker decks) |
| Wing fade brightness | 0.8x | the wing flakes' brightness, times the clouds'. They are close to the camera, where the sim's fog does not darken them as it does the clouds further off, so at 1.0x they come out lighter than the cloud around you |
| Clouds before a deck | on | when you climb or descend towards a well covered layer, clouds start before you are in it (from 300 m above the ground); off = clouds only once the sim says you are in cloud |

No clouds come within 60 m (200 ft) of the ground: fog at an airport counts
as cloud in the sim, and clouds rushing past on the take-off run look wrong.

Clouds come in random sizes and orientations and come at you from far ahead,
many of them, spread evenly through a box 100 m either side and 100 m above
and below your path by default. They are a light grey lit by the sim's own
light, darker the denser the cloud and the thicker the deck you are in (fitted
to brightness chosen by hand in a calibration flight), and lighter again in the
upper part of the deck, where the sun comes through; the Brightness slider
scales that. (Advanced has an
experimental unlit look.) The
wing fade is a stream of small cloud flakes flying along with the aircraft,
sent backwards over the wings in a 3 m tube, as many and as dense as the
cloud you are in, with a slow gusty swing.

Most of CloudSurf follows the sim on its own: when clouds start and stop,
how thick, dark and many they are (the sim's cloud density), how close new
clouds come (near cloud edges and in steep climbs or descents), staying inside
the cloud layer of the current weather (150 m inside its top and base),
which clouds stay or fade out when you leave a cloud, and the light from your
aircraft. As soon as you are in a cloud, a wide, thin wall of small clouds
comes first, about 600 m ahead, then the normal clouds, and the cloud builds up
over the first 400 m you fly in it. Thin cloud (below 3 % of the sim's density)
gets only a very light effect: mostly large, light wisps that appear far ahead
and come out of the haze slowly. Thick cloud gets denser round clouds that
appear closer and come out of the murk near you, as in real cloud, where you
see little. Every cloud fades in by distance: invisible where it appears, full
from about a third of the way. Leaving a cloud, the clouds around you stay in
place and fade, the wing fade within a second.

**Calibrate** (under Advanced) tunes the look by hand per cloud density. While it is open its
sliders act live (Auto FPS is off): cloud density, size, number of clouds,
wing fade, brightness, glow from your lights (up to 30x), how often new clouds come (every so many metres
flown), how far ahead they appear, standard clouds on/off, the share of wisps,
and the sideways and vertical spread. Fly in a cloud, tune, and press
**Confirm**: the values are stored for the sim's cloud density there (its
average over the last 5 s); a new point close to an old one (within 10 %)
replaces it. Between the stored points CloudSurf blends the values by density,
beyond them the nearest point holds. Without points the normal settings apply.

**Advanced** shows what is automatic with live values, the few fixed
settings (fade by distance from the aircraft; sideways and vertical
spread; clouds per step; sim density for full thickness, 10 %; landing light
direction) and debug tools (test mode, spawn and clear, live values, a log).

All settings are `L:CLOUDSURF_*` variables, so other tools (MobiFlight,
SPAD.neXt, …) can drive them too. See `kConfigVars` in `src/CloudSurf.cpp`.

## Questions people ask

- **Clouds appear out of thin air in front of me.** CloudSurf only knows the
  cloud you are in (the sim reports nothing ahead), so it places clouds ahead
  of you as you enter, and before a deck you are about to climb or descend
  into. In scattered cloud that shows. Turn off *Clouds before a deck* under
  Advanced to get clouds only once you are in one, or lower *Spawn distance*.
  A version that reads the sim's own cloud volume ahead of you is in the
  works.
- **Clouds on the runway.** Fixed in 1.1: nothing within 200 ft of the ground.
- **Does it work with GFX?** The world-space clouds can run alongside it. The
  CloudSurf aircraft-attached wing and beam effects are disabled in this port.
- **With AtmosphereMod, REX, ActiveSky?** They change the sim's weather and
  clouds; CloudSurf reads the result, so they go together. If the clouds look
  off, try CloudSurf alone once to tell which is which.
- **MSFS 2024?** This build targets MSFS 2020. It is compiled with the 2020
  SDK and should be installed only in the 2020 Community folder.
- **The toolbar button is missing.** Enable it in the toolbar settings (the
  pencil icon). Open the panel once per flight so CloudSurf knows the deck.
- **The clouds are dark or olive.** Up to 1.0 the clouds were drawn in the
  sim's default smoke material, which has dark, brownish colour multipliers.
  1.1 uses its own white material. If they are still too dark, raise
  *Brightness* under Advanced.
- **Where are wing fade and the beam?** They are disabled in this MSFS 2020
  port; the world-space cloud effects remain available.

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
  themselves, falling off with distance. (A separate visible beam of mist is
  in the code but off: it pointed the wrong way.)

## Build from source

Requirements: MSFS 2020 with Developer Mode, the MSFS 2020 SDK (for the WASM
toolchain), Python 3. CloudSurf uses the 2020 VFX API and package format.

```
python tools/make_cloud_vfx.py   # only when you change the effects
python build.py                  # module + panel into msfs-project/
```

Then in MSFS 2020: **Dev Mode → open `msfs-project/CloudSurf.xml` → Build All**,
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

## Contributing

Ideas and pull requests are welcome. Good starting points: better textures,
per-aircraft light positions, a visible beam that points the right way, performance tuning (see
`MAX_ALIVE`).

## License

CC BY-NC-SA 4.0: share and adapt, with credit, not for commercial use, and
under the same license. See [LICENSE.md](../LICENSE.md) and [CREDITS.md](../CREDITS.md).

Not affiliated with Microsoft, Asobo or any add-on developer.
