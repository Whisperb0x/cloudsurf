"""Live monitor for CloudSurf: logs the module's L:vars and the relevant sim
variables every frame via SimConnect. Based on the A350 wingflex monitor.

  python tools/live_monitor.py            wait for the sim, log to logs/live_<time>.csv, Ctrl+C to stop
  python tools/live_monitor.py --dll PATH  use a specific SimConnect.dll

Read-only: it never writes anything to the sim.
"""
import argparse, csv, ctypes, os, struct, sys, time
from ctypes import wintypes

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DLL_CANDIDATES = [r"C:\MSFS 2024 SDK\SimConnect SDK\lib\SimConnect.dll",
                  r"C:\MSFS SDK\SimConnect SDK\lib\SimConnect.dll"]

SIM_VARS = [  # (column, simvar, units)
    ("abs_time", "ABSOLUTE TIME", "seconds"),
    ("on_ground", "SIM ON GROUND", "bool"),
    ("gs_kt", "GROUND VELOCITY", "knots"),
    ("alt_ft", "PLANE ALTITUDE", "feet"),
    ("in_cloud", "AMBIENT IN CLOUD", "bool"),
    ("cloud_pct", "ENV CLOUD DENSITY", "percent"),
    ("vis_m", "AMBIENT VISIBILITY", "meters"),
    ("camera", "CAMERA STATE", "enum"),
    ("strobe", "LIGHT STROBE", "bool"),
    ("beacon", "LIGHT BEACON", "bool"),
    ("landing", "LIGHT LANDING", "bool"),
]
MOD_VARS = ["HEARTBEAT", "STATE", "ACTIVE", "SPAWNS", "FAILS", "LAST_LEAD", "DENS", "FADE",
            "ENABLE", "TEST", "ALT_FEET", "LEAD_MIN", "LEAD_MAX", "SPACING", "FULL_PCT", "MAX_ALIVE", "MULT",
            "EFFECT", "DENS_VAR", "CLUSTER", "ALT_OFFSET", "VERTICAL", "HOLE", "LATERAL"]

FLOAT64 = 4
PERIOD_VISUAL_FRAME = 2
RECV_EXCEPTION, RECV_QUIT, RECV_SIMOBJECT_DATA = 1, 3, 8


class SimConnect:
    def __init__(self, dll_path, name="CloudSurf Monitor"):
        d = ctypes.WinDLL(dll_path); self.d = d
        H = wintypes.HANDLE; D = wintypes.DWORD
        d.SimConnect_Open.argtypes = [ctypes.POINTER(H), ctypes.c_char_p, wintypes.HWND, D, H, D]
        d.SimConnect_Close.argtypes = [H]
        d.SimConnect_AddToDataDefinition.argtypes = [H, D, ctypes.c_char_p, ctypes.c_char_p, D, ctypes.c_float, D]
        d.SimConnect_RequestDataOnSimObject.argtypes = [H, D, D, D, D, D, D, D, D]
        d.SimConnect_GetNextDispatch.argtypes = [H, ctypes.POINTER(ctypes.c_void_p), ctypes.POINTER(D)]
        self.h = H()
        hr = d.SimConnect_Open(ctypes.byref(self.h), name.encode(), None, 0, None, 0)
        if hr != 0:
            raise ConnectionError(f"SimConnect_Open failed (0x{hr & 0xFFFFFFFF:08X})")
        self.quit = False; self.exceptions = []

    def watch(self, define_id, name, units):
        """One definition and one per-frame request per variable, so a rejected name can't shift the others."""
        if self.d.SimConnect_AddToDataDefinition(self.h, define_id, name.encode(), units.encode(), FLOAT64, 0.0, 0xFFFFFFFF):
            raise RuntimeError(f"AddToDataDefinition failed: {name}")
        if self.d.SimConnect_RequestDataOnSimObject(self.h, define_id, define_id, 0, PERIOD_VISUAL_FRAME, 0, 0, 0, 0):
            raise RuntimeError(f"RequestDataOnSimObject failed: {name}")

    def poll(self):
        out = {}; p = ctypes.c_void_p(); n = wintypes.DWORD()
        while self.h and self.d.SimConnect_GetNextDispatch(self.h, ctypes.byref(p), ctypes.byref(n)) == 0:
            raw = ctypes.string_at(p, n.value)
            rid = struct.unpack_from("<I", raw, 8)[0]
            if rid == RECV_SIMOBJECT_DATA and len(raw) >= 48:
                out[struct.unpack_from("<I", raw, 12)[0]] = struct.unpack_from("<d", raw, 40)[0]
            elif rid == RECV_EXCEPTION:
                self.exceptions.append(struct.unpack_from("<III", raw, 12))
            elif rid == RECV_QUIT:
                self.quit = True
        return out

    def close(self):
        if self.h:
            self.d.SimConnect_Close(self.h); self.h = None


def find_dll(arg):
    for p in ([arg] if arg else []) + [os.environ.get("SIMCONNECT_DLL", "")] + DLL_CANDIDATES:
        if p and os.path.isfile(p):
            return p
    sys.exit("SimConnect.dll not found; pass --dll")


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--dll"); ap.add_argument("--status-every", type=float, default=5.0)
    a = ap.parse_args()
    dll = find_dll(a.dll)
    columns = [c for c, _, _ in SIM_VARS] + MOD_VARS
    watches = [(c, n, u) for c, n, u in SIM_VARS] + [(v, f"L:CLOUDSURF_{v}", "number") for v in MOD_VARS]

    while True:
        try:
            sc = SimConnect(dll); break
        except ConnectionError:
            print("Waiting for MSFS...", flush=True); time.sleep(5)
    for i, (_, name, units) in enumerate(watches):
        sc.watch(100 + i, name, units)
    os.makedirs(os.path.join(HERE, "logs"), exist_ok=True)
    path = os.path.join(HERE, "logs", time.strftime("live_%Y%m%d_%H%M%S.csv"))
    f = open(path, "w", newline=""); w = csv.writer(f); w.writerow(["wall"] + columns)
    print(f"Connected. Logging to {path}", flush=True)

    state = {c: float("nan") for c in columns}; last_t = None; last_status = 0.0; rows = 0; t0 = time.time()
    last_beat = (None, time.time())
    try:
        while not sc.quit:
            got = sc.poll()
            for k, val in got.items():
                state[watches[k - 100][0]] = val
            t = state["abs_time"]
            if got and t == t and t != last_t:
                last_t = t
                w.writerow([f"{time.time() - t0:.4f}"] + [f"{state[c]:.6g}" for c in columns]); rows += 1
                if rows % 300 == 0: f.flush()
            if state["HEARTBEAT"] != last_beat[0]:
                last_beat = (state["HEARTBEAT"], time.time())
            if time.time() - last_status > a.status_every:
                last_status = time.time()
                alive = state["HEARTBEAT"] > 0 and time.time() - last_beat[1] < 2
                print(f"[{rows:7d} rows] {'GND' if state['on_ground'] == 1 else 'AIR'} gs={state['gs_kt']:5.1f}kt "
                      f"cloud={'IN ' if state['in_cloud'] == 1 else 'out'} {state['cloud_pct']:5.1f}% "
                      f"dens={state['DENS']:.2f} fx={state['EFFECT']:.0f} alive={state['ACTIVE']:.0f} spawned={state['SPAWNS']:.0f} "
                      f"fails={state['FAILS']:.0f} module={'running' if alive else 'NOT running'}"
                      + (f" | exceptions: {len(sc.exceptions)}" if sc.exceptions else ""), flush=True)
            time.sleep(0.002)
    except KeyboardInterrupt:
        pass
    finally:
        f.flush(); f.close(); sc.close()
        print(f"Stopped. {rows} rows in {path}", flush=True)


if __name__ == "__main__":
    main()
