// CloudPass controls + debugger for the CloudPass toolbar panel.
// Talks to the CloudPass WASM module only through L:CLOUDPASS_* vars.
(function () {
	// Must match kConfigVars in CloudPass.cpp. The first three are the main
	// controls; the rest only show under "Show debug tools".
	const MAIN = ["MULT", "SIZE", "GLOW"];
	const SLIDERS = [
		["MULT",         "Cloud density",         0,  3,   0.05, 1.0,  "x"],
		["SIZE",         "Cloud size",            0.5, 2.5, 0.05, 1.0, "x"],
		["GLOW",         "Glow from aircraft lights", 0, 5, 0.1, 1.0,  "x"],
		["LEAD_MIN",     "Nearest cloud ahead",   20, 1500, 10,  600,  "m"],
		["LEAD_MAX",     "Farthest cloud ahead",  50, 2000, 10,  800,  "m"],
		["SPACING",      "Distance between clouds", 10, 200, 5,  35,   "m"],
		["CLUSTER",      "Clouds per step",       1,  16,  1,    2,    ""],
		["LATERAL",      "Sideways spread",       0,  150, 1,    45,   "m"],
		["VERTICAL",     "Vertical spread",       0,  100, 1,    25,   "m"],
		["HOLE",         "Clear zone around flight path", 0, 40, 1, 8, "m"],
		["BEHIND",       "Remove after passing",  10, 500, 5,    150,  "m"],
		["FULL_PCT",     "Sim density for full effect", 5, 80, 1, 25, "%"],
		["MIN_PCT",      "Minimum sim density",   0,  5,   0.1,  0.3,  "%"],
		["MAX_ALIVE",    "Max clouds alive",      10, 128, 1,    45,   ""],
		["DENS_VAR",     "Density variation",     0,  1,   0.05, 0.6,  ""],
		["COCKPIT_MULT", "Cockpit view density",  0,  1,   0.05, 0.6,  "x"],
		["MIN_SPEED",    "Minimum speed",         0,  150, 5,    25,   "m/s"],
		["TEST_DENS",    "Test density",          0,  1,   0.05, 0.7,  ""],
		["TEST_INTERVAL", "Test spawn interval",  0.2, 5,  0.1,  1.0,  "s"],
		["ALT_OFFSET",   "Altitude offset",       -300, 300, 5,  0,    "m"],
		["NEAR_SHARE",   "Share over the wings",  0,  1,   0.05, 0.4,  ""],
		["NEAR_VERTICAL", "Over-wing height spread", 0, 30, 1,   5,    "m"],
		["BEAM_FWD",     "Beam start ahead",      -10, 60, 1,   15,   "m"],
		["BEAM_UP",      "Beam start height",     -10, 10, 0.5, -1,   "m"],
		["BEAM_HDG",     "Beam direction (heading)", -180, 180, 1, 0, "deg"],
		["BEAM_PITCH",   "Beam direction (pitch)", -90, 90, 1,  0,    "deg"],
	];
	// Effect labels, filled in by build.py in the same order as kEffects.
	const EFFECTS = /*@EFFECTS@*/[];
	const DEFAULT_EFFECT = /*@DEFAULT_EFFECT@*/0;
	const TOGGLES = [
		["ENABLE",   "cpEnable",  1],
		["TEST",     "cpTest",    0],
		["ALT_FEET", "cpAltFeet", 0],
		["BEAM",     "cpBeam",    1],
	];
	const STORE_KEY = "CloudPassSettings4";  // v4: density 0..1 from the sim, max alive

	const $ = id => document.getElementById(id);
	const getL = name => {
		try { return SimVar.GetSimVarValue("L:CLOUDPASS_" + name, "number"); } catch (e) { return NaN; }
	};
	const setL = (name, v) => {
		try { SimVar.SetSimVarValue("L:CLOUDPASS_" + name, "number", v); } catch (e) {}
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

	function buildSliders() {
		SLIDERS.forEach(([key, label, min, max, step, , unit]) => {
			const box = $(MAIN.includes(key) ? "cpMain" : "cpSliders");
			const row = document.createElement("div");
			row.className = "ctrl-master-intensity cp-row";
			row.innerHTML =
				`<p>${label} <span id="cpVal_${key}" class="ctrl-intensity-value"></span></p>` +
				`<span class="ctrl-slider-label">${min}</span>` +
				`<div class="ctrl-slider-wrapper"><input type="range" id="cp_${key}" min="${min}" max="${max}" step="${step}" /></div>` +
				`<span class="ctrl-slider-label">${max}</span>`;
			box.appendChild(row);
			const input = row.querySelector("input");
			const out = row.querySelector(".ctrl-intensity-value");
			input.value = valueOf(key);
			out.textContent = fmt(input.value, step) + unit;
			input.addEventListener("input", () => {
				const v = parseFloat(input.value);
				out.textContent = fmt(v, step) + unit;
				settings[key] = v;
				setL(key, v);
				save();
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

	function showEffect() {
		const i = valueOf("EFFECT");
		$("cpEffectName").textContent = `${i + 1}/${EFFECTS.length}  ${EFFECTS[i] || "?"}`;
	}

	function stepEffect(delta) {
		settings.EFFECT = (valueOf("EFFECT") + delta + EFFECTS.length) % EFFECTS.length;
		setL("EFFECT", settings.EFFECT);
		save();
		showEffect();
		log("effect: " + EFFECTS[settings.EFFECT]);
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
		SLIDERS.forEach(([key, , , , step, def, unit]) => {
			$("cp_" + key).value = def;
			$("cpVal_" + key).textContent = fmt(def, step) + unit;
		});
		TOGGLES.forEach(([key, id, def]) => { if ($(id)) $(id).checked = def > 0.5; });
		showEffect();
		applyAll();
		log("settings reset to defaults");
	}

	// --- debugger -----------------------------------------------------------

	const logLines = [];
	function log(msg) {
		const t = new Date();
		const stamp = t.toTimeString().slice(0, 8);
		logLines.unshift(`${stamp}  ${msg}`);
		logLines.length = Math.min(logLines.length, 10);
		const el = $("cpLog");
		if (el) el.textContent = logLines.join("\n");
	}

	let last = { spawns: null, fails: null, state: null, beat: null, beatAt: 0 };

	function setText(id, text, cls) {
		const el = $(id);
		if (!el) return;
		el.textContent = text;
		el.className = "cp-val" + (cls ? " " + cls : "");
	}

	function tick() {
		const beat = getL("HEARTBEAT");
		const now = Date.now();
		if (beat !== last.beat) { last.beat = beat; last.beatAt = now; }
		const running = last.beat > 0 && now - last.beatAt < 2000;
		setText("cpRunning", running ? "running" : (last.beat > 0 ? "paused / not updating" : "not loaded"),
		        running ? "cp-ok" : "cp-bad");

		const active = getL("ACTIVE"), spawns = getL("SPAWNS"), fails = getL("FAILS");
		const state = getL("STATE"), dens = getL("DENS"), lead = getL("LAST_LEAD");
		const inCloud = getA("A:AMBIENT IN CLOUD", "bool");
		const cloudPct = getA("A:ENV CLOUD DENSITY", "percent");
		const camera = getA("A:CAMERA STATE", "enum");
		const gs = getA("A:GROUND VELOCITY", "knots");

		setText("cpState", state > 0.5 ? "spawning" : "idle", state > 0.5 ? "cp-ok" : "");
		setText("cpInCloud", inCloud > 0.5 ? "yes" : "no", inCloud > 0.5 ? "cp-ok" : "");
		setText("cpCloudPct", isNaN(cloudPct) ? "-" : cloudPct.toFixed(1) + " %");
		setText("cpDens", isNaN(dens) ? "-" : dens.toFixed(2));
		setText("cpActive", isNaN(active) ? "-" : String(active));
		setText("cpSpawns", isNaN(spawns) ? "-" : String(spawns));
		setText("cpFails", isNaN(fails) ? "-" : String(fails), fails > 0 ? "cp-bad" : "");
		setText("cpCamera", camera === 2 ? "cockpit" : isNaN(camera) ? "-" : "external (" + camera + ")");
		setText("cpSpeed", isNaN(gs) ? "-" : gs.toFixed(0) + " kt");

		if (last.spawns !== null && spawns > last.spawns)
			log(`spawned ${spawns - last.spawns} patch(es), last at ${lead.toFixed(0)} m ahead`);
		if (last.fails !== null && fails > last.fails)
			log(`spawn FAILED (${fails} total) - try a smaller nearest distance`);
		if (last.state !== null && state !== last.state)
			log(state > 0.5 ? "cloud entered, spawning" : "left cloud, patches ahead stopped");
		last.spawns = spawns; last.fails = fails; last.state = state;

	}

	function init() {
		if (!$("cpSliders")) return;
		buildSliders();
		bindToggles();
		showEffect();
		applyAll();
		$("cpShowDebug").addEventListener("change", () => {
			$("cpDebug").style.display = $("cpShowDebug").checked ? "block" : "none";
		});
		$("cpEffectPrev").addEventListener("click", () => stepEffect(-1));
		$("cpEffectNext").addEventListener("click", () => stepEffect(1));
		$("cpSpawnNow").addEventListener("click", () => { setL("SPAWN_NOW", 1); log("spawn requested"); });
		$("cpClear").addEventListener("click", () => { setL("CLEAR", 1); log("all patches cleared"); });
		$("cpReset").addEventListener("click", resetAll);
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
