"""Write the CloudPass cloud effect as VFX editor XML (AceXML) into the
msfs-project, then build it in the sim (Project Editor: Build All).

  python tools/make_cloud_vfx.py [PROJECT_EFFECT_DIR]

Modelled on the MK Studios BIKF steam (decoded with tools/spb_dump.py and the
sim's Propdefs): default smoke material, few large soft particles whose size
grows with sqrt(age) and whose alpha fades out. Changes: no rise, drift with
the wind, and graph parameters CloudPass sets per spawn:

  CloudDensity  0..1  thin = light and see-through, dense = opaque and darker
  CloudSize     scale on the particle size (per cloud variation)
  CloudShade    0..1 multiplies the colour: darker at dusk and night
  CloudAlpha    0..1 multiplies the opacity: fainter at night
  GlowWhite     emissive white (strobes, landing lights)
  GlowRed       emissive red (beacon)
"""
import os, sys, uuid

PROJECT_DIR = (sys.argv[1] if len(sys.argv) > 1 else
               os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                            "msfs-project", "PackageSources", "VisualEffectLibs",
                            "cloudpass", "VisualEffectLib"))

# Tunables
RATE = 1.5            # particles per second per spawned cloud
CAPACITY = 40.0
MAX_DISTANCE = 10000.0
LIFETIME = 20.0
SIZE = 35.0           # metres, before CloudSize
ALPHA_THIN, ALPHA_DENSE = 0.20, 0.60   # start alpha at density 0 / 1
GREY_THIN, GREY_DENSE = 0.75, 0.25     # colour at density 0 / 1 (before CloudShade)
WIND_FACTOR = 1.0     # 1 = particles move with the wind
SPREAD_H, SPREAD_V = 12.0, 5.0         # m random start position per particle (flat cloud)
SIZE_VAR = (0.6, 1.4)                  # random size factor per particle
FADE_IN = 0.12                         # share of the lifetime used to fade in

# The atlas variant uses our own material (MaterialLib, CloudPuff.material) with
# a 4x4 atlas of cloud wisps; each particle picks a random cell.
ATLAS_MATERIAL = "{E10A36EB-4E91-4B0E-92DF-01130D2942B4}"
ATLAS_CELLS = 4

# (effect name, uses the atlas material)
EFFECTS = [("Cloudpass", False), ("CloudpassAtlas", True), ("CloudpassBeam", "beam")]

# Landing light beam: attached to the aircraft (local space), glowing mist
# particles shot forward in a cone. Distance travelled grows with age, so
# fading with age makes it bright at the nose and faint far out.
BEAM_RATE = 60.0          # particles per second
BEAM_LIFETIME = 2.5       # s
BEAM_SPEED = 220.0        # m/s along the cone: reaches ~550 m
BEAM_CONE = 9.0           # degrees, outer half angle
BEAM_SIZE = (4.0, 30.0)   # m at the nose / at the end
BEAM_ALPHA = 0.35         # start opacity at full Beam

Z = "{00000000-0000-0000-0000-000000000000}"
# Fixed ids so rebuilding keeps the effect GUID (CloudPass looks it up).
NS = uuid.UUID("6f1d2a8e-0c55-4c2b-9a36-3f1b9e0c7a11")


PREFIX = ""  # per effect; "" for Cloudpass keeps the GUIDs it always had


def gid(name):
    return "{" + str(uuid.uuid5(NS, PREFIX + name)).upper() + "}"


def f(v):
    return f"{v:.6f}"


nodes = []      # (instance id, xml)
positions = {}  # instance id -> (x, y) for the editor


def node(kind, name, body, pos):
    iid = gid(name)
    nodes.append(f'        <VisualEffect.{kind} InstanceId="{iid}">\n{body}        </VisualEffect.{kind}>\n')
    positions[iid] = pos
    return iid


def out(name):
    return gid(name + ".out")


def pin(tag, link=None, value=0.0):
    return f"            <{tag}>{link or Z}, {f(value)}</{tag}>\n"


def math_node(kind, name, x, y, pos, xv=0.0, yv=0.0):
    body = f"            <OutputValue>{out(name)}</OutputValue>\n"
    body += pin("xVariant", x, xv) + pin("yVariant", y, yv)
    node(kind, name, body, pos)
    return out(name)


def lerp(name, x, y, t, pos, xv=0.0, yv=0.0, smooth=False):
    body = f"            <OutputValue>{out(name)}</OutputValue>\n"
    if smooth:
        body += "            <LerpType>SmoothStep</LerpType>\n"
    body += pin("xVariant", x, xv) + pin("yVariant", y, yv) + pin("FXTime", t)
    node("Lerp", name, body, pos)
    return out(name)


def attribute(name, attr, source, pos):
    body = f"            <OutputValue>{out(name)}</OutputValue>\n"
    if source:
        body += "            <ParticleLocationType>Source</ParticleLocationType>\n"
    body += f"            <ParticleAttributeType>{attr}</ParticleAttributeType>\n"
    node("GetParticleAttribute", name, body, pos)
    return out(name)


def param(name, default, pos):
    body = (f"            <OutputValue>{out(name)}</OutputValue>\n"
            f"            <GraphParamName>{name}</GraphParamName>\n"
            + pin("GraphParamDefaultValue", None, default))
    node("GraphParameter", name, body, pos)
    return out(name)


def random(name, lo, hi, seed, index, pos):
    body = (f"            <OutputValue>{out(name)}</OutputValue>\n"
            + pin("MinRandValue", None, lo) + pin("MaxRandValue", None, hi)
            + pin("RandSeed", seed, 0) + pin("RandIndex", None, index))
    node("RandomValue", name, body, pos)
    return out(name)


def vector3(name, xyz, pos):
    body = f"            <OutputValue>{out(name)}</OutputValue>\n"
    for c, (link, v) in zip("xyz", xyz):
        body += pin(c, link, v)
    node("Vector3", name, body, pos)
    return out(name)


def clamp(name, x, lo, hi, pos):
    body = (f"            <OutputValue>{out(name)}</OutputValue>\n"
            + pin("x", x, 0) + pin("y", None, lo) + pin("z", None, hi))
    node("Clamp", name, body, pos)
    return out(name)


def float3(link):
    return f"<Float3In>{link or Z}, 0.000000, 0.000000, 0.000000</Float3In>"


def vector4(name, xyzw, pos):
    body = f"            <OutputValue>{out(name)}</OutputValue>\n"
    for c, (link, v) in zip("xyzw", xyzw):
        body += pin(c, link, v)
    node("Vector4", name, body, pos)
    return out(name)


def build(name, atlas):
    effect, emitter, init, update, output = (gid(n) for n in ("effect", "emitter", "init", "update", "output"))

    # graph parameters from CloudPass
    density = param("CloudDensity", 0.6, (-700, 100))
    csize = param("CloudSize", 1.0, (-700, 250))
    shade = param("CloudShade", 1.0, (-700, 400))
    calpha = param("CloudAlpha", 1.0, (-700, 550))
    glow_w = param("GlowWhite", 0.0, (-700, 700))
    glow_r = param("GlowRed", 0.0, (-700, 850))

    # per particle age 0..1, source size, and an id that seeds its randoms
    age = attribute("age", "AgeOverLifetime", False, (-450, 400))
    src_size = attribute("srcsize", "Size", True, (-450, 520))
    pid = attribute("pid", "id", False, (-950, 300))

    # random start position (flat), rotation and size per particle
    rx = random("rx", -SPREAD_H, SPREAD_H, pid, 1, (-800, -300))
    ry = random("ry", -SPREAD_V, SPREAD_V, pid, 2, (-800, -220))
    rz = random("rz", -SPREAD_H, SPREAD_H, pid, 3, (-800, -140))
    start = vector3("startpos", [(rx, 0), (ry, 0), (rz, 0)], (-600, -220))
    rrot = random("rrot", 0.0, 6.283, pid, 4, (-800, -60))
    rot = vector3("rot", [(None, 0), (None, 0), (rrot, 0)], (-600, -60))
    rsize = random("rsize", SIZE_VAR[0], SIZE_VAR[1], pid, 5, (-800, 20))

    base_size = math_node("MultiplyOperation", "initsize", csize, None, (-450, 250), yv=SIZE)
    init_size = math_node("MultiplyOperation", "initsizevar", base_size, rsize, (-350, 250))
    grow = math_node("PowOperation", "grow", age, None, (-250, 400), yv=0.5)
    upd_size = math_node("MultiplyOperation", "updsize", grow, src_size, (-50, 450))

    wind = out("wind")
    node("WindDirection", "wind",
         f"            <OutputValue>{wind}</OutputValue>\n", (-450, 640))
    drift = math_node("MultiplyOperation", "drift", wind, None, (-250, 640), yv=WIND_FACTOR)

    # opacity: by density and night, fading in over FADE_IN, out towards the end
    alpha_d = lerp("alpha0", None, None, density, (-450, 100), xv=ALPHA_THIN, yv=ALPHA_DENSE)
    alpha0 = math_node("MultiplyOperation", "alphanight", alpha_d, calpha, (-350, 130))
    alpha_out = lerp("alpha", alpha0, None, age, (-250, 160), yv=0.0, smooth=True)
    fin_t = math_node("MultiplyOperation", "fadeint", age, None, (-450, 180), yv=1.0 / FADE_IN)
    fin = clamp("fadein", fin_t, 0.0, 1.0, (-350, 200))
    alpha = math_node("MultiplyOperation", "alphafade", alpha_out, fin, (-150, 180))
    grey_d = lerp("grey", None, None, density, (-450, -20), xv=GREY_THIN, yv=GREY_DENSE)
    grey = math_node("MultiplyOperation", "greyshade", grey_d, shade, (-350, -20))
    colour = vector4("colour", [(grey, 0), (grey, 0), (grey, 0), (alpha, 0)], (-50, 60))

    red = math_node("AddOperation", "red", glow_w, glow_r, (-450, 780))
    emissive = vector4("emissive", [(red, 0), (glow_w, 0), (glow_w, 0), (None, 1.0)], (-250, 760))

    tex = ""
    if atlas:
        cell = random("rcell", 0.0, ATLAS_CELLS * ATLAS_CELLS - 0.001, pid, 6, (-800, 100))
        tex = f"            <ParticleTextureIndex>\n    {pin('FloatIn', cell, 0)}            </ParticleTextureIndex>\n"

    node("VisualEffect", "effect",
         f"            <Name>{name}</Name>\n"
         "            <EmitterList>\n"
         f'                <ObjectReference InstanceId="{emitter}" id="Emitter"/>\n'
         "            </EmitterList>\n", (300, -100))
    node("Emitter", "emitter",
         pin("ParticleRate", None, RATE)
         + f"            <Capacity>{f(CAPACITY)}</Capacity>\n"
         + f"            <MaxDistanceEmission>{f(MAX_DISTANCE)}</MaxDistanceEmission>\n"
         "            <ParticleInit>\n"
         f'                <ObjectReference InstanceId="{init}" id="BlockParticleInit"/>\n'
         "            </ParticleInit>\n", (300, 0))
    node("BlockParticleInit", "init",
         "            <ParticleUpdate>\n"
         f'                <ObjectReference InstanceId="{update}" id="BlockParticleUpdate"/>\n'
         "            </ParticleUpdate>\n"
         f"            <ParticleLifetime>\n    {pin('FloatIn', None, LIFETIME)}            </ParticleLifetime>\n"
         f"            <ParticleSize>\n    {pin('FloatIn', init_size, 0)}            </ParticleSize>\n"
         f"            <ParticlePosition>\n                {float3(start)}\n            </ParticlePosition>\n"
         f"            <ParticleRotation>\n                {float3(rot)}\n            </ParticleRotation>\n"
         f"            <ParticleVelocity>\n                {float3(None)}\n            </ParticleVelocity>\n"
         + tex, (300, 200))
    node("BlockParticleUpdate", "update",
         "            <ParticleOutput>\n"
         f'                <ObjectReference InstanceId="{output}" id="Output"/>\n'
         "            </ParticleOutput>\n"
         f"            <ParticleVelocity>\n                {float3(drift)}\n            </ParticleVelocity>\n"
         f"            <ParticleSize>\n    {pin('FloatIn', upd_size, 0)}            </ParticleSize>\n", (300, 420))
    material = ""
    if atlas:
        material = (f"            <Material>{ATLAS_MATERIAL}</Material>\n"
                    "            <UVMode>Atlas</UVMode>\n"
                    f"            <AtlasSize>{Z}, {f(ATLAS_CELLS)}, {f(ATLAS_CELLS)}</AtlasSize>\n")
    node("Output", "output",
         material
         + f"            <ParticleColor>\n                <ColorIn>{colour}, 0, 0, 0, 0</ColorIn>\n"
         "            </ParticleColor>\n"
         f"            <MaterialEmissiveColor>\n                <ColorIn>{emissive}, 0, 0, 0, 0</ColorIn>\n"
         "            </MaterialEmissiveColor>\n", (300, 620))
    return effect


def build_beam(name):
    effect, emitter, init, update, output = (gid(n) for n in ("effect", "emitter", "init", "update", "output"))

    # Beam: 0..1 strength from CloudPass (landing lights, in cloud, darkness).
    beam = param("Beam", 0.0, (-700, 100))
    hdg = param("BeamHeading", 0.0, (-700, 250))   # cone axis, set from CloudPass
    pitch = param("BeamPitch", 0.0, (-700, 400))

    age = attribute("age", "AgeOverLifetime", False, (-450, 400))
    pid = attribute("pid", "id", False, (-950, 300))

    cone = out("cone")
    node("RandomDirectionInCone", "cone",
         f"            <OutputValue>{cone}</OutputValue>\n"
         + pin("InputPitch", pitch, 0) + pin("InputHeading", hdg, 0)
         + pin("InnerAngle", None, 0.0) + pin("OuterAngle", None, BEAM_CONE)
         + pin("RandSeed", pid, 0) + pin("RandIndex", None, 1), (-450, 250))
    velocity = math_node("MultiplyOperation", "velocity", cone, None, (-250, 250), yv=BEAM_SPEED)

    # size widens with distance (age), opacity and glow fall off with it
    size = lerp("size", None, None, age, (-250, 400), xv=BEAM_SIZE[0], yv=BEAM_SIZE[1])
    left = lerp("left", None, None, age, (-350, 520), xv=1.0, yv=0.0)  # 1 - age
    falloff = math_node("MultiplyOperation", "falloff", left, left, (-250, 520))  # (1-age)^2
    strength = math_node("MultiplyOperation", "strength", falloff, beam, (-150, 520))
    alpha = math_node("MultiplyOperation", "alpha", strength, None, (-50, 520), yv=BEAM_ALPHA)
    colour = vector4("colour", [(None, 1.0), (None, 1.0), (None, 1.0), (alpha, 0)], (-50, 60))
    emissive = vector4("emissive", [(strength, 0), (strength, 0), (strength, 0), (None, 1.0)], (-50, 700))

    node("VisualEffect", "effect",
         f"            <Name>{name}</Name>\n"
         "            <EmitterList>\n"
         f'                <ObjectReference InstanceId="{emitter}" id="Emitter"/>\n'
         "            </EmitterList>\n", (300, -100))
    node("Emitter", "emitter",
         pin("ParticleRate", None, BEAM_RATE)
         + f"            <Capacity>{f(BEAM_RATE * BEAM_LIFETIME * 1.5)}</Capacity>\n"
         + f"            <MaxDistanceEmission>{f(MAX_DISTANCE)}</MaxDistanceEmission>\n"
         "            <EmitInLocalSpace>True</EmitInLocalSpace>\n"
         "            <ParticleInit>\n"
         f'                <ObjectReference InstanceId="{init}" id="BlockParticleInit"/>\n'
         "            </ParticleInit>\n", (300, 0))
    node("BlockParticleInit", "init",
         "            <ParticleUpdate>\n"
         f'                <ObjectReference InstanceId="{update}" id="BlockParticleUpdate"/>\n'
         "            </ParticleUpdate>\n"
         f"            <ParticleLifetime>\n    {pin('FloatIn', None, BEAM_LIFETIME)}            </ParticleLifetime>\n"
         f"            <ParticleSize>\n    {pin('FloatIn', None, BEAM_SIZE[0])}            </ParticleSize>\n"
         f"            <ParticleVelocity>\n                {float3(velocity)}\n            </ParticleVelocity>\n", (300, 200))
    node("BlockParticleUpdate", "update",
         "            <ParticleOutput>\n"
         f'                <ObjectReference InstanceId="{output}" id="Output"/>\n'
         "            </ParticleOutput>\n"
         f"            <ParticleSize>\n    {pin('FloatIn', size, 0)}            </ParticleSize>\n", (300, 420))
    node("Output", "output",
         f"            <ParticleColor>\n                <ColorIn>{colour}, 0, 0, 0, 0</ColorIn>\n"
         "            </ParticleColor>\n"
         f"            <MaterialEmissiveColor>\n                <ColorIn>{emissive}, 0, 0, 0, 0</ColorIn>\n"
         "            </MaterialEmissiveColor>\n", (300, 620))
    return effect


def write():
    global PREFIX
    for name, atlas in EFFECTS:
        PREFIX = "" if name == "Cloudpass" else name + "/"
        nodes.clear()
        positions.clear()
        if atlas == "beam":
            build_beam(name)
        else:
            build(name, atlas)
        doc = ('\ufeff<?xml version="1.0" encoding="UTF-8"?>\n\n'
               '<SimBase.Document Type="AceXML" version="1,0">\n'
               "    <Descr>AceXML Document</Descr>\n"
               "    <WorldBase.Flight>\n" + "".join(nodes) +
               "    </WorldBase.Flight>\n</SimBase.Document>\n")
        edition = ('\ufeff<?xml version="1.0" encoding="UTF-8"?>\n\n'
                   f'<SimBase.Document Type="EditionInfo" version="1,0" id="{name}_edition">\n'
                   "    <Descr>This file contains useful additional properties for edition purpose.</Descr>\n"
                   + "".join(f'    <SimEdition.EditionInfo RelatedInstanceId="{i}">\n'
                             f"        <NodePosition>{x:.3f},{y:.3f}</NodePosition>\n"
                             "    </SimEdition.EditionInfo>\n" for i, (x, y) in positions.items())
                   + "</SimBase.Document>\n")
        for fname, text in ((f"{name}.xml", doc), (f"{name}_edition.xml", edition)):
            with open(os.path.join(PROJECT_DIR, fname), "w", encoding="utf-8", newline="\r\n") as fh:
                fh.write(text)
        print(f"wrote {name}.xml ({len(nodes)} nodes), effect id {gid('effect')}")
    lib = "\r\n".join(['<VisualEffectLibrary Version="1.0.0">']
                       + [f'\t<VisualEffect File="{n}"/>' for n, _ in EFFECTS]
                       + ["</VisualEffectLibrary>", ""])
    with open(os.path.join(PROJECT_DIR, "VisualEffectLibrary.vfxlib"), "w", encoding="utf-8", newline="") as fh:
        fh.write(lib)


if __name__ == "__main__":
    write()
