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

This update is mostly about the two things people wrote about most: clouds
that seemed to appear out of nowhere, and clouds that came out dark. Thank
you for the reports.

Entering and leaving a cloud now happens the way the sim's own grey does.
The moment you are in a cloud, the clouds are around you and ahead of you,
and the effect builds up over the first few hundred metres instead of
starting far ahead and arriving later. When you leave, nothing new is made
from that moment on; the clouds you just flew through stay where they are
behind you, and only the ones still ahead, in what is now clear air, fade.
Seen from outside, the effect no longer trails the aircraft like a plume.

The wing fade has depth now. The small flakes stream through a thicker tube
instead of a flat sheet in the plane of the wings, and a second layer of big
flakes above and below the aircraft goes back more slowly, so the stream has
parallax. Flakes close to the camera come out lighter than clouds further
away, because the sim's fog does not reach them, so the wing fade has its own
brightness setting (0.8x by default).

The clouds are drawn in CloudSurf's own white material. Up to 1.0 they used
the sim's default smoke material, whose colour multipliers are dark and
brownish; that is where the dark and olive clouds came from. If they now look
a little too light for your taste, Brightness under Advanced brings them
down.

Nothing is placed within 200 ft of the ground any more. Fog at an airport
counts as cloud in the sim, which put clouds on the take-off run. Clouds that
start before a deck you are about to climb or descend into can be switched
off under Advanced (Clouds before a deck), so that in scattered cloud you
only get clouds once you are in one.

Clouds come in phases as in a real cloud, and the spawn distance follows the
cloud: far ahead in thin cloud, half of that in thick cloud, every cloud
fading in by distance so none pops. Thin cloud is now mostly large, light
wisps ("Classic + wisps", the default), thick cloud round clouds.

The panel is simpler. The main page has the on/off switch, the Performance
preset and five sliders: wing fade, cloud size, build-up after entering,
spawn distance and fade-out after leaving. Advanced sits next to the presets
and shows every setting in one list, where what you set is your own. The
hotkey Ctrl+Shift+C switches CloudSurf on and off.

Smaller things: smoother fades, a slow spin on the clouds, and two wisp
textures with hard edges fixed.
