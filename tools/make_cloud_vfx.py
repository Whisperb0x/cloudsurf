"""Write the CloudSurf cloud effect as VFX editor XML (AceXML) into the
msfs-project, then build it in the sim (Project Editor: Build All).

  python tools/make_cloud_vfx.py [PROJECT_EFFECT_DIR]

Built like a steam or smoke effect: default smoke material, few large soft
particles whose size grows with sqrt(age) and whose alpha fades out. Changes:
no rise, drift with the wind, and graph parameters CloudSurf sets per spawn:

  CloudDensity  0..1  thin = light and see-through, dense = opaque and darker
  CloudSize     scale on the particle size (per cloud variation)
  CloudShade    0..1 multiplies the colour: darker at dusk and night
  CloudAlpha    0..1 multiplies the opacity: fainter at night
  CloudFade     0..1 multiplies opacity and glow: all clouds fade out together
                after leaving the sim's cloud
  LightX/Y/Z    aircraft position in the cloud's frame (x right, y up, z ahead)
  BeamX/Y/Z     landing light direction (unit vector) in that frame
  LandingGlow, StrobeGlow, WingGlow, BeaconGlow, NavRed, NavGreen
                light strengths (0 when off)

Every particle measures itself against the light: the landing light only
lights particles inside its cone and fades with distance; strobes, beacon,
wing and nav lights light particles close to the aircraft.
"""
import math, os, sys, uuid

PROJECT_DIR = (sys.argv[1] if len(sys.argv) > 1 else
               os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                            "msfs-project", "PackageSources", "VisualEffectLibs",
                            "cloudsurf", "VisualEffectLib"))

# Tunables
RATE = 1.5            # particles per second per spawned cloud
CAPACITY = 40.0
MAX_DISTANCE = 10000.0
LIFETIME = 20.0
SIZE = 35.0           # metres, before CloudSize
ALPHA_THIN, ALPHA_DENSE = 0.30, 0.85   # start alpha at density 0 / 1 (CloudDensity goes up to 2)
GREY_THIN, GREY_DENSE = 0.75, 0.25     # colour at density 0 / 1 (before CloudShade)
WIND_FACTOR = 1.0     # 1 = particles move with the wind
SPREAD_H, SPREAD_V = 12.0, 5.0         # m random start position per particle (flat cloud)
SIZE_VAR = (0.6, 1.4)                  # random size factor per particle
FADE_IN = 0.04                         # share of the lifetime used to fade in
# A new cloud starts with a burst so it is there at once: extra particles per
# second right after spawning, tapering off over START_TIME seconds.
START_RATE, START_TIME = 12.0, 0.5
FADE_OUT = 0.4                         # share of the lifetime used to fade out
GLOW_GAIN = 6.0                        # emissive per unit of light strength
# Light falloff 1 / (1 + (d/near)^2), reaching zero at `reach` (metres).
LANDING_NEAR, LANDING_REACH = 250.0, 600.0
LANDING_CONE = 12.0                    # degrees, half angle where the landing light ends
STROBE_NEAR, STROBE_REACH = 15.0, 60.0
NAV_NEAR, NAV_REACH = 10.0, 45.0       # nav and wing lights
GLOW_FLATTEN = 3.0                     # vertical distance counts this much more near the aircraft

# The atlas variant uses our own material (MaterialLib, CloudPuff.material) with
# a 4x4 atlas of cloud wisps; each particle picks a random cell. Its quads only
# turn around the vertical axis (cylindrical billboards), so the wisps stay
# level instead of rolling with the camera, and they get only a small tilt.
ATLAS_MATERIAL = "{E10A36EB-4E91-4B0E-92DF-01130D2942B4}"
ATLAS_CELLS = 4
ATLAS_TILT = 0.25                      # rad, random tilt either way
ATLAS_RATE, ATLAS_SIZE = 2.5, 26.0     # more, smaller wisps overlap into more depth
ATLAS_SPREAD_H, ATLAS_SPREAD_V = 18.0, 8.0

# (effect name, uses the atlas material)
EFFECTS = [("CloudSurf", False), ("CloudSurfWisps", True), ("CloudSurfBeam", "beam")]

# Landing light beam: attached to the aircraft (local space), glowing mist
# particles shot forward in a cone. Distance travelled grows with age, so
# fading with age makes it bright at the nose and faint far out.
BEAM_RATE = 60.0          # particles per second
BEAM_LIFETIME = 2.5       # s
BEAM_SPEED = 220.0        # m/s along the cone: reaches ~550 m
BEAM_CONE = 9.0           # degrees, outer half angle
BEAM_SIZE = (3.0, 40.0)   # m at the nose / at the end
BEAM_ALPHA = 0.55         # start opacity at full Beam
BEAM_GLOW = 3.0           # emissive at the nose at full Beam

Z = "{00000000-0000-0000-0000-000000000000}"
# Fixed ids so rebuilding keeps the effect GUID (CloudSurf looks it up).
NS = uuid.UUID("6f1d2a8e-0c55-4c2b-9a36-3f1b9e0c7a11")


PREFIX = ""  # per effect: its name, so each effect has its own ids


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

    # graph parameters from CloudSurf
    density = param("CloudDensity", 0.6, (-700, 100))
    csize = param("CloudSize", 1.0, (-700, 250))
    shade = param("CloudShade", 1.0, (-700, 400))
    calpha = param("CloudAlpha", 1.0, (-700, 550))
    cfade = param("CloudFade", 1.0, (-700, 625))
    light = vector3("light", [(param(n, 0.0, (-1100, 700 + 80 * i)), 0)
                              for i, n in enumerate(("LightX", "LightY", "LightZ"))], (-950, 760))
    beam_dir = vector3("beamdir", [(param(n, 0.0, (-1100, 950 + 80 * i)), 0)
                                   for i, n in enumerate(("BeamX", "BeamY", "BeamZ"))], (-950, 1000))
    landing = param("LandingGlow", 0.0, (-700, 1200))
    strobe = param("StrobeGlow", 0.0, (-700, 1280))
    wing = param("WingGlow", 0.0, (-700, 1360))
    beacon = param("BeaconGlow", 0.0, (-700, 1440))
    nav_r = param("NavRed", 0.0, (-700, 1520))
    nav_g = param("NavGreen", 0.0, (-700, 1600))

    # per particle age 0..1, source size, and an id that seeds its randoms
    age = attribute("age", "AgeOverLifetime", False, (-450, 400))
    src_size = attribute("srcsize", "Size", True, (-450, 520))
    pid = attribute("pid", "id", False, (-950, 300))

    # random start position (flat), rotation and size per particle
    spread_h, spread_v = (ATLAS_SPREAD_H, ATLAS_SPREAD_V) if atlas else (SPREAD_H, SPREAD_V)
    rx = random("rx", -spread_h, spread_h, pid, 1, (-800, -300))
    ry = random("ry", -spread_v, spread_v, pid, 2, (-800, -220))
    rz = random("rz", -spread_h, spread_h, pid, 3, (-800, -140))
    start = vector3("startpos", [(rx, 0), (ry, 0), (rz, 0)], (-600, -220))
    rrot = random("rrot", -ATLAS_TILT if atlas else 0.0, ATLAS_TILT if atlas else 6.283, pid, 4, (-800, -60))
    rot = vector3("rot", [(None, 0), (None, 0), (rrot, 0)], (-600, -60))
    rsize = random("rsize", SIZE_VAR[0], SIZE_VAR[1], pid, 5, (-800, 20))

    base_size = math_node("MultiplyOperation", "initsize", csize, None, (-450, 250),
                          yv=ATLAS_SIZE if atlas else SIZE)
    init_size = math_node("MultiplyOperation", "initsizevar", base_size, rsize, (-350, 250))
    grow = math_node("PowOperation", "grow", age, None, (-250, 400), yv=0.5)
    upd_size = math_node("MultiplyOperation", "updsize", grow, src_size, (-50, 450))

    wind = out("wind")
    node("WindDirection", "wind",
         f"            <OutputValue>{wind}</OutputValue>\n", (-450, 640))
    drift = math_node("MultiplyOperation", "drift", wind, None, (-250, 640), yv=WIND_FACTOR)

    # opacity: by density (above 1 only more opaque) and night, fading in over
    # FADE_IN and out over the last FADE_OUT of the lifetime
    dens1 = clamp("dens1", density, 0.0, 1.0, (-550, 0))
    alpha_d = lerp("alpha0", None, None, density, (-450, 100), xv=ALPHA_THIN, yv=ALPHA_DENSE)
    alpha_n = math_node("MultiplyOperation", "alphanight", alpha_d, calpha, (-350, 130))
    alpha0 = clamp("alphamax", alpha_n, 0.0, 1.0, (-300, 100))
    fout_t = lerp("fadeoutt", None, None, age, (-450, 220), xv=1.0 / FADE_OUT, yv=0.0)
    fout = clamp("fadeout", fout_t, 0.0, 1.0, (-350, 240))
    fin_t = math_node("MultiplyOperation", "fadeint", age, None, (-450, 180), yv=1.0 / FADE_IN)
    fin = clamp("fadein", fin_t, 0.0, 1.0, (-350, 200))
    fade_p = math_node("MultiplyOperation", "fadep", fin, fout, (-250, 220))
    fade = math_node("MultiplyOperation", "fade", fade_p, cfade, (-200, 240))
    alpha = math_node("MultiplyOperation", "alphafade", alpha0, fade, (-150, 180))
    grey_d = lerp("grey", None, None, dens1, (-450, -20), xv=GREY_THIN, yv=GREY_DENSE)
    grey = math_node("MultiplyOperation", "greyshade", grey_d, shade, (-350, -20))
    colour = vector4("colour", [(grey, 0), (grey, 0), (grey, 0), (alpha, 0)], (-50, 60))

    # Where this particle is (start position plus wind drift so far), and
    # where it lies from the aircraft. The particle's own randoms are seeded
    # by its id, so they give the same start position here as in Init.
    alive = math_node("MultiplyOperation", "alive", age, None, (-450, 1100), yv=LIFETIME)
    moved = math_node("MultiplyOperation", "moved", drift, alive, (-350, 1100))
    ppos = math_node("AddOperation", "ppos", start, moved, (-250, 1100))
    rel = math_node("SubtractOperation", "rel", ppos, light, (-150, 1100))
    dd = math_node("Dot", "dd", rel, rel, (-50, 1100))
    dist = math_node("PowOperation", "dist", dd, None, (50, 1100), yv=0.5)
    # flatter glow near the aircraft: vertical distance counts GLOW_FLATTEN times
    up = vector3("up", [(None, 0), (None, 1.0), (None, 0)], (-150, 1200))
    rel_up = math_node("Dot", "relup", rel, up, (-50, 1200))
    up2 = math_node("MultiplyOperation", "up2", rel_up, rel_up, (50, 1200))
    up2k = math_node("MultiplyOperation", "up2k", up2, None, (150, 1200), yv=GLOW_FLATTEN ** 2 - 1)
    dd_flat = math_node("AddOperation", "ddflat", dd, up2k, (250, 1200))
    dist_flat = math_node("PowOperation", "distflat", dd_flat, None, (350, 1200), yv=0.5)

    def falloff(tag, sq, d, near, reach, y):
        q = math_node("MultiplyOperation", tag + "q", sq, None, (-50, y), yv=1.0 / near ** 2)
        q1 = math_node("AddOperation", tag + "q1", q, None, (50, y), yv=1.0)
        inv = math_node("DivideOperation", tag + "inv", None, q1, (150, y), xv=1.0)
        t = math_node("MultiplyOperation", tag + "t", d, None, (-50, y + 60), yv=1.0 / reach)
        lin = clamp(tag + "lin", math_node("SubtractOperation", tag + "1mt", None, t, (50, y + 60), xv=1.0),
                    0.0, 1.0, (150, y + 60))
        return math_node("MultiplyOperation", tag + "fall", inv, lin, (250, y))

    # landing light: inside the cone (soft edge), fading with distance
    cos_edge = math.cos(math.radians(LANDING_CONE))
    dot_b = math_node("Dot", "dotb", rel, beam_dir, (-50, 1300))
    dist1 = math_node("AddOperation", "dist1", dist, None, (50, 1360), yv=1.0)
    cos_a = math_node("DivideOperation", "cosa", dot_b, dist1, (150, 1300))
    cone_t = math_node("SubtractOperation", "conet", cos_a, None, (250, 1300), yv=cos_edge)
    cone_s = math_node("MultiplyOperation", "cones", cone_t, None, (350, 1300), yv=1.0 / (1.0 - cos_edge))
    cone1 = clamp("cone1", cone_s, 0.0, 1.0, (450, 1300))
    cone = math_node("MultiplyOperation", "cone", cone1, cone1, (550, 1300))
    fall_l = falloff("land", dd, dist, LANDING_NEAR, LANDING_REACH, 1420)
    land_k = math_node("MultiplyOperation", "landk", cone, fall_l, (650, 1420))
    land = math_node("MultiplyOperation", "land", land_k, landing, (750, 1420))

    fall_s = falloff("strobe", dd_flat, dist_flat, STROBE_NEAR, STROBE_REACH, 1540)
    fall_n = falloff("nav", dd_flat, dist_flat, NAV_NEAR, NAV_REACH, 1660)
    white_s = math_node("MultiplyOperation", "whites", strobe, fall_s, (650, 1540))
    white_n = math_node("MultiplyOperation", "whiten", wing, fall_n, (650, 1660))
    white = math_node("AddOperation", "white",
                      math_node("AddOperation", "white0", land, white_s, (750, 1540)), white_n, (850, 1600))
    red_b = math_node("MultiplyOperation", "redb", beacon, fall_s, (650, 1780))
    red_n = math_node("MultiplyOperation", "redn", nav_r, fall_n, (650, 1840))
    red = math_node("AddOperation", "red",
                    math_node("AddOperation", "red0", red_b, red_n, (750, 1800)), white, (850, 1800))
    green_n = math_node("MultiplyOperation", "greenn", nav_g, fall_n, (650, 1900))
    green = math_node("AddOperation", "green", green_n, white, (850, 1900))

    # emissive: white plus red (beacon, left nav) and green (right nav)
    gain = math_node("MultiplyOperation", "gain", cfade, None, (850, 1700), yv=GLOW_GAIN)
    red_e = math_node("MultiplyOperation", "rede", red, gain, (950, 1800))
    green_e = math_node("MultiplyOperation", "greene", green, gain, (950, 1900))
    white_e = math_node("MultiplyOperation", "whitee", white, gain, (950, 1600))
    emissive = vector4("emissive", [(red_e, 0), (green_e, 0), (white_e, 0), (None, 1.0)], (1050, 1700))

    tex = ""
    if atlas:
        cell = random("rcell", 0.0, ATLAS_CELLS * ATLAS_CELLS - 0.001, pid, 6, (-800, 100))
        # same order as BlockParticleInit in the sim's Propdefs
        tex = (f"            <ParticleQuadBillboardAxis>\n                <QuadBillboardAxis>{Z}, 0.000000, 1.000000, 0.000000</QuadBillboardAxis>\n"
               "            </ParticleQuadBillboardAxis>\n"
               f"            <ParticleTextureIndex>\n    {pin('FloatIn', cell, 0)}            </ParticleTextureIndex>\n")

    node("VisualEffect", "effect",
         f"            <Name>{name}</Name>\n"
         "            <EmitterList>\n"
         f'                <ObjectReference InstanceId="{emitter}" id="Emitter"/>\n'
         "            </EmitterList>\n", (300, -100))
    inst_age = out("instage")
    node("GetInstanceAttribute", "instage",
         f"            <OutputValue>{inst_age}</OutputValue>\n"
         "            <InstanceAttributeType>Age</InstanceAttributeType>\n", (-450, -400))
    start_t = math_node("MultiplyOperation", "startt", inst_age, None, (-350, -400), yv=1.0 / START_TIME)
    start_left = clamp("startleft", math_node("SubtractOperation", "start1mt", None, start_t, (-250, -400), xv=1.0),
                       0.0, 1.0, (-150, -400))
    burst = math_node("MultiplyOperation", "burst", start_left, None, (-50, -400), yv=START_RATE)
    rate = math_node("AddOperation", "rate", burst, None, (50, -400), yv=ATLAS_RATE if atlas else RATE)
    node("Emitter", "emitter",
         pin("ParticleRate", rate, 0.0)
         + f"            <Capacity>{f(max(CAPACITY, (ATLAS_RATE if atlas else RATE) * LIFETIME + START_RATE * START_TIME + 5))}</Capacity>\n"
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
        material = (f"            <QuadBillboardType>Cylindrical</QuadBillboardType>\n"
                    f"            <Material>{ATLAS_MATERIAL}</Material>\n"
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

    # Beam: 0..1 strength from CloudSurf (landing lights, in cloud, darkness).
    beam = param("Beam", 0.0, (-700, 100))
    hdg = param("BeamHeading", 0.0, (-700, 250))   # cone axis, set from CloudSurf
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
    glow = math_node("MultiplyOperation", "glow", strength, None, (-50, 640), yv=BEAM_GLOW)
    emissive = vector4("emissive", [(glow, 0), (glow, 0), (glow, 0), (None, 1.0)], (-50, 700))

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
        PREFIX = name + "/"
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
