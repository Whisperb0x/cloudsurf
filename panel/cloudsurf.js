// CloudSurf controls + debugger for the CloudSurf toolbar panel.
// Talks to the CloudSurf WASM module only through L:CLOUDSURF_* vars.
(function () {
	// Must match kConfigVars in CloudSurf.cpp (same defaults). MAIN sliders
	// show on the main page; the rest only under "Advanced and debug tools".
	const MAIN = ["MAX_ALIVE", "MULT", "SIZE", "GLOW"];
	const SLIDERS = [
		["MAX_ALIVE",    "Clouds around you",     10, 128, 1,    41,   ""],
		["MULT",         "Thickness",             0,  2,   0.05, 1.5,  "x"],
		["SIZE",         "Size",                  0.5, 2.5, 0.05, 1.65, "x"],
		["GLOW",         "Glow from aircraft lights", 0, 3, 0.05, 0.85, "x"],
		["LEAD_MIN",     "Nearest cloud ahead",   20, 1500, 10,  500,  "m"],
		["LEAD_MAX",     "Farthest cloud ahead",  50, 2000, 10,  800,  "m"],
		["ENTRY_NEAR",   "Nearest cloud on entering", 20, 600, 10, 120, "m"],
		["SPACING",      "Minimum distance between clouds", 5, 200, 5, 20, "m"],
		["CLUSTER",      "Clouds per step",       1,  16,  1,    2,    ""],
		["LATERAL",      "Sideways spread",       0,  150, 1,    80,   "m"],
		["VERTICAL",     "Vertical spread",       0,  100, 1,    41,   "m"],
		["HOLE",         "Clear zone around flight path", 0, 40, 1, 0, "m"],
		["BEHIND",       "Remove after passing",  10, 500, 5,    100,  "m"],
		["FULL_PCT",     "Sim density for full effect", 5, 80, 1, 25, "%"],
		["MIN_PCT",      "Minimum sim density",   0,  5,   0.1,  0.3,  "%"],
		["DENS_VAR",     "Density variation",     0,  1,   0.05, 0.25, ""],
		["MIX_LO",       "Full style: only wisps below", 0, 1, 0.05, 0.3, ""],
		["MIX_HI",       "Full style: only big clouds above", 0, 1, 0.05, 0.8, ""],
		["COCKPIT_MULT", "Cockpit view thickness", 0, 1,   0.05, 0.95, "x"],
		["MIN_SPEED",    "Minimum speed",         0,  150, 5,    25,   "m/s"],
		["TEST_DENS",    "Test density",          0,  1,   0.05, 1.0,  ""],
		["TEST_INTERVAL", "Test spawn interval",  0.2, 5,  0.1,  1.0,  "s"],
		["ALT_OFFSET",   "Altitude offset",       -300, 300, 5,  0,    "m"],
		["NEAR_SHARE",   "Share over the wings",  0,  1,   0.05, 0,    ""],
		["NEAR_VERTICAL", "Over-wing height spread", 0, 30, 1,   0,    "m"],
		["BEAM_FWD",     "Beam start ahead",      -10, 60, 1,   10,   "m"],
		["BEAM_UP",      "Beam start height",     -10, 10, 0.5, -1,   "m"],
		["BEAM_HDG",     "Beam direction (heading)", -180, 180, 1, 1, "deg"],
		["BEAM_PITCH",   "Beam direction (pitch)", -90, 90, 1,  0,    "deg"],
	];
	// Performance presets: how many clouds there are at once and per step.
	// Moving one of these sliders yourself makes the preset "custom".
	const PRESETS = {
		performance: { MAX_ALIVE: 25, CLUSTER: 1 },
		balanced:    { MAX_ALIVE: 41, CLUSTER: 2 },
		quality:     { MAX_ALIVE: 80, CLUSTER: 2 },
	};
	const DEFAULT_PRESET = "balanced";
	// Effect labels, filled in by build.py in the same order as kEffects.
	// L:CLOUDSURF_EFFECT is an index into it, or -1 for the mix (style Full).
	const EFFECTS = /*@EFFECTS@*/[];
	const DEFAULT_EFFECT = 0;
	const effectLabel = i => (i < 0 ? "Full (mix)" : EFFECTS[i] || "?");
	const TOGGLES = [
		["ENABLE",   "csEnable",  1],
		["TEST",     "csTest",    0],
		["ALT_FEET", "csAltFeet", 0],
		["BEAM",     "csBeam",    1],
	];
	const STORE_KEY = "CloudSurfSettings2";  // v2: even spacing, new distance defaults

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
		return t ? t[2] : 0;
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
				if (Object.keys(PRESETS.balanced).includes(key)) settings.PRESET = "custom";
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
		document.querySelectorAll("#csStyle .cs-seg-btn").forEach(b =>
			setOn(b, Number(b.getAttribute("data-effect")) === effect));
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
			showSlider(key);
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
		} else if (fade > 0.01 && active > 0) {
			state = "fade"; main = "Leaving cloud"; sub = "The last clouds are passing";
		} else if ($("csTest").checked) {
			state = "in"; main = "Test mode"; sub = `${active} test clouds  ·  also in clear sky`;
		} else {
			state = "clear"; main = "Clear air"; sub = "Clouds start as soon as you fly into one";
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
		$("csShowDebug").addEventListener("change", () => {
			$("csDebug").style.display = $("csShowDebug").checked ? "block" : "none";
		});
		document.querySelectorAll("#csStyle .cs-seg-btn").forEach(b =>
			b.addEventListener("click", () => setEffect(Number(b.getAttribute("data-effect")))));
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
