"""Create three editable Blender scenes from local data, then render with Blender.

blender --background --factory-startup --python build_blender.py -- --quality final
No third-party Blender packages or downloaded assets are required.
"""
import argparse
import json
import math
from pathlib import Path
import random
import sys
import time

import bpy
from mathutils import Vector

OUT = Path(__file__).resolve().parent
DATA = json.loads((OUT / 'connectome_data.json').read_text(encoding='utf-8'))
ARGS = argparse.ArgumentParser()
ARGS.add_argument('--quality', choices=['preview', 'final'], default='final')
ARGS.add_argument('--only', choices=['fly', 'brain', 'pathway', 'all'], default='all')
opts = ARGS.parse_args(sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else [])
RNG = random.Random(20261023)
PALETTE = {'LC4': '#167F94', 'LPLC2': '#DD8E23', 'relay': '#7763B1', 'command': '#B83D68'}
MATERIALS = {}
UV_MESHES = {}
GPU_DEVICE = False
try:
    preferences = bpy.context.preferences.addons['cycles'].preferences
    preferences.compute_device_type = 'CUDA'
    preferences.get_devices()
    for device in preferences.devices:
        device.use = device.type == 'CUDA'
    GPU_DEVICE = any(d.type == 'CUDA' for d in preferences.devices)
except Exception as error:
    print('CPU_FALLBACK: ' + str(error), flush=True)
bpy.context.preferences.filepaths.file_preview_type = 'NONE'


def rgb(value):
    value = value.lstrip('#')
    result = []
    for i in (0, 2, 4):
        c = int(value[i:i+2], 16) / 255
        result.append(c / 12.92 if c <= .04045 else ((c + .055) / 1.055) ** 2.4)
    return tuple(result)


def material(name, color, roughness=.4, metal=0, emission=0):
    if name in MATERIALS:
        return MATERIALS[name]
    mat = bpy.data.materials.new(name)
    mat.diffuse_color = (*rgb(color), 1)
    mat.use_nodes = True
    bs = mat.node_tree.nodes.get('Principled BSDF')
    bs.inputs['Base Color'].default_value = (*rgb(color), 1)
    bs.inputs['Roughness'].default_value = roughness
    bs.inputs['Metallic'].default_value = metal
    if emission:
        bs.inputs['Emission Color'].default_value = (*rgb(color), 1)
        bs.inputs['Emission Strength'].default_value = emission
    MATERIALS[name] = mat
    return mat


def unlit(name, color):
    mat = material(name, color)
    nodes = mat.node_tree.nodes
    nodes.clear()
    em = nodes.new('ShaderNodeEmission')
    em.inputs['Color'].default_value = (*rgb(color), 1)
    em.inputs['Strength'].default_value = 1
    out = nodes.new('ShaderNodeOutputMaterial')
    mat.node_tree.links.new(em.outputs[0], out.inputs['Surface'])
    return mat


def move_to(obj, collection):
    for old in list(obj.users_collection):
        old.objects.unlink(obj)
    collection.objects.link(obj)
    return obj


def collection(scene, name):
    result = bpy.data.collections.new(name)
    scene.collection.children.link(result)
    return result


def uv(name, loc, scale, mat, col, segments=48, rings=28):
    key = (segments, rings, mat.name)
    if key not in UV_MESHES:
        bpy.ops.mesh.primitive_uv_sphere_add(segments=segments, ring_count=rings)
        template = bpy.context.object
        mesh = template.data
        mesh.name = 'Shared_sphere_%s_%s_%s' % key
        mesh.materials.append(mat)
        for poly in mesh.polygons:
            poly.use_smooth = True
        bpy.data.objects.remove(template, do_unlink=True)
        UV_MESHES[key] = mesh
    obj = bpy.data.objects.new(name, UV_MESHES[key])
    col.objects.link(obj)
    obj.location = loc
    obj.scale = scale
    return obj


def curve(name, points, radius, mat, col, smooth=True, radii=None):
    data = bpy.data.curves.new(name, 'CURVE')
    data.dimensions = '3D'
    data.resolution_u = 12
    data.bevel_depth = radius
    data.bevel_resolution = 3 if radius > .012 else 2
    if smooth:
        spline = data.splines.new('BEZIER')
        spline.bezier_points.add(len(points) - 1)
        for i, (p, co) in enumerate(zip(spline.bezier_points, points)):
            p.co = co
            p.handle_left_type = p.handle_right_type = 'AUTO'
            if radii:
                p.radius = radii[i]
    else:
        spline = data.splines.new('POLY')
        spline.points.add(len(points) - 1)
        for p, co in zip(spline.points, points):
            p.co = (*co, 1)
    data.materials.append(mat)
    obj = bpy.data.objects.new(name, data)
    col.objects.link(obj)
    return obj


def sphere_batch(name, points, radius, mat, col, subdivision=1):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=subdivision, radius=1)
    template = bpy.context.object
    basev = [v.co.copy() for v in template.data.vertices]
    basef = [list(p.vertices) for p in template.data.polygons]
    bpy.data.objects.remove(template, do_unlink=True)
    vertices, faces = [], []
    for item in points:
        center, r = (item[0], item[1]) if isinstance(item, tuple) else (item, radius)
        offset = len(vertices)
        vertices.extend([Vector(center) + v * r for v in basev])
        faces.extend([[i + offset for i in face] for face in basef])
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(vertices, [], faces)
    mesh.materials.append(mat)
    for p in mesh.polygons:
        p.use_smooth = True
    obj = bpy.data.objects.new(name, mesh)
    col.objects.link(obj)
    return obj


def light(scene, name, loc, power, size, color=(1, 1, 1)):
    data = bpy.data.lights.new(name, 'AREA')
    data.energy = power
    data.shape = 'DISK'
    data.size = size
    data.color = color
    obj = bpy.data.objects.new(name, data)
    scene.collection.objects.link(obj)
    obj.location = loc
    obj.rotation_euler = (Vector((0, 0, .7)) - obj.location).to_track_quat('-Z', 'Y').to_euler()


def setup(name, camera_loc, target, width, ratio=(2400, 1600)):
    scene = bpy.data.scenes.new(name)
    bpy.context.window.scene = scene
    scene.render.engine = 'CYCLES'
    scene.cycles.device = 'GPU' if GPU_DEVICE else 'CPU'
    scene.cycles.samples = 48 if opts.quality == 'final' else 20
    scene.cycles.adaptive_threshold = .035
    scene.cycles.adaptive_min_samples = 12
    scene.cycles.use_denoising = True
    scene.cycles.max_bounces = 6
    scene.cycles.transparent_max_bounces = 8
    scene.render.resolution_x, scene.render.resolution_y = ratio
    scene.render.resolution_percentage = 100 if opts.quality == 'final' else 45
    scene.render.image_settings.file_format = 'PNG'
    scene.render.image_settings.color_mode = 'RGBA'
    scene.render.image_settings.color_depth = '8'
    scene.render.film_transparent = False
    scene.world = bpy.data.worlds.new(name + '_studio')
    scene.world.use_nodes = True
    scene.world.node_tree.nodes.get('Background').inputs['Color'].default_value = (.86, .9, 1.0, 1)
    scene.world.node_tree.nodes.get('Background').inputs['Strength'].default_value = .32
    scene.view_settings.view_transform = 'AgX'
    scene.view_settings.look = 'AgX - Medium High Contrast'
    # An opaque nearly white world is composited from the camera direction.
    world = scene.world.node_tree
    lightpath = world.nodes.new('ShaderNodeLightPath')
    camera_bg = world.nodes.new('ShaderNodeBackground')
    camera_bg.inputs[0].default_value = (.96, .966, .975, 1)
    camera_bg.inputs[1].default_value = 1
    mix = world.nodes.new('ShaderNodeMixShader')
    world.links.new(lightpath.outputs['Is Camera Ray'], mix.inputs[0])
    world.links.new(world.nodes.get('Background').outputs[0], mix.inputs[1])
    world.links.new(camera_bg.outputs[0], mix.inputs[2])
    world.links.new(mix.outputs[0], world.nodes.get('World Output').inputs['Surface'])
    cam_data = bpy.data.cameras.new(name + '_camera')
    cam = bpy.data.objects.new(name + '_camera', cam_data)
    scene.collection.objects.link(cam)
    cam.location = camera_loc
    cam.rotation_euler = (Vector(target) - cam.location).to_track_quat('-Z', 'Y').to_euler()
    cam_data.type = 'ORTHO'
    cam_data.ortho_scale = width
    cam_data.lens = 52
    scene.camera = cam
    bpy.context.view_layer.update()
    light(scene, 'Key_softbox', (-5, -3, 9), 1100, 7)
    light(scene, 'Fill_softbox', (6, 4, 6), 850, 6, (.83, .9, 1))
    light(scene, 'Rim_softbox', (0, 5, 9), 1200, 5, (1, .88, .73))
    return scene


TEXTCOL = None
FONT = None
fontpath = Path('C:/Windows/Fonts/segoeui.ttf')
if fontpath.exists():
    FONT = bpy.data.fonts.load(str(fontpath))
INK = unlit('Text_ink', '#243B4B')
MUTED = unlit('Text_muted', '#617483')


def hud(scene, text, x, y, size=.24, mat=None, align='LEFT'):
    cam = scene.camera
    frame = cam.data.view_frame(scene=scene)
    xmin, xmax = min(v.x for v in frame), max(v.x for v in frame)
    ymin, ymax = min(v.y for v in frame), max(v.y for v in frame)
    local = Vector((xmin + (xmax - xmin) * x, ymin + (ymax - ymin) * y, -5))
    data = bpy.data.curves.new('Label_' + text[:35], 'FONT')
    data.body = text
    data.size = size
    data.align_x = align
    data.space_line = 1.15
    if FONT:
        data.font = FONT
    data.materials.append(mat or INK)
    obj = bpy.data.objects.new(data.name, data)
    scene.collection.objects.link(obj)
    obj.location = cam.matrix_world @ local
    obj.rotation_euler = cam.rotation_euler
    return obj


def worldlabel(scene, text, position, size=.16, mat=None):
    data = bpy.data.curves.new('Node_label_' + text, 'FONT')
    data.body = text
    data.size = size
    if FONT:
        data.font = FONT
    data.materials.append(mat or INK)
    obj = bpy.data.objects.new(data.name, data)
    scene.collection.objects.link(obj)
    obj.location = position
    obj.rotation_euler = scene.camera.rotation_euler
    return obj


def fly_scene():
    scene = setup('01_Fruit_fly', (7.2, 9.5, 10.5), (0, -.35, 1.0), 9.7)
    bodycol = collection(scene, 'Fly_body_editable')
    legscol = collection(scene, 'Six_articulated_legs')
    wingscol = collection(scene, 'One_pair_of_veined_wings')
    hairscol = collection(scene, 'Bristles_and_eye_facets')
    gold = material('Thorax_ochre', '#B28C4F', .47)
    abdomen = material('Abdomen_amber', '#C59A54', .4)
    dark = material('Abdominal_dark_bands', '#302B24', .4)
    legmat = material('Legs_chestnut', '#79572E', .4)
    hairmat = material('Bristles_um ber', '#3F3325', .62)
    eye = material('Compound_eye_ruby', '#8F1626', .28)
    eye_dark = material('Eye_facets_deep_red', '#A52132', .33)
    uv('Thorax', (0, .35, 1.47), (.61, .82, .59), gold, bodycol)
    uv('Head', (0, 1.39, 1.59), (.51, .49, .43), gold, bodycol)
    uv('Scutellum', (0, -.32, 1.72), (.38, .3, .22), abdomen, bodycol)
    # One continuous tapered abdomen, with material bands assigned on the mesh.
    nrings, nsides = 51, 64
    verts, faces = [], []
    for k in range(nrings):
        t = k / (nrings - 1)
        y = -.3 - 1.92 * t
        r = .63 * max(.005, math.sin(math.pi * (.21 + .79 * t))) ** .72
        z = 1.27 - .13 * t
        for j in range(nsides):
            a = j / nsides * 2 * math.pi
            verts.append((r * math.cos(a), y, z + .72 * r * math.sin(a)))
    for k in range(nrings - 1):
        for j in range(nsides):
            faces.append((k * nsides + j, k * nsides + (j+1) % nsides,
                          (k+1) * nsides + (j+1) % nsides, (k+1) * nsides + j))
    faces += [tuple(range(nsides - 1, -1, -1)), tuple((nrings-1)*nsides+j for j in range(nsides))]
    mesh = bpy.data.meshes.new('Tapered_segmented_abdomen')
    mesh.from_pydata(verts, [], faces)
    mesh.materials.append(abdomen)
    mesh.materials.append(dark)
    for i, p in enumerate(mesh.polygons):
        k = min(i // nsides, nrings - 2)
        t = (k + .5) / (nrings - 1)
        p.material_index = int(t > .28 and (t * 5.2) % 1 > .63)
        p.use_smooth = True
    obj = bpy.data.objects.new('Abdomen_with_transverse_bands', mesh)
    bodycol.objects.link(obj)
    # Large red compound eyes, with individually modelled small ommatidial facets.
    for side in (-1, 1):
        center = Vector((side * .405, 1.48, 1.68))
        scale = Vector((.29, .405, .40))
        uv(('Left' if side < 0 else 'Right') + '_compound_eye', center, scale, eye, bodycol)
        points = []
        for ring in range(1, 18):
            theta = math.pi * ring / 18
            n = max(5, int(36 * math.sin(theta)))
            for j in range(n):
                phi = 2 * math.pi * (j + .5 * (ring % 2)) / n
                normal = Vector((math.sin(theta)*math.cos(phi), math.sin(theta)*math.sin(phi), math.cos(theta)))
                if normal.x * side < -.2:
                    continue
                surface = center + Vector([normal[a] * scale[a] for a in range(3)]) * .985
                points.append((list(surface), .011))
        sphere_batch('Compound_eye_facets_' + str(side), points, .011, eye_dark, hairscol, 1)
        # Jointed antennae and plumose arista.
        uv('Antenna_pedicel_' + str(side), (side*.16, 1.87, 1.64), (.08,.11,.08), gold, bodycol)
        uv('Antenna_funiculus_' + str(side), (side*.20, 2.02, 1.62), (.10,.15,.085), legmat, bodycol)
        arista = [Vector((side*.23,2.05,1.7)),Vector((side*.39,2.15,1.92)),Vector((side*.55,2.18,2.16))]
        curve('Arista_' + str(side), arista, .013, hairmat, hairscol)
        for j in range(1, 7):
            t = j / 7
            p = arista[0].lerp(arista[-1], t)
            for sign in (-1, 1):
                q = p + Vector((side * .10 * sign, .03, .11 * sign))
                curve('Arista_branch', [p,q], .004, hairmat, hairscol, False)
        # Three true leg pairs: coxa/femur/tibia/tarsus and paired claws.
        for i in range(3):
            ya = [.86,.18,-.48][i]
            start = Vector((side*.40,ya,1.24))
            hip = Vector((side*.72,ya + [.12,-.02,-.14][i],1.12))
            knee = Vector((side*[1.25,1.65,1.25][i],ya + [.85,.10,-.82][i],.85))
            ankle = Vector((side*[1.52,1.93,1.74][i],ya + [1.14,-.13,-1.34][i],.12))
            foot = Vector((side*[1.85,2.25,2.1][i],ya + [1.38,-.16,-1.56][i],.035))
            points = [start,hip,knee,ankle,foot]
            for j in range(4):
                curve('Leg_%s_%s_segment_%s' % (side,i+1,j+1), [points[j],points[j+1]],
                      [.072,.057,.036,.019][j], legmat, legscol, False,
                      radii=None)
            for p, r in [(hip,.067),(knee,.056),(ankle,.031)]:
                uv('Leg_joint',p,(r,r,r),legmat,legscol,20,12)
            for j in range(7):
                p = knee.lerp(ankle,(j+1)/9)
                curve('Tibial_bristle',[p,p+Vector((side*.10,.035,.10))], .005,hairmat,hairscol,False)
            for sign in (-1,1):
                curve('Tarsal_claw',[foot,foot+Vector((side*.045,sign*.06,.015)),foot+Vector((side*.075,sign*.07,.04))],.009,dark,legscol)
        uv('Haltere_' + str(side), (side*.70,-.40,1.20),(.10,.085,.09),gold,bodycol)
        curve('Haltere_stalk_' + str(side),[(side*.46,-.26,1.28),(side*.70,-.40,1.20)],.026,gold,bodycol)
    for x,y in [(-.08,1.38),(.08,1.38),(0,1.48)]:
        uv('Ocellus',(x,y,2.009),(.045,.045,.027),dark,bodycol,20,12)
    uv('Proboscis',(0,1.80,1.29),(.10,.15,.12),legmat,bodycol)
    # Slightly translucent, membranous wings with a fine rim and longitudinal veins.
    membrane = material('Wing_translucent_chitin','#DCE6DB',.28)
    nodes = membrane.node_tree.nodes
    bs = nodes.get('Principled BSDF')
    bs.inputs['Transmission Weight'].default_value = .45
    bs.inputs['IOR'].default_value = 1.32
    bs.inputs['Alpha'].default_value = .24
    veinmat = material('Wing_veins','#8C9479',.52)
    outline = [( .43,.48,1.83),(.91,.35,1.91),(1.87,.05,1.99),(2.83,-.58,2.00),
               (3.27,-1.28,1.96),(3.16,-1.72,1.89),(2.73,-1.93,1.83),
               (2.10,-1.68,1.80),(1.38,-.92,1.80),(.70,-.12,1.80)]
    for side in (-1,1):
        points = [(side*x,y,z) for x,y,z in outline]
        # Sample a closed Catmull-Rom outline, then triangulate to a central fan.
        smooth = []
        for i in range(len(points)):
            p0,p1,p2,p3 = [Vector(points[j % len(points)]) for j in (i-1,i,i+1,i+2)]
            for step in range(8):
                t = step/8
                p = .5*((2*p1)+(-p0+p2)*t+(2*p0-5*p1+4*p2-p3)*t*t+(-p0+3*p1-3*p2+p3)*t*t*t)
                smooth.append(p)
        center = sum(smooth,Vector())/len(smooth)
        mesh = bpy.data.meshes.new('Wing_membrane_mesh')
        mesh.from_pydata([center]+smooth, [], [(0,i+1,(i+1)%len(smooth)+1) for i in range(len(smooth))])
        mesh.materials.append(membrane)
        wing = bpy.data.objects.new('Left_wing' if side<0 else 'Right_wing',mesh)
        wingscol.objects.link(wing)
        curve('Wing_costal_rim',smooth+[smooth[0]],.010,veinmat,wingscol,False)
        veins = [[(.48,.40,1.846),(1.33,.13,1.94),(2.40,-.43,2.014),(3.17,-1.21,1.98)],
                 [(.49,.37,1.846),(1.27,-.13,1.92),(2.28,-.73,1.95),(3.13,-1.62,1.92)],
                 [(.50,.34,1.846),(1.19,-.40,1.88),(1.97,-1.02,1.89),(2.72,-1.85,1.86)],
                 [(.50,.30,1.846),(1.02,-.48,1.84),(1.62,-1.15,1.84),(2.11,-1.67,1.84)],
                 [(1.56,-.32,1.94),(1.55,-.65,1.91)],
                 [(2.26,-.70,1.96),(2.22,-1.25,1.90)]]
        for j, line in enumerate(veins):
            curve('Wing_vein_' + str(j),[(side*x,y,z) for x,y,z in line],.010 if j<4 else .008,veinmat,wingscol)
    # Sparse surface bristles, plus longer macrochaetae at the thorax rim.
    for i in range(125):
        phi = RNG.uniform(0,2*math.pi)
        theta = RNG.uniform(.16,math.pi*.85)
        n = Vector((math.sin(theta)*math.cos(phi),math.sin(theta)*math.sin(phi),math.cos(theta)))
        if n.z < .1:
            continue
        p = Vector((0,.35,1.47))+Vector((n.x*.61,n.y*.82,n.z*.59))
        length = RNG.uniform(.08,.18)
        curve('Thoracic_bristle',[p,p+n*length+Vector((0,-.025,.025))],.005,hairmat,hairscol,False)
    for side in (-1,1):
        for ya in (-.14,.18,.55,.85):
            p=Vector((side*.43,ya,1.88))
            curve('Thoracic_macrochaeta',[p,p+Vector((side*.11,-.05,.25)),p+Vector((side*.20,-.10,.40))],.009,hairmat,hairscol,radii=[1,.8,.1])
    # Very subtle chitin microtexture.
    for mat in (gold,abdomen):
        nodes=mat.node_tree.nodes
        tex=nodes.new('ShaderNodeTexNoise')
        tex.inputs['Scale'].default_value=75
        bump=nodes.new('ShaderNodeBump')
        bump.inputs['Strength'].default_value=.12
        bump.inputs['Distance'].default_value=.025
        mat.node_tree.links.new(tex.outputs['Fac'],bump.inputs['Height'])
        mat.node_tree.links.new(bump.outputs['Normal'],nodes.get('Principled BSDF').inputs['Normal'])
    bpy.ops.mesh.primitive_plane_add(size=200,location=(0,0,-.018))
    floor=bpy.context.object
    floor.name='Studio_floor'
    floor.data.materials.append(material('Warm_white_floor','#F2F3F2',.65))
    hud(scene,'Drosophila melanogaster',.06,.915,.32)
    hud(scene,'Procedural 3D illustration',.06,.865,.16,MUTED)
    hud(scene,'COMPOUND EYES   /   VEINED WINGS   /   SIX LEGS',.06,.075,.16,MUTED)
    hud(scene,'Illustrative exterior; no anatomical scan was used.',.06,.039,.15,MUTED)
    scene['scope']='Procedural illustrative fruit fly, not a specimen reconstruction; no invented spatial connection to the separate connectome.'
    return scene


def node_materials():
    return {k:material('Neuron_'+k,v,.32,.04) for k,v in PALETTE.items()}


def add_node(node, position, radius, mats, col):
    obj=uv(node['cell_type']+'_'+node['side']+'_'+node['root_id'],position,(radius,)*3,mats[node['role']],col,24,16)
    obj['FlyWire_root_id']=node['root_id']
    obj['model_index']=node['index']
    obj['cell_type']=node['cell_type']
    obj['side']=node['side']
    obj['native_anchor_voxels']=node['anchor_voxels']
    return obj


def edge_materials(pale=False):
    colors={'LC4':'#94B7C2','LPLC2':'#D9BB8B','relay':'#BCB3CC','command':'#C194A7'} if pale else PALETTE
    return {k:material(('Edge_pale_' if pale else 'Edge_')+k,v,.52) for k,v in colors.items()}


def graph_edges(scene, positions, nodes, col, pale=False, anatomy=False):
    mats=edge_materials(pale)
    maximum=max(abs(e['signed_model_weight']) for e in DATA['edges'])
    for k,e in enumerate(DATA['edges']):
        a,b=Vector(positions[e['source']]),Vector(positions[e['target']])
        mid=(a+b)*.5
        # Routing is explicitly illustrative and carries no axon-path meaning.
        if not anatomy:
            mid.y += .12 + .07*math.sin(k*.37)
        else:
            mid.y += .035*math.sin(k)
        strength=math.log1p(abs(e['signed_model_weight']))/math.log1p(maximum)
        radius=(.0028+.0075*strength) if anatomy else (.0035+.009*strength)
        role=nodes[e['source']]['role']
        obj=curve('Connection_%s_to_%s'%(e['source'],e['target']),[a,mid,b],radius,mats[role],col)
        obj['source_root_id']=nodes[e['source']]['root_id']
        obj['target_root_id']=nodes[e['target']]['root_id']
        obj['signed_model_weight']=e['signed_model_weight']
        obj['contact_count']=e['contacts']


def brain_scene():
    scene=setup('02_Connectome_anchors',(0,-18,4.7),(0,0,0),12.5)
    col=collection(scene,'Selected_pathway_neurons_actual_anchors')
    bcol=collection(scene,'Background_8500_sampled_actual_anchors')
    ecol=collection(scene,'1050_real_edges_abstract_curves')
    mats=node_materials()
    node_by_id={n['index']:n for n in DATA['nodes']}
    positions={n['index']:n['position'] for n in DATA['nodes']}
    for group,color in [('optic','#BACAD1'),('other','#A5B5C5')]:
        points=[p['position'] for p in DATA['background'] if p['group']==group]
        sphere_batch('Sampled_'+group+'_anchors',points,.020,material('Background_'+group,color,.6),bcol,1)
    graph_edges(scene,positions,node_by_id,ecol,pale=True,anatomy=True)
    for node in DATA['nodes']:
        r={'LC4':.042,'LPLC2':.042,'relay':.051,'command':.105}[node['role']]
        add_node(node,node['position'],r,mats,col)
    hud(scene,'The local fly connectome',.055,.92,.37)
    hud(scene,'FlyWire v783  /  measured representative neuron locations',.055,.864,.17,MUTED)
    # Compact data legend, below the anatomical view.
    for k,x in [('LC4',.06),('LPLC2',.27),('relay',.49),('command',.72)]:
        count=sum(n['role']==k for n in DATA['nodes'])
        hud(scene,f'{k.upper() if k=="relay" else k}   {count}',x,.14,.18,unlit('Legend_'+k,PALETTE[k]))
    hud(scene,'8,500 background anchors  +  selected visual-to-command pathway',.06,.092,.165,MUTED)
    hud(scene,'Curves encode selected connections; they do not reconstruct axons or dendrites.',.06,.05,.165,MUTED)
    scene['scope']='Anchor point positions from local annotations; 4x4x40 nm voxel scaling. Abstract connectivity curves are not measured neurites.'
    return scene


def pathway_scene():
    scene=setup('03_Visual_command_pathway',(0,-22,3.8),(0,0,0),13.8,ratio=(2600,1600))
    ncol=collection(scene,'Mapped_neurons_schematic_layout')
    ecol=collection(scene,'Selected_actual_connections')
    mats=node_materials()
    nodes={n['index']:n for n in DATA['nodes']}
    positions={}
    # A deterministic clustered layout; no claim of anatomical positions here.
    for role,center,radii in [('LC4',(-4.15,0,1.25),(.70,.32,1.02)),
                               ('LPLC2',(-4.15,0,-1.18),(.82,.42,1.10)),
                               ('relay',(0,0,0),(.90,.58,2.12))]:
        group=[n for n in DATA['nodes'] if n['role']==role]
        for i,node in enumerate(group):
            angle=i*math.pi*(3-math.sqrt(5))
            t=(i+.5)/len(group)
            rad=math.sqrt(t)
            p=[center[0]+radii[0]*rad*math.cos(angle),
               center[1]+radii[1]*math.sin(i*2.3),
               center[2]+radii[2]*rad*math.sin(angle)]
            positions[node['index']]=p
    outputs=sorted([n for n in DATA['nodes'] if n['role']=='command'],key=lambda n:(['DNp01','DNa02','DNp04','DNb01'].index(n['cell_type']),n['side']))
    for i,node in enumerate(outputs):
        positions[node['index']]=[3.6,0,2.12-i*.60]
    graph_edges(scene,positions,nodes,ecol,pale=True)
    for node in DATA['nodes']:
        radius={'LC4':.052,'LPLC2':.046,'relay':.074,'command':.13}[node['role']]
        add_node(node,positions[node['index']],radius,mats,ncol)
    for node in outputs:
        p=Vector(positions[node['index']])+Vector((.27,-.08,-.06))
        side={'left':'L','right':'R'}.get(node['side'],node['side'])
        worldlabel(scene,node['cell_type']+'  '+side,p,.19)
    hud(scene,'Visual-to-command pathway',.055,.92,.38)
    hud(scene,'Real connectivity from your local fruit-fly project',.055,.864,.18,MUTED)
    hud(scene,'VISUAL INPUT',.19,.80,.19,MUTED,'CENTER')
    hud(scene,'SELECTED RELAYS',.50,.80,.19,MUTED,'CENTER')
    hud(scene,'COMMAND OUTPUT',.80,.80,.19,MUTED,'CENTER')
    hud(scene,'LC4  104',.065,.59,.18,unlit('Legend_LC4',PALETTE['LC4']))
    hud(scene,'LPLC2  210',.056,.32,.18,unlit('Legend_LPLC2',PALETTE['LPLC2']))
    distinct=DATA['summary'].get('distinct_relay_nodes',sum(n['role']=='relay' for n in DATA['nodes']))
    hud(scene,f'{distinct} distinct relays',.5,.17,.18,unlit('Legend_relay',PALETTE['relay']),'CENTER')
    hud(scene,'8 neurons',.80,.17,.18,unlit('Legend_command',PALETTE['command']),'CENTER')
    hud(scene,f'{len(DATA["nodes"]):,} unique neurons  /  1,050 selected directed connections  /  direction: left to right',.055,.092,.17,MUTED)
    hud(scene,'Schematic positions. Thickness follows absolute model weight; colors identify neuron groups.',.055,.048,.16,MUTED)
    scene['scope']='Actual selected neuron IDs and directed edges; positions are schematic, not anatomical. Colors identify groups, not activity or neurotransmitter sign.'
    return scene


def save_render(scene, stem):
    bpy.context.window.scene=scene
    # Save opening view in camera mode; keep all objects editable by group.
    for screen in bpy.data.screens:
        for area in screen.areas:
            if area.type=='VIEW_3D':
                area.spaces.active.region_3d.view_perspective='CAMERA'
                area.spaces.active.overlay.show_overlays=False
                area.spaces.active.shading.type='MATERIAL'
    scene.render.filepath=str(OUT/(stem+'.png'))
    print('RENDER_START '+stem+' device='+scene.cycles.device,flush=True)
    try:
        bpy.ops.render.render(write_still=True)
    except RuntimeError:
        if scene.cycles.device != 'GPU':
            raise
        print('GPU_RENDER_FAILED_RETRY_CPU',flush=True)
        scene.cycles.device='CPU'
        bpy.ops.render.render(write_still=True)
    print('RENDER_DONE '+stem,flush=True)


def main():
    # Factory content is discarded only in this fresh Blender process.
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)
    initial=list(bpy.data.scenes)
    scenes=[]
    if opts.only in ['fly','all']:
        print('BUILD_FLY',flush=True)
        scenes.append((fly_scene(),'fruit_fly'))
    if opts.only in ['brain','all']:
        print('BUILD_BRAIN',flush=True)
        scenes.append((brain_scene(),'connectome'))
    if opts.only in ['pathway','all']:
        print('BUILD_PATHWAY',flush=True)
        scenes.append((pathway_scene(),'visual_pathway'))
    for scene in initial:
        bpy.data.scenes.remove(scene)
    for name in ['data_manifest.json','displayed_neurons.csv','displayed_edges.csv']:
        text=bpy.data.texts.new(name)
        text.write((OUT/name).read_text(encoding='utf-8-sig'))
    source=bpy.data.texts.new('build_blender.py')
    source.write(Path(__file__).read_text(encoding='utf-8'))
    # Pack the loaded font so the editable project does not depend on Windows fonts.
    bpy.context.window.scene=scenes[0][0]
    bpy.ops.file.pack_all()
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'drosophila_studio.blend'))
    for scene,stem in scenes:
        save_render(scene,stem)
    # Keep the fly as the opening scene in the complete project.
    bpy.context.window.scene=scenes[0][0]
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'drosophila_studio.blend'))
    (OUT/'render_status.json').write_text(json.dumps(dict(blender=bpy.app.version_string,
        quality=opts.quality,scenes=[s.name for s,_ in scenes],
        outputs=[stem+'.png' for _,stem in scenes],
        note='Three-dimensional Blender/Cycles renders. Actual connectivity with clearly distinguished illustrative geometry.'),indent=2),encoding='utf-8')
    print('ALL_SCENES_COMPLETE',flush=True)


if __name__=='__main__':
    main()
