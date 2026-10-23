"""Export copied Blender scenes for the v9 paper, without editing originals.

Run with Blender --background --python-exit-code 1 --python this.py --
--source copied.blend --out NEW_DIRECTORY. No neural simulation is performed.
"""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import time

import bpy
from mathutils import Vector


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def identities(scene):
    nodes = sorted((str(o['FlyWire_root_id']), int(o['model_index']))
                   for o in scene.objects if 'FlyWire_root_id' in o)
    edges = sorted((str(o['source_root_id']), str(o['target_root_id']),
                    float(o['signed_model_weight']), int(o['contact_count']))
                   for o in scene.objects if 'source_root_id' in o)
    payload = json.dumps(dict(nodes=nodes, edges=edges), sort_keys=True).encode()
    return dict(nodes=len(nodes), edges=len(edges), sha256=hashlib.sha256(payload).hexdigest())


def frame_geometry(scene, padding=1.04):
    """Fit the existing orthographic camera to all visible geometry, no cropping."""
    camera = scene.camera
    bpy.context.view_layer.update()
    inv = camera.matrix_world.inverted()
    points = [inv @ (o.matrix_world @ Vector(v)) for o in scene.objects
              if o.type in {'MESH', 'CURVE'} and not o.hide_render
              for v in o.bound_box]
    xmin, xmax = min(v.x for v in points), max(v.x for v in points)
    ymin, ymax = min(v.y for v in points), max(v.y for v in points)
    camera.location += camera.matrix_world.to_quaternion() @ Vector(((xmin+xmax)/2, (ymin+ymax)/2, 0))
    aspect = scene.render.resolution_x/scene.render.resolution_y
    camera.data.ortho_scale = max(xmax-xmin, (ymax-ymin)*aspect)*padding
    bpy.context.view_layer.update()
    return dict(projected_bounds=[xmin,xmax,ymin,ymax],padding=padding,
                ortho_scale=camera.data.ortho_scale,
                camera_location=list(camera.location),camera_rotation=list(camera.rotation_euler))


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--source',type=Path,required=True)
    ap.add_argument('--out',type=Path,required=True)
    args=ap.parse_args(sys.argv[sys.argv.index('--')+1:])
    args.out.mkdir(parents=True,exist_ok=False)
    source_hash=sha(args.source)
    bpy.ops.wm.open_mainfile(filepath=str(args.source.resolve()))
    bpy.context.preferences.filepaths.file_preview_type='NONE'
    gpu=False
    try:
        pref=bpy.context.preferences.addons['cycles'].preferences
        pref.compute_device_type='CUDA';pref.get_devices()
        for d in pref.devices:d.use=d.type=='CUDA'
        gpu=any(d.type=='CUDA' for d in pref.devices)
    except Exception as error:print('CPU_FALLBACK',str(error),flush=True)
    scenes=[('01_Fruit_fly','fly',(1200,1000)),
            ('02_Connectome_anchors','brain',(2200,1100)),
            ('03_Visual_command_pathway','pathway',(2200,1050))]
    report={}
    for name,stem,resolution in scenes:
        scene=bpy.data.scenes[name];bpy.context.window.scene=scene
        before=identities(scene)
        hidden=[]
        for o in scene.objects:
            if o.type=='FONT' or o.name=='Studio_floor':
                o.hide_render=True;hidden.append(o.name)
            if o.type=='CURVE' and 'source_root_id' in o:
                o.data.bevel_depth*=.65
        scene.render.resolution_x,scene.render.resolution_y=resolution
        scene.render.resolution_percentage=100
        scene.render.film_transparent=True
        scene.render.image_settings.color_mode='RGBA'
        scene.cycles.samples=64;scene.cycles.adaptive_threshold=.025
        scene.cycles.device='GPU' if gpu else 'CPU'
        camera=frame_geometry(scene)
        assert identities(scene)==before, 'display change altered graph identities'
        t=time.monotonic();scene.render.filepath=str((args.out/(stem+'.png')).resolve())
        print('RENDER_START',stem,scene.cycles.device,flush=True)
        try:bpy.ops.render.render(write_still=True)
        except RuntimeError:
            if scene.cycles.device=='CPU':raise
            scene.cycles.device='CPU';bpy.ops.render.render(write_still=True)
        report[stem]=dict(scene=name,identities=before,hidden=hidden,camera=camera,
            resolution=list(resolution),device=scene.cycles.device,
            seconds=time.monotonic()-t,png_sha256=sha(args.out/(stem+'.png')))
        print('RENDER_DONE',stem,flush=True)
    bpy.ops.wm.save_as_mainfile(filepath=str((args.out/'paper_scenes.blend').resolve()))
    assert sha(args.source)==source_hash, 'source modified'
    result=dict(source_sha256=source_hash,script_sha256=sha(__file__),
        blender_version=bpy.app.version_string,scenes=report,
        display_only=dict(transparent_background=True,hide_text_and_floor=True,
                          uniform_edge_radius_multiplier=.65,all_geometry_in_frame=True),
        outputs={p.name:sha(p) for p in args.out.iterdir() if p.is_file()})
    (args.out/'render-manifest.json').write_text(json.dumps(result,indent=2)+'\n')


if __name__=='__main__':main()
