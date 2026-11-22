# Bukti scene Blender gaya utech_gadget: gang kampung + warung + chibi + router.
# Jalankan: blender -b -P scene.py -- still | anim
import bpy, math, os, sys
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
MODE = sys.argv[sys.argv.index('--') + 1] if '--' in sys.argv else 'still'

# ---------- reset ----------
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene

# ---------- renderer: Eevee, bayangan lembut, AO ----------
# Guard hasattr: API Eevee berubah antar versi (VM lokal 4.0, runner GitHub 5.0).
def _set(obj, name, value):
    if hasattr(obj, name):
        setattr(obj, name, value)

scene.render.engine = 'BLENDER_EEVEE'
_set(scene.eevee, 'taa_render_samples', 32)
_set(scene.eevee, 'use_soft_shadows', True)  # <= 4.x
_set(scene.eevee, 'use_shadows', True)       # 5.x
_set(scene.eevee, 'shadow_cube_size', '1024')
_set(scene.eevee, 'shadow_cascade_size', '1024')
_set(scene.eevee, 'shadow_pool_size', '1024')  # 5.x: atlas bayangan lebih besar
_set(scene.eevee, 'use_gtao', True)
_set(scene.eevee, 'gtao_factor', 1.1)
_set(scene.eevee, 'gtao_distance', 4.0)
scene.render.resolution_x = 1080
scene.render.resolution_y = 1920
scene.render.resolution_percentage = 50  # iterasi cepat; final proof dinaikkan
scene.render.fps = 24
# Grading "tropis jenuh" ala referensi: AgX + Punchy (Filmik bikin pucat).
try:
    scene.view_settings.view_transform = 'AgX'
    scene.view_settings.look = 'Punchy'
except Exception:
    scene.view_settings.view_transform = 'Filmic'
    scene.view_settings.look = 'High Contrast'
scene.view_settings.exposure = 0.35
scene.frame_start, scene.frame_end = 1, 240

# ---------- dunia: langit biru + matahari ----------
world = bpy.data.worlds.new('W'); scene.world = world
world.use_nodes = True
world.node_tree.nodes['Background'].inputs[0].default_value = (0.08, 0.34, 0.98, 1)
world.node_tree.nodes['Background'].inputs[1].default_value = 0.34

sun_data = bpy.data.lights.new('sun', 'SUN')
sun_data.energy = 5.2
sun_data.color = (1.0, 0.88, 0.70)  # matahari hangat
sun_data.angle = math.radians(4.0)  # tepi bayangan lembut
_set(sun_data, 'shadow_ray_count', 3)    # 5.x: sinar penelusuran bayangan lembut
_set(sun_data, 'shadow_step_count', 12)  # 5.x: langkah penelusuran (anti-grain)
sun = bpy.data.objects.new('sun', sun_data)
scene.collection.objects.link(sun)
sun.rotation_euler = (math.radians(48), math.radians(12), math.radians(-32))
_set(sun_data, 'shadow_cascade_max_distance', 60)

fill_data = bpy.data.lights.new('fill', 'SUN')
fill_data.energy = 0.38
fill_data.color = (0.72, 0.84, 1.0)  # isi dingin: bayangan agak biru
fill = bpy.data.objects.new('fill', fill_data)
scene.collection.objects.link(fill)
fill.rotation_euler = (math.radians(60), 0, math.radians(140))
_set(fill_data, 'shadow_ray_count', 2)
_set(fill_data, 'shadow_step_count', 8)

# ---------- material helpers ----------
def mat(name, color, rough=0.85, emission=None, e_strength=0.0, alpha=None):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    bsdf = m.node_tree.nodes['Principled BSDF']
    bsdf.inputs['Base Color'].default_value = (*color, 1)
    bsdf.inputs['Roughness'].default_value = rough
    if emission is not None:
        bsdf.inputs['Emission Color'].default_value = (*emission, 1)
        bsdf.inputs['Emission Strength'].default_value = e_strength
    if alpha is not None:
        bsdf.inputs['Alpha'].default_value = alpha
        m.blend_method = 'BLEND'
    return m

def mat_noise(name, c1, c2, scale=7.0, mix=0.16, rough=0.95):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    bsdf = nt.nodes['Principled BSDF']
    tex = nt.nodes.new('ShaderNodeTexNoise'); tex.inputs['Scale'].default_value = scale
    ramp = nt.nodes.new('ShaderNodeValToRGB')
    ramp.color_ramp.elements[0].color = (*c1, 1)
    ramp.color_ramp.elements[1].color = (*c2, 1)
    mixn = nt.nodes.new('ShaderNodeMixRGB'); mixn.blend_type = 'MIX'
    mixn.inputs[0].default_value = mix
    mixn.inputs[1].default_value = (*c1, 1)
    nt.links.new(tex.outputs['Fac'], ramp.inputs['Fac'])
    nt.links.new(ramp.outputs['Color'], mixn.inputs[2])
    nt.links.new(mixn.outputs['Color'], bsdf.inputs['Base Color'])
    bsdf.inputs['Roughness'].default_value = rough
    return m

def mat_brick(name, c1, c2, scale=3.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    bsdf = nt.nodes['Principled BSDF']
    coord = nt.nodes.new('ShaderNodeTexCoord')
    mapping = nt.nodes.new('ShaderNodeMapping')
    mapping.inputs['Scale'].default_value = (scale, scale, scale)
    brick = nt.nodes.new('ShaderNodeTexBrick')
    brick.inputs['Color1'].default_value = (*c1, 1)
    brick.inputs['Color2'].default_value = (*c2, 1)
    brick.inputs['Mortar'].default_value = (0.45, 0.30, 0.24, 1)
    brick.inputs['Scale'].default_value = 6.0
    brick.inputs['Mortar Size'].default_value = 0.02
    brick.inputs['Brick Width'].default_value = 0.32
    brick.inputs['Row Height'].default_value = 0.11
    nt.links.new(coord.outputs['Object'], mapping.inputs['Vector'])
    nt.links.new(mapping.outputs['Vector'], brick.inputs['Vector'])
    nt.links.new(brick.outputs['Color'], bsdf.inputs['Base Color'])
    nt.links.new(brick.outputs['Fac'], bsdf.inputs['Roughness'])
    bsdf.inputs['Roughness'].default_value = 0.9
    return m

def mat_tiles(name, c1, c2, scale=3.0):
    """Genteng berbaris: pola bata rapat dibaca sebagai baris genteng."""
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    bsdf = nt.nodes['Principled BSDF']
    coord = nt.nodes.new('ShaderNodeTexCoord')
    mapping = nt.nodes.new('ShaderNodeMapping')
    # Rotasi 90°: bubungan atap prisma berjalan searah Y, jadi baris pola bata
    # harus ditumpuk sepanjang X (menuruni lereng), bukan sepanjang Y.
    mapping.inputs['Rotation'].default_value = (0, 0, math.radians(90))
    mapping.inputs['Scale'].default_value = (scale * 0.9, scale * 0.45, scale * 0.45)
    brick = nt.nodes.new('ShaderNodeTexBrick')
    brick.inputs['Color1'].default_value = (*c1, 1)
    brick.inputs['Color2'].default_value = (*c2, 1)
    brick.inputs['Mortar'].default_value = (0.30, 0.16, 0.11, 1)
    brick.inputs['Scale'].default_value = 1.6
    brick.inputs['Mortar Size'].default_value = 0.03
    brick.inputs['Brick Width'].default_value = 0.55
    brick.inputs['Row Height'].default_value = 0.14
    try:
        brick.offset = 0.5; brick.offset_frequency = 1
    except Exception:
        pass
    if 'Offset' in brick.inputs:
        brick.inputs['Offset'].default_value = 0.5
    noise = nt.nodes.new('ShaderNodeTexNoise'); noise.inputs['Scale'].default_value = 6.0
    bump = nt.nodes.new('ShaderNodeBump'); bump.inputs['Strength'].default_value = 0.35
    bump.inputs['Distance'].default_value = 0.25
    nt.links.new(coord.outputs['Generated'], mapping.inputs['Vector'])
    nt.links.new(mapping.outputs['Vector'], brick.inputs['Vector'])
    nt.links.new(brick.outputs['Color'], bsdf.inputs['Base Color'])
    nt.links.new(noise.outputs['Fac'], bump.inputs['Height'])
    nt.links.new(bump.outputs['Normal'], bsdf.inputs['Normal'])
    bsdf.inputs['Roughness'].default_value = 0.92
    return m

def mat_wood(name, c1, c2, scale=1.4, rough=0.85):
    """Kayu berurat: gelombang pita diacak noise -> garis serat memanjang."""
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    bsdf = nt.nodes['Principled BSDF']
    coord = nt.nodes.new('ShaderNodeTexCoord')
    mapping = nt.nodes.new('ShaderNodeMapping')
    mapping.inputs['Scale'].default_value = (scale, scale, scale)
    wave = nt.nodes.new('ShaderNodeTexWave')
    wave.wave_type = 'BANDS'; wave.bands_direction = 'Z'
    wave.inputs['Scale'].default_value = 4.5
    wave.inputs['Distortion'].default_value = 3.5
    wave.inputs['Detail'].default_value = 3.0
    ramp = nt.nodes.new('ShaderNodeValToRGB')
    ramp.color_ramp.elements[0].color = (*c1, 1)
    ramp.color_ramp.elements[1].color = (*c2, 1)
    noise = nt.nodes.new('ShaderNodeTexNoise'); noise.inputs['Scale'].default_value = 5.0
    bump = nt.nodes.new('ShaderNodeBump'); bump.inputs['Strength'].default_value = 0.22
    bump.inputs['Distance'].default_value = 0.2
    nt.links.new(coord.outputs['Generated'], mapping.inputs['Vector'])
    nt.links.new(mapping.outputs['Vector'], wave.inputs['Vector'])
    nt.links.new(wave.outputs['Color'], ramp.inputs['Fac'])
    nt.links.new(ramp.outputs['Color'], bsdf.inputs['Base Color'])
    nt.links.new(noise.outputs['Fac'], bump.inputs['Height'])
    nt.links.new(bump.outputs['Normal'], bsdf.inputs['Normal'])
    bsdf.inputs['Roughness'].default_value = rough
    return m

def mat_grain(name, c1, c2, scale=9.0, mix=0.3, bump_s=0.25, patches=None,
              map_scale=(1, 1, 1)):
    """Noise warna + bump butiran. map_scale mengkompensasi bidang panjang
    (koordinat Generated ternormalisasi -> tanpa ini tekstur melar searah sumbu panjang)."""
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    bsdf = nt.nodes['Principled BSDF']
    coord = nt.nodes.new('ShaderNodeTexCoord')
    mapping = nt.nodes.new('ShaderNodeMapping')
    mapping.inputs['Scale'].default_value = map_scale
    nt.links.new(coord.outputs['Generated'], mapping.inputs['Vector'])
    tex = nt.nodes.new('ShaderNodeTexNoise'); tex.inputs['Scale'].default_value = scale
    ramp = nt.nodes.new('ShaderNodeValToRGB')
    ramp.color_ramp.elements[0].color = (*c1, 1)
    ramp.color_ramp.elements[1].color = (*c2, 1)
    mixn = nt.nodes.new('ShaderNodeMixRGB'); mixn.blend_type = 'MIX'
    mixn.inputs[0].default_value = mix
    mixn.inputs[1].default_value = (*c1, 1)
    nt.links.new(mapping.outputs['Vector'], tex.inputs['Vector'])
    nt.links.new(tex.outputs['Fac'], ramp.inputs['Fac'])
    nt.links.new(ramp.outputs['Color'], mixn.inputs[2])
    out = mixn.outputs['Color']
    if patches is not None:
        pn = nt.nodes.new('ShaderNodeTexNoise'); pn.inputs['Scale'].default_value = patches[1]
        pm = nt.nodes.new('ShaderNodeMixRGB'); pm.blend_type = 'MIX'
        pm.inputs[2].default_value = (*patches[0], 1)
        nt.links.new(pn.outputs['Fac'], pm.inputs[0])
        nt.links.new(out, pm.inputs[1])
        out = pm.outputs['Color']
    nt.links.new(out, bsdf.inputs['Base Color'])
    bnoise = nt.nodes.new('ShaderNodeTexNoise'); bnoise.inputs['Scale'].default_value = scale * 5.0
    bump = nt.nodes.new('ShaderNodeBump'); bump.inputs['Strength'].default_value = bump_s
    bump.inputs['Distance'].default_value = 0.15
    nt.links.new(mapping.outputs['Vector'], bnoise.inputs['Vector'])
    nt.links.new(bnoise.outputs['Fac'], bump.inputs['Height'])
    nt.links.new(bump.outputs['Normal'], bsdf.inputs['Normal'])
    bsdf.inputs['Roughness'].default_value = 0.95
    return m

def mat_image(name, path, alpha=False):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    bsdf = nt.nodes['Principled BSDF']
    tex = nt.nodes.new('ShaderNodeTexImage')
    tex.image = bpy.data.images.load(path)
    nt.links.new(tex.outputs['Color'], bsdf.inputs['Base Color'])
    if alpha:
        nt.links.new(tex.outputs['Alpha'], bsdf.inputs['Alpha'])
        m.blend_method = 'BLEND'
    bsdf.inputs['Roughness'].default_value = 0.7
    return m

# palet
M = {
    'road':   mat_grain('road', (0.58, 0.49, 0.37), (0.47, 0.39, 0.29), 6, 0.3, 0.18, map_scale=(1, 7.2, 1)),
    'walk':   mat_grain('walk', (0.74, 0.67, 0.55), (0.63, 0.56, 0.45), 6, 0.25, 0.15, map_scale=(1, 35, 1)),
    'grass':  mat_grain('grass', (0.12, 0.56, 0.11), (0.16, 0.62, 0.13), 8, 0.4, 0.15, patches=((0.30, 0.66, 0.16), 1.6)),
    'window': mat('window', (0.13, 0.20, 0.30), 0.25),
    'wall_w': mat_grain('wall_w', (0.97, 0.94, 0.88), (0.93, 0.89, 0.82), 7, 0.35, 0.10),
    'wall_c': mat('wall_c', (0.97, 0.85, 0.62)),
    'wall_b': mat('wall_b', (0.64, 0.79, 0.95)),
    'roof':   mat_tiles('roof', (0.76, 0.27, 0.09), (0.62, 0.20, 0.07)),
    'wood':   mat_wood('wood', (0.34, 0.21, 0.11), (0.52, 0.36, 0.20)),
    'wood_l': mat_wood('wood_l', (0.52, 0.36, 0.19), (0.70, 0.52, 0.31)),
    'pole':   mat('pole', (0.15, 0.13, 0.11), 0.9),
    'black':  mat('black', (0.05, 0.05, 0.06), 0.6),
    'white':  mat('white', (0.96, 0.96, 0.97), 0.5),
    'teal':   mat_wood('teal', (0.03, 0.48, 0.45), (0.07, 0.62, 0.58), rough=0.7),
    'orange': mat('orange', (0.95, 0.36, 0.12)),
    'red':    mat('red', (0.88, 0.16, 0.14)),
    'green1': mat('green1', (0.22, 0.72, 0.18)),
    'green2': mat('green2', (0.14, 0.58, 0.15)),
    'skin':   mat('skin', (0.96, 0.78, 0.60), 0.65),
    'shirt_t': mat('shirt_t', (0.05, 0.72, 0.62)),
    'shirt_r': mat('shirt_r', (0.92, 0.26, 0.20)),
    'hijab':  mat('hijab', (0.98, 0.80, 0.16)),
    'pants':  mat('pants', (0.16, 0.20, 0.30)),
    'cloud':  mat('cloud', (1, 1, 1), 1.0, emission=(1, 1, 1), e_strength=0.45),
    'led':    mat('led', (0.1, 0.9, 0.3), 0.4, emission=(0.1, 0.95, 0.3), e_strength=2.0),
    'glass':  mat('glass', (0.75, 0.88, 0.95), 0.12, alpha=0.35),
    'roof2':  mat_tiles('roof2', (0.42, 0.34, 0.29), (0.33, 0.26, 0.22)),
    'cream':  mat('cream', (0.87, 0.80, 0.66), 0.95),
    'grey':   mat('grey', (0.45, 0.46, 0.48), 0.8),
    'terra':  mat('terra', (0.62, 0.30, 0.16), 0.9),
    'lamp':   mat('lamp', (1.0, 0.80, 0.45), 0.4, emission=(1.0, 0.72, 0.32), e_strength=1.6),
}

# ---------- bangun helpers ----------
def link(obj, material=None, smooth=True):
    scene.collection.objects.link(obj)
    if material: obj.data.materials.append(material)
    if smooth and obj.type == 'MESH':
        for p in obj.data.polygons: p.use_smooth = True
    return obj

def box(name, loc, dims, material, bevel=0.0, rot=(0, 0, 0)):
    """dims = ukuran penuh (x, y, z)."""
    bpy.ops.mesh.primitive_cube_add(location=loc, rotation=rot)
    o = bpy.context.object; o.name = name
    o.dimensions = dims
    bpy.ops.object.transform_apply(scale=True)
    if material: o.data.materials.append(material)
    if bevel > 0:
        mod = o.modifiers.new('bev', 'BEVEL'); mod.width = bevel; mod.segments = 3
    return o

def cyl(name, loc, r, depth, material, rot=(0, 0, 0), vertices=24):
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices, radius=r, depth=depth,
                                        location=loc, rotation=rot)
    o = bpy.context.object; o.name = name
    if material: o.data.materials.append(material)
    for p in o.data.polygons: p.use_smooth = True
    return o

def sph(name, loc, r, material, scale=(1, 1, 1)):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=28, ring_count=18, radius=r, location=loc)
    o = bpy.context.object; o.name = name; o.scale = scale
    if material: o.data.materials.append(material)
    for p in o.data.polygons: p.use_smooth = True
    return o

def empty(name, loc):
    o = bpy.data.objects.new(name, None)
    o.location = loc
    scene.collection.objects.link(o)
    return o

def prism_roof(name, loc, w, d, h, material):
    """Atap pelana: prisma segitiga manual."""
    hw, hd = w / 2, d / 2
    # 4 sudut alas + 2 titik punggung (depan/belakang)
    verts = [(-hw, -hd, 0), (hw, -hd, 0), (hw, hd, 0), (-hw, hd, 0),
             (0, -hd, h), (0, hd, h)]
    faces = [(1, 2, 5, 4), (0, 3, 5, 4), (0, 1, 4), (2, 3, 5), (0, 3, 2, 1)]
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts, [], faces); me.update()
    o = bpy.data.objects.new(name, me)
    o.location = loc
    scene.collection.objects.link(o)
    o.data.materials.append(material)
    return o

def cable(name, p0, p1, sag=0.45, r=0.016):
    mid = (Vector(p0) + Vector(p1)) / 2; mid.z -= sag
    cu = bpy.data.curves.new(name, 'CURVE')
    cu.dimensions = '3D'; cu.bevel_depth = r; cu.bevel_resolution = 2
    spl = cu.splines.new('BEZIER'); spl.bezier_points.add(1)
    spl.bezier_points[0].co = p0; spl.bezier_points[0].handle_right = mid
    spl.bezier_points[1].co = p1; spl.bezier_points[1].handle_left = mid
    o = bpy.data.objects.new(name, cu)
    scene.collection.objects.link(o)
    o.data.materials.append(M['black'])
    return o

# ============================================================
# LINGKUNGAN — gang kampung (jalan membujur sumbu Y)
# ============================================================
def plane(name, loc, size, material):
    bpy.ops.mesh.primitive_plane_add(size=1, location=loc)
    o = bpy.context.object; o.name = name; o.dimensions = (size[0], size[1], 0)
    bpy.ops.object.transform_apply(scale=True)
    if material: o.data.materials.append(material)
    return o

plane('ground_far', (0, 26, -0.02), (90, 90), M['grass'])
plane('road', (0, 4, 0), (6.4, 46), M['road'])
plane('walk_r', (3.85, 4, 0.012), (1.3, 46), M['walk'])
plane('walk_l', (-3.85, 4, 0.012), (1.3, 46), M['walk'])

def house(x, y, w, d, h, wall, flip=False, roof_mat=None):
    g = empty(f'house_{x}_{y}', (x, y, 0))
    # fondasi/skirting abu di kaki dinding (biar rumah terasa menapak)
    box('found', (x, y, 0.16), (w + 0.10, d + 0.10, 0.32), M['grey'])
    b = box('wall', (x, y, h / 2 + 0.1), (w, d, h), wall)
    r = prism_roof('roof', (x, y, h + 0.1), w + 0.5, d + 0.5, h * 0.52, roof_mat or M['roof'])
    # bubungan atap
    box('ridge', (x, y, h + 0.1 + h * 0.52 + 0.03), (0.20, d + 0.56, 0.10), M['wood'])
    # pintu + jendela di sisi menghadap jalan
    face = 1 if x < 0 else -1
    fx = x + face * (w / 2 + 0.01)
    box('door', (fx, y - d * 0.18, 0.95), (0.06, 0.8, 1.7), M['wood'])
    box('step', (x + face * (w / 2 + 0.22), y - d * 0.18, 0.06), (0.46, 1.0, 0.12), M['walk'])
    # jendela: kusen putih + kaca + palang silang
    wy = y + d * 0.22
    box('wframe', (fx, wy, 1.45), (0.05, 1.02, 1.02), M['white'])
    box('win', (fx + face * 0.02, wy, 1.45), (0.06, 0.9, 0.9), M['window'])
    box('wmull_v', (fx + face * 0.045, wy, 1.45), (0.03, 0.06, 0.9), M['white'])
    box('wmull_h', (fx + face * 0.045, wy, 1.45), (0.03, 0.9, 0.06), M['white'])
    return g

house(-5.6, -3.5, 3.6, 4.6, 3.0, M['wall_c'])
house(-5.8, 3.5, 3.8, 5.0, 3.4, M['wall_w'], roof_mat=M['roof2'])
house(-5.6, 11.0, 3.6, 4.6, 3.0, M['wall_b'])
house(5.9, 6.5, 3.8, 5.2, 3.3, M['wall_w'])
house(5.7, 14.0, 3.6, 4.8, 3.0, mat_brick('brick1', (0.62, 0.30, 0.20), (0.52, 0.24, 0.16)), roof_mat=M['roof2'])
house(-5.7, 18.5, 3.7, 4.8, 3.2, M['wall_w'])
house(5.8, 21.0, 3.7, 4.8, 3.1, M['wall_b'])

def fence_run(x, y0, y1):
    n = int((y1 - y0) / 1.1)
    for i in range(n + 1):
        y = y0 + i * 1.1
        box('fpost', (x, y, 0.55), (0.14, 0.14, 1.1), M['white'], bevel=0.02)
    for z in (0.42, 0.82):
        box('frail', (x, (y0 + y1) / 2, z), (0.07, y1 - y0, 0.09), M['white'])

fence_run(-4.35, -7.5, 20)
fence_run(4.35, 3.0, 20)
fence_run(4.35, -7.5, -2.2)

def tree(x, y, s=1.0):
    cyl('trunk', (x, y, 0.7 * s), 0.09 * s, 1.4 * s, M['wood'])
    sph('leaf1', (x, y, 1.9 * s), 0.95 * s, M['green1'])
    sph('leaf2', (x + 0.55 * s, y + 0.2 * s, 1.55 * s), 0.7 * s, M['green2'])
    sph('leaf3', (x - 0.5 * s, y - 0.15 * s, 1.6 * s), 0.65 * s, M['green1'])
    sph('leaf4', (x + 0.1 * s, y - 0.4 * s, 2.35 * s), 0.6 * s, M['green2'])

tree(-4.6, -6.2, 1.15); tree(4.7, 9.5, 1.3); tree(-4.7, 8.0, 1.0)
tree(4.6, 17.5, 1.2); tree(-4.6, 15.5, 0.9)

# tiang listrik + kabel (hero pole di kanan depan: router nempel di sana)
POLES = [(-3.1, -6.5), (3.0, -3.2), (-3.1, 2.5), (3.0, 6.0), (-3.1, 11.5), (3.0, 15.0)]
for i, (px, py) in enumerate(POLES):
    cyl(f'pole{i}', (px, py, 3.1), 0.09, 6.2, M['pole'])
    box(f'cross{i}', (px, py, 5.6), (1.3, 0.09, 0.12), M['pole'])
for i in range(len(POLES) - 2):
    (x0, y0), (x1, y1) = POLES[i], POLES[i + 2]
    cable(f'cab{i}a', (x0 - 0.55, y0, 5.6), (x1 - 0.55, y1, 5.6), sag=0.5)
    cable(f'cab{i}b', (x0 + 0.55, y0, 5.6), (x1 + 0.55, y1, 5.6), sag=0.65)
cable('drop1', (3.0, -3.2, 5.2), (5.2, 1.5, 3.4), sag=0.4)   # drop ke rumah kanan
cable('drop2', (-3.1, 2.5, 5.2), (-5.0, 3.5, 3.6), sag=0.4)  # drop ke rumah kiri

# masjid jauh (siluet kampung)
box('mosq', (10.5, 30, 2.2), (6.5, 6.5, 4.4), M['white'])
sph('dome', (10.5, 30, 5.1), 2.3, M['teal'], scale=(1, 1, 0.75))
cyl('minaret', (14.6, 30, 4.4), 0.42, 8.8, M['white'])
sph('minaret_top', (14.6, 30, 9.1), 0.62, M['teal'], scale=(1, 1, 0.8))

# awan kartun pipih
def cloud(x, y, z, s=1.0):
    for dx, dy, r in ((0, 0, 1.1), (1.0, 0.2, 0.8), (-1.0, 0.15, 0.75), (0.3, -0.3, 0.7)):
        o = sph('cloud', (x + dx * s, y + dy * s, z), r * s, M['cloud'], scale=(1, 1, 0.45))
        o.rotation_euler = (0, 0, 0)
    return o

clouds = []
for cx, cy, cz, cs in ((-9, 18, 13, 1.6), (7, 26, 15, 2.1), (-4, 34, 14, 1.4), (12, 8, 13.5, 1.2)):
    g = empty(f'cloudg_{cx}', (cx, cy, cz))
    for dx, dy, r in ((0, 0, 1.1), (1.0, 0.2, 0.8), (-1.0, 0.15, 0.75), (0.3, -0.3, 0.7)):
        o = sph('cloudp', (cx + dx * cs, cy + dy * cs, cz), r * cs, M['cloud'], scale=(1, 1, 0.45))
    clouds.append((cx, g))

# ============================================================
# WARUNG (kanan depan) — papan nama bertekstur gambar
# ============================================================
WX, WY = 4.6, -1.6
box('w_counter', (WX, WY, 0.55), (2.6, 1.1, 1.1), M['teal'], bevel=0.03)
box('w_top', (WX, WY, 1.13), (2.7, 1.2, 0.06), M['wood_l'])
for dx in (-1.2, 1.2):
    box('w_post', (WX + dx, WY - 0.5, 1.55), (0.12, 0.12, 3.1), M['wood'])
    box('w_post2', (WX + dx, WY + 0.55, 1.55), (0.12, 0.12, 3.1), M['wood'])
box('w_roof', (WX, WY, 3.16), (3.1, 1.9, 0.09), M['orange'], bevel=0.02)
# papan nama: kotak tipis, material gambar HANYA di muka -X (arah jalan)
sign_mat = mat_image('sign', os.path.join(HERE, 'sign_warung.png'))
sign = box('w_sign', (WX - 1.60, WY, 3.62), (0.07, 2.9, 1.09), M['black'], bevel=0.015)
sign.data.materials.append(sign_mat)
# UV muka -X ditulis manual: transform_apply mengecilkan UV kubus secara
# proporsional terhadap skala — tanpa ini tekstur cuma kepakai seiris.
_uvl = sign.data.uv_layers.active.data
_ys = [v.co.y for v in sign.data.vertices]; _zs = [v.co.z for v in sign.data.vertices]
_ymin, _ymax, _zmin, _zmax = min(_ys), max(_ys), min(_zs), max(_zs)
for p in sign.data.polygons:
    if p.normal.x < -0.9:
        p.material_index = 1
        for li in p.loop_indices:
            v = sign.data.vertices[sign.data.loops[li].vertex_index].co
            _uvl[li].uv = (1 - (v.y - _ymin) / (_ymax - _ymin), (v.z - _zmin) / (_zmax - _zmin))
# sachet renteng di mulut warung
sachet_cols = [(0.92, 0.30, 0.25), (0.25, 0.55, 0.90), (0.30, 0.75, 0.35),
               (0.95, 0.75, 0.20), (0.60, 0.35, 0.85)]
for i, c in enumerate(sachet_cols):
    sm = mat(f'sachet{i}', c, 0.6)
    for j in range(4):
        box(f'sac{i}_{j}', (WX - 0.62, WY - 0.44 + i * 0.22, 2.62 - j * 0.34),
            (0.05, 0.19, 0.30), sm, bevel=0.015)
# bangku + kucing oren
box('bench', (WX - 1.15, WY + 1.15, 0.28), (0.5, 1.7, 0.09), M['wood_l'], bevel=0.02)
for dz in (-0.7, 0.7):
    box('bench_leg', (WX - 1.15, WY + 1.15 + dz, 0.12), (0.42, 0.09, 0.24), M['wood'])
cat = empty('cat', (WX - 1.15, WY + 1.0, 0.36))
sph('cat_body', (WX - 1.15, WY + 1.0, 0.44), 0.16, M['orange'], scale=(1.5, 0.95, 0.8))
sph('cat_head', (WX - 1.32, WY + 0.72, 0.47), 0.105, M['orange'])
for s_ in (-1, 1):
    bpy.ops.mesh.primitive_cone_add(radius1=0.035, radius2=0.0, depth=0.11,
                                    location=(WX - 1.32 + 0.055 * s_, WY + 0.72, 0.58))
    bpy.context.object.data.materials.append(M['orange'])
cyl('cat_tail', (WX - 1.02, WY + 1.28, 0.42), 0.028, 0.3, M['orange'], rot=(math.radians(65), 0, math.radians(-30)))
# router kecil di meja warung
box('w_router', (WX - 0.3, WY + 0.28, 1.24), (0.52, 0.34, 0.07), M['white'], bevel=0.025)
for dx in (-0.18, 0.18):
    cyl('w_ant', (WX - 0.3 + dx, WY + 0.42, 1.42), 0.016, 0.3, M['black'])
for i in range(3):
    sph('w_led', (WX - 0.44, WY + 0.10, 1.245), 0.014, M['led'])

# ============================================================
# ROUTER HERO di tiang (3.0, -3.2) + cincin sinyal animasi
# ============================================================
box('r_mount', (2.93, -3.2, 3.05), (0.16, 0.1, 0.5), M['pole'])
box('router', (2.80, -3.2, 3.1), (0.13, 0.58, 0.40), M['white'], bevel=0.03)
for dy in (-0.19, 0.19):
    cyl('r_ant', (2.80, -3.2 + dy, 3.52), 0.017, 0.46, M['black'])
for i in range(3):
    sph('r_led', (2.725, -3.34 + i * 0.14, 3.16), 0.016, M['led'])

rings = []
for i in range(3):
    ring_mat = mat(f'ring{i}', (0.45, 0.85, 1.0), 0.3,
                   emission=(0.45, 0.85, 1.0), e_strength=0.7, alpha=0.0)
    bpy.ops.mesh.primitive_torus_add(major_radius=0.34, minor_radius=0.014,
                                     major_segments=40, minor_segments=8,
                                     location=(2.72, -3.2, 3.1),
                                     rotation=(0, math.radians(90), 0))
    r = bpy.context.object; r.name = f'ring{i}'
    r.data.materials.append(ring_mat)
    rings.append((r, ring_mat))

for ri, (r, ring_mat) in enumerate(rings):
    alpha_in = ring_mat.node_tree.nodes['Principled BSDF'].inputs['Alpha']
    for cyc in range(3):
        f0 = 1 + cyc * 72 + ri * 24
        f1 = f0 + 54
        if f1 > 245: break
        r.scale = (0.35, 0.35, 0.35); r.keyframe_insert('scale', frame=f0)
        alpha_in.default_value = 0.85; alpha_in.keyframe_insert('default_value', frame=f0)
        r.scale = (2.3, 2.3, 2.3); r.keyframe_insert('scale', frame=f1)
        alpha_in.default_value = 0.0; alpha_in.keyframe_insert('default_value', frame=f1)

# ============================================================
# KARAKTER CHIBI — menghadap -Y (ke kamera), offset diputar rot_z
# ============================================================
def chibi(name, loc, shirt, pants_c, rot_z=0.0, hijab_c=None, hair=True, phone=False):
    cz, sz = math.cos(rot_z), math.sin(rot_z)
    def off(lx, ly):
        return (loc[0] + lx * cz - ly * sz, loc[1] + lx * sz + ly * cz)
    parts = []
    def reg(o): parts.append(o); return o
    for s_ in (-1, 1):
        x, y = off(0.095 * s_, 0)
        reg(cyl(f'{name}_leg', (x, y, 0.19), 0.055, 0.30, pants_c))
        x, y = off(0.095 * s_, -0.03)
        reg(box(f'{name}_shoe', (x, y, 0.045), (0.13, 0.23, 0.09), M['black'], bevel=0.03))
    reg(box(f'{name}_body', (loc[0], loc[1], 0.63), (0.52, 0.34, 0.56), shirt, bevel=0.10))
    reg(cyl(f'{name}_neck', (loc[0], loc[1], 0.94), 0.07, 0.14, M['skin']))
    # lengan (bola lonjong) + tangan
    for s_ in (-1, 1):
        if phone and s_ > 0:
            x, y = off(0.30, -0.13)
            a = reg(sph(f'{name}_armR', (x, y, 0.80), 0.155, shirt, scale=(0.36, 0.36, 1.05)))
            a.rotation_euler = (math.radians(-38), 0, 0)
            x, y = off(0.31, -0.26)
            reg(sph(f'{name}_handR', (x, y, 0.94), 0.052, M['skin']))
            x, y = off(0.31, -0.285)
            ph = reg(box(f'{name}_phone', (x, y, 1.0), (0.10, 0.02, 0.18), M['black'], bevel=0.008))
            ph.rotation_euler = (math.radians(-18), 0, 0)
        else:
            x, y = off(0.315 * s_, 0)
            reg(sph(f'{name}_arm', (x, y, 0.60), 0.155, shirt, scale=(0.36, 0.36, 1.1)))
            x, y = off(0.315 * s_, -0.01)
            reg(sph(f'{name}_hand', (x, y, 0.40), 0.052, M['skin']))
    # kepala + wajah
    reg(sph(f'{name}_head', (loc[0], loc[1], 1.14), 0.26, M['skin']))
    fx, fy = off(0, -0.238)
    for s_ in (-1, 1):
        x, y = off(0.095 * s_, -0.228)
        reg(sph(f'{name}_eye', (x, y, 1.185), 0.027, M['black'], scale=(1, 0.5, 1.35)))
    # mulut: torus separuh masuk kepala -> busur yang nongol = ekspresi
    bpy.ops.mesh.primitive_torus_add(major_radius=0.042, minor_radius=0.009,
                                     major_segments=20, minor_segments=6,
                                     location=(fx, fy, 1.078),
                                     rotation=(math.radians(90), 0, rot_z))
    mo = bpy.context.object; mo.name = f'{name}_mouth'
    mo.data.materials.append(M['black']); parts.append(mo)
    if hijab_c is not None:
        x, y = off(0, 0.045)
        reg(sph(f'{name}_hijab', (x, y, 1.17), 0.285, hijab_c, scale=(1, 1, 1.02)))
        bpy.ops.mesh.primitive_cone_add(vertices=24, radius1=0.30, radius2=0.205,
                                        depth=0.34, location=(loc[0], loc[1], 0.94))
        dr = bpy.context.object; dr.name = f'{name}_drape'
        dr.data.materials.append(hijab_c)
        for p in dr.data.polygons: p.use_smooth = True
        parts.append(dr)
    elif hair:
        x, y = off(0, 0.035)
        reg(sph(f'{name}_hair', (x, y, 1.205), 0.263, M['black'], scale=(1, 1, 0.80)))
    return parts

charA = chibi('wargaA', (-1.35, -3.4, 0), M['shirt_t'], M['pants'], phone=True)
charB = chibi('wargaB', (3.25, 0.9, 0), M['shirt_r'], M['pants'], rot_z=math.radians(-90), hijab_c=M['hijab'], hair=False)

# gelembung ikon no-signal di atas wargaA (bidang bertekstur, menghadap -Y)
icon_mat = mat_image('icon', os.path.join(HERE, 'icon_nosignal.png'), alpha=True)
bpy.ops.mesh.primitive_plane_add(size=0.55, location=(-1.35, -3.5, 2.02),
                                 rotation=(math.radians(90), 0, 0))
icon = bpy.context.object; icon.name = 'icon_bubble'
icon.data.materials.append(icon_mat)

# ============================================================
# ANIMASI KARAKTER (PR #2) — bob idle + akting per karakter.
# Semua keyframe ditulis dari posisi/rotasi dasar tiap part, jadi
# bob dan gerakan kepala/lengan berbagi fcurve location yang sama.
# ============================================================
from mathutils import Matrix, Vector

def _track(keys):
    """Interpolasi halus (smoothstep) antar (frame, nilai)."""
    def at(f):
        if f <= keys[0][0]: return keys[0][1]
        for (f0, v0), (f1, v1) in zip(keys, keys[1:]):
            if f <= f1:
                t = (f - f0) / max(1, f1 - f0)
                t = t * t * (3 - 2 * t)
                return v0 + (v1 - v0) * t
        return keys[-1][1]
    return at

def _group(prefix, subs, exclude=()):
    return [o for o in bpy.data.objects
            if o.name.startswith(prefix)
            and any(s in o.name for s in subs)
            and not any(e in o.name for e in exclude)]

def _pivot_pose(base_loc, base_euler, pivot, R):
    loc = pivot + R @ (base_loc - pivot)
    rot = (R.to_3x3() @ base_euler.to_matrix()).to_euler()
    return loc, rot

def animate_char(parts, prefix, loc, phase, head_pitch, head_yaw,
                 pitch_axis, phone_arm=False, tap_shoe=False):
    head = _group(prefix, ('_head', '_eye', '_mouth', '_hair', '_hijab'))
    phone = _group(prefix, ('_armR', '_handR', '_phone')) if phone_arm else []
    shoe = _group(prefix, ('_shoe',))
    shoe_r = shoe[1] if (tap_shoe and len(shoe) > 1) else None
    pivot = Vector((loc[0], loc[1], 0.98))
    spivot = Vector((loc[0] + 0.30, loc[1] - 0.02, 0.90))
    base = {o.name: (o.location.copy(), o.rotation_euler.copy()) for o in parts}
    for f in range(1, 242, 4):
        dz = 0.022 * math.sin(2 * math.pi * f / 52 + phase)
        p = head_pitch(f)
        if phone_arm and p > 8:  # angguk kecil pas scroll HP
            p += 3.5 * math.sin(2 * math.pi * f / 18)
        R = (Matrix.Rotation(math.radians(head_yaw(f)), 4, 'Z')
             @ Matrix.Rotation(math.radians(p), 4, pitch_axis))
        Ra = Matrix.Rotation(math.radians((19 - head_pitch(f)) * 1.1), 4, pitch_axis)
        for o in parts:
            bl, be = base[o.name]
            nl, nr = bl, be
            if o in head:
                nl, nr = _pivot_pose(bl, be, pivot, R)
            elif o in phone:
                nl, nr = _pivot_pose(bl, be, spivot, Ra)
            o.location = (nl.x, nl.y, nl.z + dz)
            o.keyframe_insert('location', frame=f)
            if o in head or o in phone:
                o.rotation_euler = nr
                o.keyframe_insert('rotation_euler', frame=f)
            if shoe_r is not None and o is shoe_r:
                tap = 0.0
                if 96 <= f <= 144:
                    tap = math.radians(11) * max(0.0, math.sin(2 * math.pi * f / 9))
                o.rotation_euler = (be.x + tap, be.y, be.z)
                o.keyframe_insert('rotation_euler', frame=f)
    for o in parts:
        bl, be = base[o.name]
        o.location = bl; o.rotation_euler = be

# wargaA: cek HP (nunduk) -> angkat kepala + geleng frustrasi -> nunduk lagi
pitchA = _track([(1, 17), (50, 22), (62, 0), (86, 0), (100, 20), (140, 23),
                 (152, 0), (172, 0), (186, 19), (240, 19)])
yawA = _track([(1, 0), (62, 0), (66, -16), (70, 16), (74, -16), (78, 12),
               (82, 0), (152, 0), (156, -13), (160, 13), (164, -9), (168, 0), (240, 0)])
animate_char(charA, 'wargaA', (-1.35, -3.4, 0), 0.0, pitchA, yawA, 'X',
             phone_arm=True, tap_shoe=True)

# wargaB (ibu warung): noleh sepanjang jalan pelan + satu anggukan menyapa
pitchB = _track([(1, 5), (100, 5), (112, 17), (124, 5), (240, 5)])
yawB = _track([(1, 0), (40, -20), (80, -20), (110, 16), (150, 16),
               (185, -12), (240, -12)])
animate_char(charB, 'wargaB', (3.25, 0.9, 0), 1.7, pitchB, yawB, 'Y')

# lengan kanan ibu warung: gerakan mengelap/melayani (rotasi saja)
armB = bpy.data.objects.get('wargaB_arm.001')
if armB is not None:
    be = armB.rotation_euler.copy()
    for f in range(1, 242, 4):
        armB.rotation_euler = (be.x, be.y + 0.48 * math.sin(2 * math.pi * f / 30), be.z)
        armB.keyframe_insert('rotation_euler', frame=f)
    armB.rotation_euler = be

# ekor kucing kibas pelan
tail = bpy.data.objects.get('cat_tail')
if tail is not None:
    be = tail.rotation_euler.copy()
    for f in range(1, 242, 6):
        tail.rotation_euler = (be.x, be.y, be.z + 0.48 * math.sin(2 * math.pi * f / 36))
        tail.keyframe_insert('rotation_euler', frame=f)
    tail.rotation_euler = be

# ikon ikut bob wargaA
for f in range(1, 242, 16):
    icon.location.z = 2.02 + 0.03 * math.sin(2 * math.pi * f / 52 + 0.0) + 0.02 * math.sin(2 * math.pi * f / 26)
    icon.keyframe_insert('location', frame=f)
icon.location.z = 2.02

# ============================================================
# PR #1 — POLES MODEL & SET (semua statis, tanpa keyframe)
# ============================================================
# --- Warung: dinding belakang + rak + barang dagangan (interior terbaca) ---
box('w_back', (6.04, WY, 1.52), (0.09, 2.5, 2.3), M['wood_l'])
box('w_side', (5.55, WY - 1.28, 1.30), (1.05, 0.08, 1.9), M['wood_l'])
for sz in (1.78, 2.24):
    box('w_shelf', (5.82, WY, sz), (0.34, 2.2, 0.05), M['wood'])
_goods = [(0.92, 0.30, 0.25), (0.25, 0.55, 0.90), (0.30, 0.75, 0.35), (0.95, 0.75, 0.20),
          (0.95, 0.55, 0.15), (0.60, 0.35, 0.85), (0.15, 0.70, 0.65), (0.90, 0.45, 0.60)]
_gm = [mat(f'good{i}', c, 0.55) for i, c in enumerate(_goods)]
for k in range(9):  # toples & kaleng di dua rak
    gx = 5.80 + (0.09 if k % 3 == 0 else -0.07)
    gy = WY - 0.95 + (k % 5) * 0.44
    gz = 1.78 if k < 5 else 2.24
    if k % 3 == 0:
        cyl(f'jar{k}', (gx, gy, gz + 0.10), 0.075, 0.20, M['glass'])
        cyl(f'jarf{k}', (gx, gy, gz + 0.09), 0.062, 0.15, _gm[k % len(_gm)])
    else:
        cyl(f'can{k}', (gx, gy, gz + 0.07), 0.055, 0.14, _gm[k % len(_gm)])
for k in range(4):  # botol di meja belakang counter
    cyl(f'btl{k}', (5.55 - 0.12, WY - 0.75 + k * 0.5, 1.28), 0.05, 0.24, _gm[(k + 3) % len(_gm)])
# --- Etalase kaca di atas counter: gorengan di dalamnya ---
EX, EY, EZ = WX - 0.55, WY - 0.30, 1.16
box('et_base', (EX, EY, EZ + 0.02), (0.74, 0.52, 0.04), M['wood'])
box('et_top', (EX, EY, EZ + 0.46), (0.74, 0.52, 0.04), M['wood'])
for sx in (-0.35, 0.35):
    for sy in (-0.24, 0.24):
        box('et_post', (EX + sx, EY + sy, EZ + 0.24), (0.04, 0.04, 0.44), M['wood'])
box('et_glass', (EX, EY, EZ + 0.24), (0.68, 0.46, 0.40), M['glass'])
box('et_tray', (EX, EY, EZ + 0.07), (0.60, 0.40, 0.03), M['grey'])
for k in range(10):
    sph(f'fry{k}', (EX - 0.22 + (k % 5) * 0.115, EY - 0.09 + (k // 5) * 0.18, EZ + 0.125),
        0.058, _gm[4], scale=(1, 1, 0.75))
# --- Lampu gantung warung + krat botol + karung + ember ---
cyl('w_cord', (5.0, WY, 2.86), 0.012, 0.6, M['black'])
bpy.ops.mesh.primitive_cone_add(vertices=20, radius1=0.16, radius2=0.05, depth=0.14,
                                location=(5.0, WY, 2.52))
bpy.context.object.data.materials.append(M['orange'])
sph('w_bulb', (5.0, WY, 2.44), 0.055, M['lamp'])
box('crate1', (6.0, WY + 1.52, 0.21), (0.56, 0.56, 0.42), M['red'], bevel=0.02)
box('crate2', (6.0, WY + 1.52, 0.62), (0.56, 0.56, 0.40), _gm[1], bevel=0.02)
for k in range(3):
    cyl(f'cbtl{k}', (5.86 + (k % 2) * 0.24, WY + 1.40 + (k // 2) * 0.24, 0.94), 0.045, 0.24, _gm[(k + 1) % len(_gm)])
sph('sack', (5.9, WY - 1.05, 0.26), 0.34, M['cream'], scale=(1, 1, 0.78))
cyl('bucket', (5.35, WY - 1.35, 0.19), 0.17, 0.38, _gm[5])

# --- Tiang hero: kotak sambungan + lilitan kabel + pita kuning ---
box('pole_box', (2.94, -3.2, 2.15), (0.15, 0.36, 0.46), M['grey'], bevel=0.02)
bpy.ops.mesh.primitive_torus_add(major_radius=0.115, minor_radius=0.022, major_segments=24,
                                 minor_segments=8, location=(2.90, -3.48, 2.62),
                                 rotation=(0, math.radians(90), 0))
bpy.context.object.data.materials.append(M['black'])
cyl('pole_band', (3.0, -3.2, 3.78), 0.098, 0.15, _gm[3])

# --- Motor bebek parkir di trotoar kiri depan ---
def motorbike(x, y, rot_z, body_mat):
    cz, sz = math.cos(rot_z), math.sin(rot_z)
    def off(lx, ly):
        return (x + lx * cz - ly * sz, y + lx * sz + ly * cz)
    for ly in (0.52, -0.52):  # roda depan/belakang
        wx_, wy_ = off(0, ly)
        bpy.ops.mesh.primitive_torus_add(major_radius=0.24, minor_radius=0.065,
                                         major_segments=24, minor_segments=10,
                                         location=(wx_, wy_, 0.27),
                                         rotation=(0, math.radians(90), rot_z))
        bpy.context.object.data.materials.append(M['black'])
        hx, hy = off(0, ly)
        cyl('hub', (hx, hy, 0.27), 0.085, 0.06, M['grey'], rot=(0, math.radians(90), 0))
    bx, by = off(0, -0.08)
    box('mb_body', (bx, by, 0.44), (0.30, 0.80, 0.30), body_mat, bevel=0.07, rot=(0, 0, rot_z))
    sx_, sy_ = off(0, -0.28)
    box('mb_seat', (sx_, sy_, 0.63), (0.30, 0.52, 0.11), M['black'], bevel=0.04, rot=(0, 0, rot_z))
    fx_, fy_ = off(0, 0.42)
    box('mb_shield', (fx_, fy_, 0.55), (0.32, 0.07, 0.46), body_mat, bevel=0.03,
        rot=(math.radians(-18), 0, rot_z))
    hx, hy = off(0, 0.47)
    cyl('mb_bar', (hx, hy, 0.82), 0.022, 0.44, M['black'], rot=(0, 0, math.radians(90) + rot_z))
    lx_, ly_ = off(0, 0.50)
    sph('mb_light', (lx_, ly_, 0.66), 0.055, M['lamp'])
    kx, ky = off(-0.10, -0.05)
    cyl('mb_stand', (kx, ky, 0.16), 0.018, 0.34, M['grey'], rot=(math.radians(25), math.radians(18), 0))

motorbike(-2.7, 5.5, 0.35, M['red'])

# --- Jemuran di celah antar rumah kiri (biar kelihatan kamera) ---
cyl('laundry_p1', (-3.95, -1.15, 1.27), 0.035, 2.55, M['wood'])
cyl('laundry_p2', (-3.95, 0.95, 1.27), 0.035, 2.55, M['wood'])
cable('laundry_line', (-3.95, -1.15, 2.5), (-3.95, 0.95, 2.5), sag=0.08, r=0.012)
for i, (cy, cm) in enumerate(((-0.62, M['red']), (-0.05, M['white']), (0.55, _gm[1]))):
    box(f'cloth{i}', (-3.95, cy, 2.06), (0.05, 0.52, 0.78), cm, rot=(0, 0, 0.03 * (i - 1)))

# --- Pot tanaman + semak di sepanjang pagar ---
def pot(x, y):
    bpy.ops.mesh.primitive_cone_add(vertices=16, radius1=0.13, radius2=0.19, depth=0.30,
                                    location=(x, y, 0.15))
    bpy.context.object.data.materials.append(M['terra'])
    sph('potleaf', (x, y, 0.48), 0.24, M['green2'], scale=(1, 1, 0.8))

pot(4.30, -0.35); pot(4.30, 2.3); pot(-4.30, -2.6); pot(-4.30, 6.4); pot(4.30, 12.6)
for bx, by in ((-4.25, 1.2), (4.25, 8.6), (-4.25, 13.8)):
    sph('bush', (bx, by, 0.22), 0.34, M['green2'], scale=(1.15, 1, 0.65))

# --- Marka jalan putus-putus (bagian dekat kamera, warna pudar) ---
_dashm = mat('dash', (0.72, 0.70, 0.64), 0.95)
for k in range(5):
    box(f'dash{k}', (0, -9.5 + k * 2.3, 0.006), (0.14, 0.9, 0.012), _dashm)

# ============================================================
# KAMERA — dolly masuk gang, target geser ke router hero
# ============================================================
cam_data = bpy.data.cameras.new('cam'); cam_data.lens = 30
cam = bpy.data.objects.new('cam', cam_data)
scene.collection.objects.link(cam)
scene.camera = cam
target = empty('cam_target', (0, 0, 1.1))
con = cam.constraints.new('TRACK_TO')
con.target = target; con.track_axis = 'TRACK_NEGATIVE_Z'; con.up_axis = 'UP_Y'
cam.location = (0.0, -12.5, 2.6); cam.keyframe_insert('location', frame=1)
target.location = (0, 0, 1.1); target.keyframe_insert('location', frame=1)
cam.location = (0.1, -9.2, 2.05); cam.keyframe_insert('location', frame=120)
target.location = (0.6, -2.8, 1.8); target.keyframe_insert('location', frame=120)
cam.location = (0.55, -6.6, 1.65); cam.keyframe_insert('location', frame=240)
target.location = (2.45, -2.95, 2.55); target.keyframe_insert('location', frame=240)
# Interpolasi keyframe kamera: default Blender memang BEZIER, jadi blok ini
# kosmetik — dibungkus try agar perbedaan API actions antar versi (4.0 vs 5.0)
# tidak pernah menggagalkan render.
try:
    def _action_fcurves(action):
        if hasattr(action, 'fcurves'):
            return list(action.fcurves)
        fcs = []
        for layer in action.layers:
            for strip in layer.strips:
                bag = getattr(strip, 'channelbag', None)
                if bag is not None and hasattr(bag, 'fcurves'):
                    fcs.extend(bag.fcurves)
        return fcs

    for _obj in (cam, target):
        for fc in _action_fcurves(_obj.animation_data.action):
            for kp in fc.keyframe_points:
                kp.interpolation = 'BEZIER'
except Exception as e:
    print('interp kamera dilewati (default BEZIER):', e)

# ---------- render ----------
if MODE == 'still':
    argv = sys.argv[sys.argv.index('--') + 1:]
    fr = int(argv[1]) if len(argv) > 1 else 100
    scene.frame_set(fr)
    scene.render.filepath = os.path.join(HERE, f'still{fr}.png')
    bpy.ops.render.render(write_still=True)
    print('STILL DONE', fr)
else:
    # mode anim: argumen opsional sesudahnya = frame awal & akhir (buat chunking farm)
    argv = sys.argv[sys.argv.index('--') + 1:]
    if len(argv) > 2:
        scene.frame_start, scene.frame_end = int(argv[1]), int(argv[2])
    pct = os.environ.get('RENDER_PCT')
    if pct:
        scene.render.resolution_percentage = int(pct)
    os.makedirs(os.path.join(HERE, 'frames'), exist_ok=True)
    scene.render.filepath = os.path.join(HERE, 'frames', 'f')
    scene.render.image_settings.file_format = 'PNG'
    bpy.ops.render.render(animation=True)
    print('ANIM DONE', scene.frame_start, scene.frame_end)
