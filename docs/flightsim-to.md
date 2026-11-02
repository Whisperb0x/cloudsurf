# flightsim.to page text (1.1)

The whole add-on page, ready to paste. The page's editor drops Markdown list
markers, so lists use plain bullet characters (•), one item per line.

---

**Short description**

Fly through clouds instead of sitting in grey fog. Cloud puffs rush past your windows and wings, following the sim's own weather. Any aircraft, live weather and presets. Free and open.

**Description**

Flying into a cloud in MSFS turns the screen grey, with no sense of speed and nothing streaming past. CloudSurf fixes that. I think this belongs in the sim by default; until it is, here's a free community version.

While you're in a cloud, CloudSurf places soft cloud puffs at fixed spots in the world around and ahead of you. They come at you, sweep over the windscreen and wings, and fall behind. Leave the cloud and they stay where they were, behind you, like the real one.

1.1 is out, built on the comments on 1.0 (thank you). The two things people wrote about most, puffs appearing out of nowhere and dark clouds, are what it is about. Changelog at the bottom.

Replies may take a while. Issues and pull requests on GitHub are the best way to help.

**Features**

• Sense of speed in IMC: cloud puffs at fixed world positions, coming at you and passing by.
• In and out of cloud at once: the clouds are around you the moment you are in one and build up over the first few hundred metres; when you leave, nothing new is made and the clouds behind you stay.
• Wing fade with depth: a stream of small flakes over the wings plus a second layer of big flakes above and below the aircraft, as dense as the cloud you're in.
• Follows the sim's weather: density, brightness and number of puffs follow the sim's own cloud density; thin cloud gets light wisps, thick cloud dense round clouds; clouds are darker in thick decks and lighter near the top.
• Stays inside the deck: clouds keep to the cloud layer of the current weather.
• Nothing near the ground: no clouds within 200 ft, so nothing on the take-off run in airport fog.
• Simple panel: on/off, a Performance preset (Auto keeps your FPS within about 10 % of your FPS before the cloud; Performance, Balanced and Quality use a fixed number of clouds) and five sliders: wing fade, cloud size, build-up after entering, spawn distance, fade-out after leaving.
• Advanced, next to the presets: every setting, what is automatic, a Calibrate mode to tune the look per cloud density, and debug tools.
• Hotkey Ctrl+Shift+C switches CloudSurf on and off.
• Works in live weather and weather presets, with any aircraft. It only reads the sim's weather, so other weather add-ons work alongside it.
• No external app: a WASM module plus a toolbar panel. All settings are L:CLOUDSURF_* variables, so MobiFlight, SPAD.neXt and the like can drive them.
• Aircraft lights (beta): strobes, beacon, nav and landing lights making nearby cloud glow at night. Doesn't really work yet (see Known limitations).

**Installation**

• Copy the whisperb0x-cloudsurf folder into your Community folder.
• Start the sim and open CloudSurf from the toolbar. If the button doesn't show, enable it in the toolbar settings (the pencil icon).
• Open the panel once after loading a flight. It reads the cloud layers of the active weather, so CloudSurf knows where decks start and end. They stay known after you close it.
• Using another in-cloud or wing-fade add-on? Switch that effect off there, or you get both.

**Known limitations**

• MSFS 2024 only. The module uses the 2024 WASM API and does not load in 2020.
• The sim only reports the cloud you're in, not what's ahead. CloudSurf places clouds ahead of you as you enter, and before a deck you are about to climb or descend into; in scattered cloud that can show. Turn off Clouds before a deck under Advanced to get clouds only once you are in one.
• Without opening the panel once per flight, CloudSurf doesn't know the deck top and base. It still works, but puffs aren't kept inside the deck.
• The aircraft lights are beta. MSFS doesn't light particles with aircraft lights, and the workaround isn't there yet.
• Tested on a high-end system (Ryzen 7 7800X3D, RTX 5090). Auto mode and the sliders keep the cost in check; reports from other setups are welcome: FPS before and in cloud, and which preset.
• Specific weather situations (odd layer setups, storms, very low or very high decks) may still look funky. That's one reason it's open.

**Questions people ask**

Clouds appear out of thin air in front of me. CloudSurf only knows the cloud you are in, so it places clouds ahead as you enter, and before a deck you are about to enter. Under Advanced, turn off Clouds before a deck, or lower Spawn distance. A version that reads the sim's own cloud volume ahead of you is in the works.

Clouds on the runway. Fixed in 1.1: nothing within 200 ft of the ground.

Does it work with GFX? Yes. Turn off GFX's wing fade (you would get both), keep the rest.

With AtmosphereMod, REX, ActiveSky? They change the sim's weather and clouds; CloudSurf reads the result, so they go together. If the clouds look off, try CloudSurf alone once to tell which is which.

MSFS 2020? No, sorry. The module does not load in 2020.

The toolbar button is missing. Enable it in the toolbar settings (the pencil icon).

The clouds are dark or olive. Up to 1.0 they were drawn in the sim's default smoke material, which has dark, brownish colour multipliers. 1.1 uses its own white material. Too light? Brightness under Advanced.

Wing fade does nothing. It follows the clouds around you: thin cloud gives little. Raise Intensity (Advanced) or the Wing fade slider; in thick cloud it should be clearly there.

Smoke trails behind AI aircraft on landing? Not CloudSurf: it only spawns its own effects around your aircraft, never on others.

**Free and open**

The source code, effects and panel are on GitHub: Whisperb0x/cloudsurf. The license is CC BY-NC-SA 4.0: free to use, share and adapt, with credit, not for commercial use, and under the same license. Issues, ideas, pull requests and better textures are very welcome.

**Credits**

CloudSurf by whisperb0x and contributors. Cloud wisp textures (the wisps style) converted from 2D Cloud Textures Pack by VFX Assets (free, own terms).

**Changelog**

1.1

Thanks for all the reports. This update is mostly about the two things people wrote about most: clouds that seemed to appear out of nowhere, and clouds that came out dark.

• In and out of cloud at once: clouds around you the moment you are in one, building up over the first few hundred metres; when you leave, nothing new is made, the clouds behind you stay, only the ones still ahead in clear air fade. No more plume behind the aircraft from outside.
• Wing fade with depth: a thicker stream of small flakes plus a second layer of big flakes above and below the aircraft, going back more slowly.
• Wing fade brightness setting (0.8x by default): flakes close to the camera came out lighter than the clouds.
• White cloud material: no more dark or olive clouds (the sim's default smoke material tinted them). Too light? Brightness under Advanced.
• No clouds within 200 ft of the ground: nothing on the take-off run in airport fog.
• Clouds before a deck can be switched off (Advanced): in scattered cloud you then only get clouds once you are in one.
• Cloud phases: spawn distance far ahead in thin cloud, half of that in thick cloud, every cloud fading in by distance so none pops.
• Thin cloud is mostly large, light wisps now (Classic + wisps, the default); thick cloud round clouds.
• Simpler panel: on/off, the Performance preset and five sliders (wing fade, cloud size, build-up after entering, spawn distance, fade-out after leaving). Advanced sits next to the presets and shows every setting.
• Hotkey Ctrl+Shift+C switches CloudSurf on and off.
• Smoother fades, a slow spin on the clouds, two wisp textures with hard edges fixed.

1.0.0

First public release.
