"""Dump an MSFS .spb (visual effect property bag) as a tree, for comparing
effects and finding the floats worth changing.

  python tools/spb_dump.py FILE.spb [FILE2.spb]

Format as far as worked out: header, then a schema of (16-byte type GUID,
int32 size) records from offset 0x32, then data records [u32 index into the
schema, 1-based] followed by either `size` fixed bytes or, for size -1, a u32
length and that many bytes (which usually hold nested records again).
"""
import glob, os, re, struct, sys, uuid

PROPDEFS = os.environ.get(
    "SPB_PROPDEFS", r"C:\XboxGames\Microsoft Flight Simulator 2024\Content\Propdefs\1.0\Common")


def load_names():
    """Property/set GUID -> name from the sim's Propdefs XML files."""
    names = {}
    tag = re.compile(r"<(?:PropertyDef|SetDef)\b([^>]*)>", re.S)
    attr_name = re.compile(r'\bname\s*=\s*"([^"]+)"')
    attr_id = re.compile(r'\bid\s*=\s*"\{([0-9A-Fa-f-]+)\}"')
    for f in glob.glob(os.path.join(PROPDEFS, "*.xml")):
        for attrs in tag.findall(open(f, encoding="utf-8", errors="ignore").read()):
            n, i = attr_name.search(attrs), attr_id.search(attrs)
            if n and i:
                names[i.group(1).upper()] = n.group(1)
    return names


NAMES = load_names()


def schema_of(d):
    """Returns ([size per record index], [name per record index], data start)."""
    i, sizes, names = 0x32, [], []
    while i + 20 <= len(d):
        size = struct.unpack_from("<i", d, i + 16)[0]
        if size not in (-1, 4, 8, 12, 16, 20, 24, 28, 32, 36, 40, 44, 48):
            break
        gid = str(uuid.UUID(bytes_le=d[i:i + 16])).upper()
        sizes.append(size)
        names.append(NAMES.get(gid, "?" + gid[:8]))
        i += 20
    return sizes, names, i


def records(d, start, end, schema):
    """Parse records in d[start:end]; None if they don't tile the range exactly."""
    out, p = [], start
    while p < end:
        if end - p <= 8 and not any(d[p:end]):
            break  # zero padding at the end of a container
        if p + 4 > end:
            return None
        idx = struct.unpack_from("<I", d, p)[0]
        if not 1 <= idx <= len(schema):
            return None
        size = schema[idx - 1]
        if size == -1:
            if p + 8 > end:
                return None
            n = struct.unpack_from("<I", d, p + 4)[0]
            body = (p + 8, p + 8 + n)
            p = p + 8 + n
        else:
            body = (p + 4, p + 4 + size)
            p = p + 4 + size
        if p > end:
            return None
        out.append((idx, size, body))
    return out


def fmt_leaf(d, a, b):
    raw = d[a:b]
    n = b - a
    if n == 4:
        f = struct.unpack("<f", raw)[0]
        i = struct.unpack("<i", raw)[0]
        return f"f={f:g} i={i}"
    if n == 16:
        return "guid " + str(uuid.UUID(bytes_le=raw)).upper()
    if n == 20:
        f = struct.unpack_from("<f", raw, 16)[0]
        return "guid " + str(uuid.UUID(bytes_le=raw[:16])).upper() + f" + f={f:g}"
    if n % 4 == 0 and n <= 48:
        return "floats " + " ".join(f"{x:g}" for x in struct.unpack(f"<{n // 4}f", raw))
    return raw.hex(" ")[:96]


def walk(d, start, end, schema, depth, out, names=None):
    recs = records(d, start, end, schema)
    if recs is None:
        return False
    for idx, size, (a, b) in recs:
        label = names[idx - 1] if names else f"#{idx:02x}"
        line = f"{'  ' * depth}{label} @{a:#06x} len={b - a}"
        if size == -1 and b > a and walk_try(d, a, b, schema, depth + 1):
            out.append(line)
            walk(d, a, b, schema, depth + 1, out, names)
        else:
            out.append(f"{line}  {fmt_leaf(d, a, b)}")
    return True


def walk_try(d, a, b, schema, depth):
    return records(d, a, b, schema) is not None and b - a >= 4


def effect_guids(path):
    """InstanceIds of the VisualEffect nodes in an .spb (the GUIDs to spawn)."""
    d = open(path, "rb").read()
    schema, names, start = schema_of(d)
    found = []

    def scan(a, b):
        recs = records(d, a, b, schema)
        for idx, size, (s, e) in recs or []:
            if names[idx - 1] == "VisualEffect":
                for cidx, csize, (cs, ce) in records(d, s, e, schema) or []:
                    if names[cidx - 1] == "InstanceId" and ce - cs == 16:
                        found.append(str(uuid.UUID(bytes_le=d[cs:ce])).upper())
            elif size == -1 and e > s and walk_try(d, s, e, schema, 0):
                scan(s, e)

    scan(start, len(d))
    return found


def dump(path):
    d = open(path, "rb").read()
    schema, names, data_start = schema_of(d)
    out = []
    if not walk(d, data_start, len(d), schema, 0, out, names):
        out.append(f"(could not tile records from {data_start:#x})")
    return out


if __name__ == "__main__":
    dumps = [dump(p) for p in sys.argv[1:]]
    if len(dumps) == 1:
        print("\n".join(dumps[0]))
    else:
        w = max(len(x) for x in dumps[0]) + 2
        for i in range(max(len(x) for x in dumps)):
            l = dumps[0][i] if i < len(dumps[0]) else ""
            r = dumps[1][i] if i < len(dumps[1]) else ""
            print(l.ljust(w) + "| " + r)
