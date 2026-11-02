"""Generate the soft cloud particle texture (CloudSoft.png): white RGB with a
soft round alpha, its edge eroded a little by fractal noise so the clouds do
not read as discs.

  python tools/make_soft_texture.py OUT.png [size] [seed]

The round clouds and the wing flakes were drawn in the sim's default smoke
material, whose colour multipliers are dark and brownish: in cloud they came
out dark and olive. This texture goes in our own white material
(MaterialLibs/cloudsurf/CloudSoft.material), so the clouds take the colour
CloudSurf gives them. Pure Python, no dependencies.
"""
import math, random, struct, sys, zlib


class Noise:
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
        xi, yi = int(x), int(y)
        fx, fy = x - xi, y - yi
        fx = fx * fx * (3 - 2 * fx)
        fy = fy * fy * (3 - 2 * fy)
        g = self.g
        a = g[yi % c][xi % c] + (g[yi % c][(xi + 1) % c] - g[yi % c][xi % c]) * fx
        b = g[(yi + 1) % c][xi % c] + (g[(yi + 1) % c][(xi + 1) % c] - g[(yi + 1) % c][xi % c]) * fx
        return a + (b - a) * fy


def fractal(noises, u, v):
    s, w, total = 0.0, 1.0, 0.0
    for n in noises:
        s += w * n.at(u, v)
        total += w
        w *= 0.5
        u, v = u * 2.0, v * 2.0
    return s / total


def make(size, seed):
    rng = random.Random(seed)
    edge = [Noise(4, rng), Noise(8, rng), Noise(16, rng), Noise(32, rng)]
    inner = [Noise(6, rng), Noise(12, rng), Noise(24, rng)]
    rows = []
    for y in range(size):
        row = bytearray()
        for x in range(size):
            u, v = (x + 0.5) / size, (y + 0.5) / size
            dx, dy = u - 0.5, v - 0.5
            r = math.hypot(dx, dy) * 2.0  # 0 centre, 1 the edge of the image
            # the radius where the puff ends, 0.8..1.0 around the rim by the noise
            ang = math.atan2(dy, dx)
            rim = 0.78 + 0.2 * fractal(edge, 0.5 + 0.5 * math.cos(ang), 0.5 + 0.5 * math.sin(ang))
            t = r / rim
            a = 0.0 if t >= 1.0 else (1.0 - t * t) ** 1.6  # soft, dense in the middle
            # a little inner structure, never a hole
            a *= 0.85 + 0.15 * fractal(inner, u, v)
            a = max(0.0, min(1.0, a))
            row += bytes((255, 255, 255, int(a * 255 + 0.5)))
        rows.append(bytes(row))
    return rows


def write_png(path, rows, size):
    raw = b"".join(b"\x00" + r for r in rows)

    def chunk(tag, data):
        return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)

    png = b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", size, size, 8, 6, 0, 0, 0))
    png += chunk(b"IDAT", zlib.compress(raw, 9)) + chunk(b"IEND", b"")
    open(path, "wb").write(png)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    size = int(sys.argv[2]) if len(sys.argv) > 2 else 512
    seed = int(sys.argv[3]) if len(sys.argv) > 3 else 7
    write_png(sys.argv[1], make(size, seed), size)
    print(f"wrote {sys.argv[1]} ({size}x{size})")
