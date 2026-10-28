"""Read the calibration points the panel sent to the module (L:CLOUDSURF_CAL*)
from the running sim, and print them as JSON.

  python tools/read_calibration.py [--dll PATH]

Read-only.
"""
import argparse, json, os, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from live_monitor import SimConnect, find_dll

KEYS = ["DENS", "SIZE", "COUNT", "WING", "BRIGHT", "SPACING", "LEAD",
        "CLASSIC", "WISPS", "LATERAL", "VERTICAL", "GLOW"]


def read(sc, names):
    for i, n in enumerate(names):
        sc.watch(1000 + len(read.seen) + i, f"L:CLOUDSURF_{n}", "number")
    ids = {1000 + len(read.seen) + i: n for i, n in enumerate(names)}
    read.seen += names
    got, t0 = {}, time.time()
    while len(got) < len(names) and time.time() - t0 < 5:
        for k, v in sc.poll().items():
            if k in ids:
                got[ids[k]] = v
        time.sleep(0.01)
    return got
read.seen = []


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--dll")
    sc = SimConnect(find_dll(ap.parse_args().dll), "CloudSurf Calibration Reader")
    n = int(read(sc, ["CAL_N"]).get("CAL_N", 0))
    points = []
    for i in range(1, n + 1):
        names = [f"CAL{i}_PCT"] + [f"CAL{i}_{k}" for k in KEYS]
        v = read(sc, names)
        points.append({"pct": v.get(f"CAL{i}_PCT"), **{k: v.get(f"CAL{i}_{k}") for k in KEYS}})
    sc.close()
    print(json.dumps(points, indent=1))


if __name__ == "__main__":
    main()
