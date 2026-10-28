// CloudSurf controls + debugger for the CloudSurf toolbar panel.
// Talks to the CloudSurf WASM module only through L:CLOUDSURF_* vars.
(function () {
	// Must match kConfigVars in CloudSurf.cpp (same defaults). MAIN sliders
	// show on the main page; the rest are the fixed settings under "Advanced".
	// Everything else follows the sim on its own (see the Automatic box).
	const MAIN = ["MAX_ALIVE", "MULT", "SIZE", "BRIGHT", "WING", "GLOW"];
	const SLIDERS = [
		["MAX_ALIVE",    "Clouds around you (Auto: at most)", 10, 128, 1, 128, ""],
		["MULT",         "Thickness",             0,  2,   0.05, 2.0,  "x"],
		["SIZE",         "Size",                  0.5, 2.5, 0.05, 1.65, "x"],
		["BRIGHT",       "Brightness (match the sim's cloud)", 0.2, 3, 0.05, 1.0, "x"],
		["WING",         "Wing fade", 0, 2, 0.05, 1.0, "x"],
		["GLOW",         "Glow from aircraft lights", 0, 3, 0.05, 0.85, "x"],
		["LEAD_MAX",     "New clouds appear ahead at (closer near edges, at least 500 m)", 500, 2500, 10, 1200, "m"],
		["LATERAL",      "Sideways spread",       20, 200, 1,    120,  "m"],
		["VERTICAL",     "Vertical spread (less when climbing steeply)", 0, 150, 1, 50, "m"],
		["CLUSTER",      "Clouds per step",       1,  16,  1,    8,    ""],
		["FULL_PCT",     "Sim density for full thickness", 3, 40, 1, 10, "%"],
		["TEST_DENS",    "Test mode density",     0,  1,   0.05, 1.0,  ""],
		["BEAM_FWD",     "Beam start ahead",      -10, 60, 1,   10,   "m"],
		["BEAM_UP",      "Beam start height",     -10, 10, 0.5, -1,   "m"],
		["BEAM_HDG",     "Beam direction (heading)", -180, 180, 1, 1, "deg"],
		["BEAM_PITCH",   "Beam direction (pitch)", -90, 90, 1,  0,    "deg"],
	];
	// Performance presets: how many clouds there are at once and per step.
	// Auto lets the module pick the number (up to MAX_ALIVE) so the frame rate
	// in cloud stays within 10 % of the one before it. Moving one of these
	// sliders yourself makes the preset "custom" (fixed, Auto off).
	const PRESETS = {
		auto:        { AUTO: 1, MAX_ALIVE: 128, CLUSTER: 8 },
		performance: { AUTO: 0, MAX_ALIVE: 35, CLUSTER: 6 },
		balanced:    { AUTO: 0, MAX_ALIVE: 60, CLUSTER: 8 },
		quality:     { AUTO: 0, MAX_ALIVE: 100, CLUSTER: 10 },
	};
	const DEFAULT_PRESET = "auto";
	// Settings without a control of their own (set by the presets).
	const HIDDEN = [["AUTO", 1]];
	// Effect labels, filled in by build.py in the same order as kEffects.
	// L:CLOUDSURF_EFFECT is an index into it, or -1 for the mix (style Full).
	const EFFECTS = /*@EFFECTS@*/[];
	const DEFAULT_EFFECT = 0;
	// The custom-texture wisps are experimental: only here, not on the main page.
	const EFFECT_LABELS = { CloudSurf: "Classic", CloudSurfWisps: "Wisps only (experimental)" };
	const effectLabel = i => (i < 0 ? "Classic + wisps (experimental)" : EFFECT_LABELS[EFFECTS[i]] || EFFECTS[i] || "?");
	const TOGGLES = [
		["ENABLE",   "csEnable",  1],
		["TEST",     "csTest",    0],
		["BEAM",     "csBeam",    1],
		["LIT",      "csLit",     1],
	];
	const STORE_KEY = "CloudSurfSettings3";  // v3: 8 per step, wing clouds, wisps experimental

	const $ = id => document.getElementById(id);
	const getL = name => {
		try { return SimVar.GetSimVarValue("L:CLOUDSURF_" + name, "number"); } catch (e) { return NaN; }
	};
	const setL = (name, v) => {
		try { SimVar.SetSimVarValue("L:CLOUDSURF_" + name, "number", v); } catch (e) {}
	};
	const getA = (name, unit) => {
		try { return SimVar.GetSimVarValue(name, unit); } catch (e) { return NaN; }
	};

	// The sim's own storage (dataStorage.js) survives a restart; localStorage
	// in the panel did not, so it is only a fallback.
	function loadSettings() {
		const sources = [
			() => typeof GetStoredData === "function" ? GetStoredData(STORE_KEY) : null,
			() => localStorage.getItem(STORE_KEY),
		];
		for (const get of sources) {
			try {
				const raw = get();
				if (raw) return JSON.parse(raw) || {};
			} catch (e) {}
		}
		return {};
	}
	let settings = loadSettings();
	// 800 m was the old default distance; it is 1200 m now.
	if (settings.LEAD_MAX === 800) delete settings.LEAD_MAX;
	// 25 % was the old density for full thickness; real decks rarely go over ~10 %.
	if (settings.FULL_PCT === 25) delete settings.FULL_PCT;
	// v4 defaults: lit by the sim's light, 120 x 50 m spread, dense and many.
	if (!settings.__v4) {
		["LIT", "LATERAL", "VERTICAL", "MULT", "MAX_ALIVE", "CLUSTER", "PRESET", "BRIGHT"].forEach(k => delete settings[k]);
		settings.__v4 = true;
	}
	// v5: Auto FPS is the default.
	if (!settings.__v5) {
		["AUTO", "MAX_ALIVE", "CLUSTER", "PRESET"].forEach(k => delete settings[k]);
		settings.__v5 = true;
	}
	const save = () => {
		const raw = JSON.stringify(settings);
		try { if (typeof SetStoredData === "function") SetStoredData(STORE_KEY, raw); } catch (e) {}
		try { localStorage.setItem(STORE_KEY, raw); } catch (e) {}
	};

	function defaultOf(key) {
		if (key === "EFFECT") return DEFAULT_EFFECT;
		if (key === "PRESET") return DEFAULT_PRESET;
		const s = SLIDERS.find(x => x[0] === key);
		if (s) return s[5];
		const t = TOGGLES.find(x => x[0] === key);
		if (t) return t[2];
		const h = HIDDEN.find(x => x[0] === key);
		return h ? h[1] : 0;
	}
	const valueOf = key => (key in settings ? settings[key] : defaultOf(key));

	function fmt(v, step) {
		const decimals = step < 0.1 ? 2 : step < 1 ? 1 : 0;
		return Number(v).toFixed(decimals);
	}

	function showSlider(key) {
		const s = SLIDERS.find(x => x[0] === key);
		$("cs_" + key).value = valueOf(key);
		$("csVal_" + key).textContent = fmt(valueOf(key), s[4]) + s[6];
	}

	function buildSliders() {
		SLIDERS.forEach(([key, label, min, max, step, , unit]) => {
			const box = $(MAIN.includes(key) ? "csMain" : "csSliders");
			const row = document.createElement("div");
			row.className = "ctrl-master-intensity cs-row";
			row.innerHTML =
				`<p>${label} <span id="csVal_${key}" class="ctrl-intensity-value"></span></p>` +
				`<span class="ctrl-slider-label">${min}</span>` +
				`<div class="ctrl-slider-wrapper"><input type="range" id="cs_${key}" min="${min}" max="${max}" step="${step}" /></div>` +
				`<span class="ctrl-slider-label">${max}</span>`;
			box.appendChild(row);
			showSlider(key);
			row.querySelector("input").addEventListener("input", e => {
				const v = parseFloat(e.target.value);
				settings[key] = v;
				$("csVal_" + key).textContent = fmt(v, step) + unit;
				setL(key, v);
				if (Object.keys(PRESETS.balanced).includes(key)) {
					settings.PRESET = "custom";
					settings.AUTO = 0;
					setL("AUTO", 0);
				}
				save();
				showChoices();
			});
		});
	}

	function bindToggles() {
		TOGGLES.forEach(([key, id]) => {
			const el = $(id);
			if (!el) return;
			el.checked = valueOf(key) > 0.5;
			el.addEventListener("change", () => {
				settings[key] = el.checked ? 1 : 0;
				setL(key, settings[key]);
				if (key !== "TEST") save();  // test mode is never remembered
			});
		});
	}

	// --- style and performance buttons --------------------------------------

	const setOn = (el, on) => (on ? el.classList.add("cs-on") : el.classList.remove("cs-on"));

	function showChoices() {
		const effect = valueOf("EFFECT"), preset = valueOf("PRESET");
		document.querySelectorAll("#csPreset .cs-seg-btn").forEach(b =>
			setOn(b, b.getAttribute("data-preset") === preset));
		$("csEffectName").textContent = `${effect + 2}/${EFFECTS.length + 1}  ${effectLabel(effect)}`;
	}

	function setEffect(i) {
		settings.EFFECT = i;
		setL("EFFECT", i);
		save();
		showChoices();
		log("effect: " + effectLabel(i));
	}

	function stepEffect(delta) {
		const n = EFFECTS.length + 1;  // the mix first
		setEffect((valueOf("EFFECT") + 1 + delta + n) % n - 1);
	}

	function setPreset(name) {
		settings.PRESET = name;
		Object.keys(PRESETS[name]).forEach(key => {
			settings[key] = PRESETS[name][key];
			setL(key, settings[key]);
			if (SLIDERS.some(s => s[0] === key)) showSlider(key);
		});
		save();
		showChoices();
		log("performance: " + name);
	}

	// Push stored settings to the module. INIT=1 stops the module from
	// overwriting them with its own defaults.
	function applyAll() {
		setL("EFFECT", valueOf("EFFECT"));
		SLIDERS.forEach(([key]) => setL(key, valueOf(key)));
		TOGGLES.forEach(([key, id]) => setL(key, $(id) && $(id).checked ? 1 : 0));
		HIDDEN.forEach(([key]) => setL(key, valueOf(key)));
		setL("INIT", 1);
	}

	function resetAll() {
		settings = {};
		save();
		SLIDERS.forEach(([key]) => showSlider(key));
		TOGGLES.forEach(([key, id, def]) => { if ($(id)) $(id).checked = def > 0.5; });
		showChoices();
		applyAll();
		log("settings reset to defaults");
	}

	// --- cloud layers -------------------------------------------------------
	// The sim's own weather panel API (JS_LISTENER_WEATHER; internal, not an
	// official SDK API) gives the active weather's cloud layers. They go to the
	// module as L:CLOUDSURF_LAYERS (count, 0 = unknown), LAYER<n>_BOT/_TOP
	// (feet), _COV (0..1), _DENS and LAYERS_AGL. Without it CloudSurf still
	// works, only without knowing the layers.

	let layers = [], layersAgl = false;

	function coverWord(c) {
		return c < 0.15 ? "few" : c < 0.5 ? "scattered" : c < 0.85 ? "broken" : "overcast";
	}
	const feet = v => String(Math.round(v / 100) * 100).replace(/\B(?=(\d{3})+(?!\d))/g, ",");
	function layersText() {
		if (!layers.length) return "";
		return layers.map(l => `${feet(l.bot)}-${feet(l.top)} ft ${coverWord(l.cov)}`).join("  ·  ") +
		       (layersAgl ? " (above ground)" : "");
	}

	function writeLayers(data) {
		const value = (l, key) => (l && l[key] ? Number(l[key].value) || 0 : 0);
		layers = ((data && data.tCloudLayers) || [])
			.map(l => ({ bot: value(l, "dvAltitudeBot"), top: value(l, "dvAltitudeTop"),
			             cov: value(l, "dvCoverageRatio") / 100, dens: value(l, "dvDensityMultiplier") }))
			.filter(l => l.top > l.bot && l.cov > 0);
		layersAgl = !!(data && data.oSettings && data.oSettings.bIsAltitudeAMGL);
		layers.forEach((l, i) => {
			setL(`LAYER${i + 1}_BOT`, l.bot);
			setL(`LAYER${i + 1}_TOP`, l.top);
			setL(`LAYER${i + 1}_COV`, l.cov);
			setL(`LAYER${i + 1}_DENS`, l.dens);
		});
		setL("LAYERS_AGL", layersAgl ? 1 : 0);
		setL("LAYERS", layers.length);
	}

	function startLayers() {
		if (typeof RegisterViewListener !== "function") return;
		try {
			let listener = null;
			const ask = () => { try { if (listener) listener.trigger("ASK_UPDATE_PRESET"); } catch (e) {} };
			listener = RegisterViewListener("JS_LISTENER_WEATHER", ask);
			listener.on("UpdatePreset", writeLayers);
			setInterval(ask, 10000);  // the weather can change in flight
		} catch (e) {
			log("cloud layers not available");
		}
	}

	// --- status and debugger ------------------------------------------------

	const logLines = [];
	function log(msg) {
		const stamp = new Date().toTimeString().slice(0, 8);
		logLines.unshift(`${stamp}  ${msg}`);
		logLines.length = Math.min(logLines.length, 10);
		const el = $("csLog");
		if (el) el.textContent = logLines.join("\n");
	}

	let last = { spawns: null, fails: null, state: null, beat: null, beatAt: 0 };

	function setText(id, text, cls) {
		const el = $(id);
		if (!el) return;
		el.textContent = text;
		el.className = "cs-val" + (cls ? " " + cls : "");
	}

	function cloudWord(pct) {
		return pct < 5 ? "thin" : pct < 20 ? "medium" : "thick";
	}

	function showStatus(running, inCloud, cloudPct, active, fade) {
		let state, main, sub;
		if (!running) {
			state = "off"; main = last.beat > 0 ? "Paused" : "Waiting for the sim";
			sub = last.beat > 0 ? "CloudSurf resumes when the sim runs" : "The CloudSurf module is not loaded yet";
		} else if (!$("csEnable").checked) {
			state = "off"; main = "Off"; sub = "Switch on \"Fly through clouds\"";
		} else if (inCloud > 0.5) {
			state = "in"; main = `In ${cloudWord(cloudPct)} cloud`;
			sub = `${cloudPct.toFixed(0)} % density  ·  ${active} clouds around you`;
		} else if (getL("EARLY") > 0.5) {
			state = "in"; main = "Entering a cloud layer";
			sub = `Clouds placed ahead  ·  ${layersText()}`;
		} else if (fade > 0.01 && active > 0) {
			state = "fade"; main = "Leaving cloud"; sub = "The last clouds are passing";
		} else if ($("csTest").checked) {
			state = "in"; main = "Test mode"; sub = `${active} test clouds  ·  also in clear sky`;
		} else {
			state = "clear"; main = "Clear air";
			sub = layers.length ? "Cloud layers: " + layersText() : "Clouds start as soon as you fly into one";
		}
		$("csStatus").className = "cs-status cs-" + state;
		$("csStatusMain").textContent = main;
		$("csStatusSub").textContent = sub;
	}

	function tick() {
		const beat = getL("HEARTBEAT");
		const now = Date.now();
		if (beat !== last.beat) { last.beat = beat; last.beatAt = now; }
		const running = last.beat > 0 && now - last.beatAt < 2000;
		setText("csRunning", running ? "running" : (last.beat > 0 ? "paused / not updating" : "not loaded"),
		        running ? "cs-ok" : "cs-bad");

		const active = getL("ACTIVE"), spawns = getL("SPAWNS"), fails = getL("FAILS");
		const state = getL("STATE"), dens = getL("DENS"), lead = getL("LAST_LEAD"), fade = getL("FADE");
		const inCloud = getA("A:AMBIENT IN CLOUD", "bool");
		const cloudPct = getA("A:ENV CLOUD DENSITY", "percent");
		const camera = getA("A:CAMERA STATE", "enum");
		const gs = getA("A:GROUND VELOCITY", "knots");

		showStatus(running, inCloud, isNaN(cloudPct) ? 0 : cloudPct, isNaN(active) ? 0 : active, fade);
		setText("csState", state > 0.5 ? "spawning" : "idle", state > 0.5 ? "cs-ok" : "");
		setText("csInCloud", inCloud > 0.5 ? "yes" : "no", inCloud > 0.5 ? "cs-ok" : "");
		setText("csCloudPct", isNaN(cloudPct) ? "-" : cloudPct.toFixed(1) + " %");
		setText("csDens", isNaN(dens) ? "-" : dens.toFixed(2));
		setText("csFade", isNaN(fade) ? "-" : fade.toFixed(2));
		const tone = getL("TONE"), sun = getL("SUN"), vis = getL("VIS");
		setText("csTone", isNaN(tone) ? "-" : `${tone.toFixed(2)}  (sun ${isNaN(sun) ? "-" : sun.toFixed(0)}°)`);
		setText("csVis", vis > 0 ? `${vis.toFixed(0)} m` : "-");
		const fps = getL("FPS"), fpsBase = getL("FPS_BASE"), cap = getL("CAP");
		setText("csAutoFps", valueOf("AUTO") < 0.5 ? "off (fixed number)" :
		        fpsBase > 0 ? `${fps.toFixed(0)} fps (before cloud ${fpsBase.toFixed(0)}), up to ${cap} clouds`
		                    : `measuring, up to ${cap} clouds`);
		const leadNow = getL("LEAD_NOW");
		setText("csLeadNow", leadNow > 0 ? `${leadNow.toFixed(0)} m` : "-");
		const deckTop = getL("DECK_TOP"), deckBot = getL("DECK_BOT");
		setText("csDeck", deckTop > 0 ? `${feet(deckBot)}-${feet(deckTop)} ft` : "-");
		const layerNow = getL("LAYER");
		setText("csLayers", layers.length ? `${layers.length}, in #${layerNow || "-"}` : "unknown");
		const change = getL("CHANGE");
		setText("csChange", isNaN(change) || change === 0 ? "steady" :
		        (change > 0 ? "thicker " : "thinner ") + Math.abs(change).toFixed(2));
		setText("csActive", isNaN(active) ? "-" : String(active));
		setText("csSpawns", isNaN(spawns) ? "-" : String(spawns));
		setText("csFails", isNaN(fails) ? "-" : String(fails), fails > 0 ? "cs-bad" : "");
		setText("csCamera", camera === 2 ? "cockpit" : isNaN(camera) ? "-" : "external (" + camera + ")");
		setText("csSpeed", isNaN(gs) ? "-" : gs.toFixed(0) + " kt");

		if (last.spawns !== null && spawns > last.spawns)
			log(`spawned ${spawns - last.spawns} cloud(s), last at ${lead.toFixed(0)} m ahead`);
		if (last.fails !== null && fails > last.fails)
			log(`spawn FAILED (${fails} total) - try a smaller nearest distance`);
		if (last.state !== null && state !== last.state)
			log(state > 0.5 ? "cloud entered, spawning" : "left cloud, no new clouds");
		last.spawns = spawns; last.fails = fails; last.state = state;
	}

	function init() {
		if (!$("csSliders")) return;
		buildSliders();
		bindToggles();
		showChoices();
		applyAll();
		startLayers();
		$("csShowDebug").addEventListener("change", () => {
			$("csDebug").style.display = $("csShowDebug").checked ? "block" : "none";
		});
		document.querySelectorAll("#csPreset .cs-seg-btn").forEach(b =>
			b.addEventListener("click", () => setPreset(b.getAttribute("data-preset"))));
		$("csEffectPrev").addEventListener("click", () => stepEffect(-1));
		$("csEffectNext").addEventListener("click", () => stepEffect(1));
		$("csSpawnNow").addEventListener("click", () => { setL("SPAWN_NOW", 1); log("spawn requested"); });
		$("csClear").addEventListener("click", () => { setL("CLEAR", 1); log("all clouds cleared"); });
		$("csReset").addEventListener("click", resetAll);
		// The module may load after the panel; re-apply once it is alive.
		let applied = false;
		setInterval(() => {
			tick();
			if (!applied && last.beat > 0) { applyAll(); applied = true; log("module found, settings applied"); }
		}, 250);
		log("panel loaded");
	}

	if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", init);
	else init();
})();
