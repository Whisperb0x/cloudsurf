"""Generate a cumulus-puff particle texture as PNG (RGB shading + alpha).

  python tools/make_cloud_texture.py OUT.png [size] [seed]
  python tools/make_cloud_texture.py --preview OUT.png PREVIEW.png [size] [seed]

The shape is a cluster of soft spheres (a big core with smaller lobes on top,
which gives the cauliflower outline), the coordinates are domain-warped with
fractal noise for ragged wisps, and fine noise adds inner texture. Shading is
lighter where the cloud's top edge faces up and slightly grey underneath, so
the flat billboard reads as a volume. Pure Python, no dependencies.
"""
import math, random, struct, sys, zlib


class Noise:
    """2D value noise with smoothstep interpolation. Each instance samples a
    rotated, offset copy of its grid so stacked octaves don't line up into
    visible squares."""

    def __init__(self, cells, rng):
        self.c = cells
        self.g = [[rng.random() for _ in range(cells)] for _ in range(cells)]
        a = rng.uniform(0, math.tau)
        self.cs, self.sn = math.cos(a), math.sin(a)
        self.ox, self.oy = rng.random(), rng.random()

    def at(self, u, v):
        c = self.c
        u, v = u * self.cs - v * self.sn + self.ox, u * self.sn + v * self.cs + self.oy
        x = (u % 1.0) * c
        y = (v % 1.0) * c
        x0 = int(x); y0 = int(y)
        tx = x - x0; ty = y - y0
        tx = tx * tx * (3 - 2 * tx); ty = ty * ty * (3 - 2 * ty)
        x1 = (x0 + 1) % c; y1 = (y0 + 1) % c
        g = self.g
        a = g[y0][x0] + (g[y0][x1] - g[y0][x0]) * tx
        b = g[y1][x0] + (g[y1][x1] - g[y1][x0]) * tx
        return a + (b - a) * ty


def fbm(layers, u, v):
    s = 0.0
    for n, w in layers:
        s += n.at(u, v) * w
    return s


def smoothstep(e0, e1, x):
    t = min(1.0, max(0.0, (x - e0) / (e1 - e0)))
    return t * t * (3 - 2 * t)


def make_blobs(rng):
    """Sphere cluster in -1..1 space (y up = negative y in image)."""
    blobs = [(0.0, 0.12, 0.56)]  # core, slightly low
    for _ in range(rng.randint(5, 7)):  # big lobes, mostly on the upper half
        a = rng.uniform(-math.pi * 0.95, -math.pi * 0.05)
        d = rng.uniform(0.2, 0.42)
        blobs.append((math.cos(a) * d, 0.12 + math.sin(a) * d, rng.uniform(0.2, 0.34)))
    for _ in range(rng.randint(6, 10)):  # small bumps on the top edge: cauliflower
        a = rng.uniform(-math.pi * 0.9, -math.pi * 0.1)
        d = rng.uniform(0.34, 0.52)
        blobs.append((math.cos(a) * d, 0.12 + math.sin(a) * d * rng.uniform(0.7, 1.05), rng.uniform(0.09, 0.17)))
    for _ in range(rng.randint(2, 4)):  # flatter base
        blobs.append((rng.uniform(-0.45, 0.45), rng.uniform(0.28, 0.4), rng.uniform(0.16, 0.26)))
    return blobs


def density(blobs, x, y):
    # soft envelope that ties the lobes together into one puff
    e = 1.0 - (x * x / 0.55 + (y - 0.05) ** 2 / 0.35)
    s = 0.45 * e * e if e > 0 else 0.0
    for bx, by, r in blobs:
        dx = (x - bx) / r
        dy = (y - by) / r
        q = 1.0 - (dx * dx + dy * dy)
        if q > 0:
            s += q * q
    return s


SCALE = 1.3  # >1 = the cloud fills more of the texture


def make(size=1024, seed=7):
    rng = random.Random(seed)
    warp = [(Noise(c, rng), w) for c, w in ((4, 0.55), (8, 0.3), (16, 0.15))]
    warp2 = [(Noise(c, rng), w) for c, w in ((4, 0.55), (8, 0.3), (16, 0.15))]
    detail = [(Noise(c, rng), w) for c, w in ((12, 0.35), (24, 0.25), (48, 0.2), (96, 0.12), (192, 0.08))]
    blobs = make_blobs(rng)
    edge = 0.035  # how far "up" to look for the lit top edge
    rows = []
    for py in range(size):
        v = (py + 0.5) / size
        row = bytearray()
        for px in range(size):
            u = (px + 0.5) / size
            # domain warp: shift the sample point by noise, stronger near edges
            wx = (fbm(warp, u, v) - 0.5) * 0.3
            wy = (fbm(warp2, u, v) - 0.5) * 0.3
            x = (u * 2 - 1 + wx) / SCALE
            y = (v * 2 - 1 + wy) / SCALE
            dn = density(blobs, x, y)
            det = fbm(detail, u, v)
            body = dn * (0.45 + 1.1 * det)
            a = smoothstep(0.02, 1.1, body) * 0.9
            # keep the outer square clean
            r = math.sqrt((u * 2 - 1) ** 2 + (v * 2 - 1) ** 2)
            a *= 1.0 - smoothstep(0.82, 0.98, r)
            if a <= 0.002:
                row += b"\xff\xff\xff\x00"
                continue
            # light from above: brighter where there is less cloud just above
            above = density(blobs, x, y - edge / SCALE)
            lit = smoothstep(-0.25, 0.35, dn - above)  # top edges -> 1
            base = smoothstep(-0.6, 0.6, y)  # 0 at top, 1 at bottom
            shade = 0.80 + 0.20 * lit - 0.10 * base + 0.06 * (det - 0.5)
            c = int(max(0.0, min(1.0, shade)) * 255)
            row += bytes((c, c, min(255, c + 4), int(a * 255)))
        rows.append(bytes(row))
    return rows


def write_png(path, rows, size):
    raw = b"".join(b"\x00" + r for r in rows)

    def chunk(tag, data):
        return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)

    png = b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", size, size, 8, 6, 0, 0, 0))
    png += chunk(b"IDAT", zlib.compress(raw, 9)) + chunk(b"IEND", b"")
    open(path, "wb").write(png)


def preview(rows, size, bg=(70, 120, 190)):
    out = []
    for r in rows:
        row = bytearray()
        for i in range(0, len(r), 4):
            a = r[i + 3] / 255
            row += bytes((int(r[i] * a + bg[0] * (1 - a)), int(r[i + 1] * a + bg[1] * (1 - a)),
                          int(r[i + 2] * a + bg[2] * (1 - a)), 255))
        out.append(bytes(row))
    return out


if __name__ == "__main__":
    args = sys.argv[1:]
    prev = None
    if args and args[0] == "--preview":
        prev = args[2]
        args = [args[1]] + args[3:]
    out = args[0]
    size = int(args[1]) if len(args) > 1 else 1024
    seed = int(args[2]) if len(args) > 2 else 7
    rows = make(size, seed)
    write_png(out, rows, size)
    if prev:
        write_png(prev, preview(rows, size), size)
    print(f"wrote {out} ({size}x{size}, seed {seed})")
