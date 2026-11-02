# flightsim.to page text

Ready to paste into the add-on page (Description, FAQ, Changelog). Keep the
Description that is there; add the FAQ after "Known limitations" and the
changelog entry at the end. The page's editor drops list markers, so every
item is a paragraph of its own.

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

Thanks for all the reports. This update is mostly about the two things people wrote about most: clouds that seemed to appear out of nowhere, and clouds that came out dark.

In and out of cloud at once. The moment you are in a cloud, the clouds are around you and ahead of you, building up over the first few hundred metres. When you leave, nothing new is made; the clouds you flew through stay behind you, and only the ones still ahead in clear air fade. From outside, the effect no longer trails the aircraft like a plume.

Wing fade with depth. The small flakes stream through a thicker tube instead of a flat sheet, and a second layer of big flakes above and below the aircraft goes back more slowly. It has its own brightness setting (0.8x by default), because flakes close to the camera come out lighter than the clouds.

White cloud material. Up to 1.0 the clouds used the sim's default smoke material, whose colour multipliers are dark and brownish: that is where the dark and olive clouds came from. Too light now? Brightness under Advanced brings them down.

No clouds near the ground. Nothing within 200 ft: fog at an airport counts as cloud in the sim, which put clouds on the take-off run.

Clouds before a deck can be switched off (Advanced), so in scattered cloud you only get clouds once you are in one.

Cloud phases. The spawn distance follows the cloud: far ahead in thin cloud, half of that in thick cloud, every cloud fading in by distance so none pops. Thin cloud is now mostly large, light wisps (Classic + wisps, the default), thick cloud round clouds.

A simpler panel. On/off, the Performance preset and five sliders: wing fade, cloud size, build-up after entering, spawn distance and fade-out after leaving. Advanced sits next to the presets and shows every setting in one list.

Hotkey Ctrl+Shift+C switches CloudSurf on and off.

Smaller things: smoother fades, a slow spin on the clouds, and two wisp textures with hard edges fixed.
