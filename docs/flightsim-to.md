# flightsim.to page text

Ready to paste into the add-on page (Description, FAQ, Changelog). Keep the
Description that is there; add the FAQ after "Known limitations" and the
changelog entry at the end.

## FAQ (new section)

**Clouds appear out of thin air in front of me.** CloudSurf only knows the
cloud you are in: the sim reports nothing ahead. So it places clouds ahead of
you as you enter, and before a deck you are about to climb or descend into.
In scattered cloud that shows. Under Advanced, turn off *Clouds before a
deck* to get clouds only once you are in one, or lower *Spawn distance*. A
version that reads the sim's own cloud volume ahead of you is in the works.

**Clouds on the runway.** Fixed in 1.1: nothing within 200 ft of the ground.

**Does it work with GFX?** Yes. Turn off GFX's wing fade (you would get
both), keep the rest.

**With AtmosphereMod, REX, ActiveSky?** They change the sim's weather and
clouds; CloudSurf reads the result, so they go together. If the clouds look
off, try CloudSurf alone once to tell which is which.

**MSFS 2020?** No. CloudSurf uses the 2024 WASM API for effects; the module
does not load in 2020. Sorry.

**The toolbar button is missing.** Enable it in the toolbar settings (the
pencil icon). Open the panel once per flight so CloudSurf knows the deck.

**The clouds are dark or olive.** Up to 1.0 they were drawn in the sim's
default smoke material, which has dark, brownish colour multipliers. 1.1 uses
its own white material. Still too dark? Raise *Brightness* under Advanced.

**Wing fade does nothing.** It follows the clouds around you: thin cloud
gives little. Raise *Intensity* or the *Wing fade* slider; in thick cloud it
should be clearly there.

**Smoke trails behind AI aircraft on landing?** Not CloudSurf: it only spawns
its own effects around your aircraft, never on others. Check your traffic
add-on's effects.

## Changelog

**1.1**
- Clouds come in phases, as in a real cloud: the effect builds up over the
  first 400 m you fly in, the wing fade goes out in a second when you leave.
- Spawn distance follows the cloud: far ahead (1000 m) in thin cloud, half of
  that in thick cloud; every cloud fades in by distance, so none pops.
- Thin cloud is mostly large, light wisps now ("Classic + wisps", the
  default); thick cloud round clouds.
- Own white cloud material: no more dark or olive clouds (the sim's smoke
  material tinted them).
- No clouds within 200 ft of the ground: nothing on the take-off run in
  airport fog.
- New switch under Advanced: *Clouds before a deck* (off = only in cloud).
- Entering a cloud the clouds are around you at once and build up; leaving
  it, nothing new is made, the clouds you passed stay where they are, only
  the ones still ahead in clear air fade.
- Wing fade with depth: a thicker stream of small flakes plus a second layer
  of big flakes above and below the aircraft, going back slower. Its
  brightness has its own setting (*Wing fade brightness*, 0.8x by default),
  because flakes close to the camera come out lighter than the clouds.
- Hotkey Ctrl+Shift+C switches CloudSurf on and off.
- Smoother fades, a slow spin on the clouds, and two wisp textures with hard
  edges fixed.
