import sys
import bpy
import glob

bpy.ops.wm.addon_enable(module='blend4web')

def gen_blender_scene(cortexdir, outputdir, priorstimdir, contactdir=None, subject=None, subject_num=None):
    red, blue, green, white = setup_color_materials()
    load_meshes(cortexdir)
    prettify_objects(white)
    consolidate_hemispheres()

    if subject is not None:
        add_contacts(contactdir + '/monopolar_blender.txt', red)
        add_contacts(contactdir + '/bipolar_blender.txt', blue)
        add_contacts(contactdir + '/monopolar_start_blender.txt', green)
        add_prior_stim_sites(priorstimdir)

    add_prior_stim_sites(priorstimdir)
    if subject is None:
        bpy.data.objects['lh.pial-outer-smoothed'].select = True
        bpy.ops.object.delete()

    finalize_object_attributes()
    add_scene_lighting()
    add_camera()
    save_scene(outputdir)
    return


def setup_color_materials():
    red = make_material('Red',(1,0,0),(1,1,1),1)
    blue = make_material('Blue',(0,0,1),(1,1,1),1)
    green = make_material('Green',(0,1,0),(1,1,1),1)
    white = make_material('White',(1,1,1),(1,1,1),1)

    bpy.data.materials["White"].game_settings.alpha_blend = "ALPHA"
    bpy.data.materials["White"].use_transparency = True

    return red, blue, green, white


def load_meshes(cortexdir):
    for line in glob.glob(cortexdir + '/*.obj'):
        cortexpath = line
        bpy.ops.import_scene.obj(filepath=cortexpath)
    return

def prettify_objects(white):
    for ob in bpy.context.scene.objects:
        set_material(ob, white)
        ob.select = True

    bpy.ops.object.shade_smooth()
    for ob in bpy.context.scene.objects:
        ob.select = False

    for o in bpy.data.objects:
        o.rotation_euler[0] = 0
        o.scale[0] = 0.02
        o.scale[1] = 0.02
        o.scale[2] = 0.02

    return


def consolidate_hemispheres():
    bpy.ops.object.empty_add(type='PLAIN_AXES')
    bpy.ops.object.empty_add(type='PLAIN_AXES')
    bpy.ops.object.empty_add(type='PLAIN_AXES')

    for ob in bpy.context.scene.objects:
        if ob.name[0] is 'l':
            ob.parent = bpy.data.objects["Empty.001"]
        if ob.name[0] is 'r':
            ob.parent = bpy.data.objects["Empty.002"]

    bpy.data.objects["Empty.001"].name = 'lh'
    bpy.data.objects["Empty.002"].name = 'rh'
    bpy.data.objects['lh'].b4w_do_not_batch = True
    bpy.data.objects['rh'].b4w_do_not_batch = True

    return

def finalize_object_attributes():
    for o in bpy.data.objects:
        o.b4w_selectable=True
        o.b4w_outlining=True
        o.b4w_do_not_batch=True
    return

def add_scene_lighting():
    bpy.ops.object.lamp_add(type='SUN')
    bpy.context.active_object.name = 'Sun'

    bpy.ops.object.lamp_add(type='POINT', location = (-15,0,0))
    bpy.context.active_object.name = 'Point1'

    bpy.ops.object.lamp_add(type='POINT', location = (0,-15,0))
    bpy.context.active_object.name = 'Point2'

    bpy.ops.object.lamp_add(type='POINT', location = (15,0,0))
    bpy.context.active_object.name = 'Point3'

    bpy.ops.object.lamp_add(type='POINT', location = (0,15,0))
    bpy.context.active_object.name = 'Point4'

    bpy.ops.object.lamp_add(type='POINT', location = (0,0,-15))
    bpy.context.active_object.name = 'Point5'
    return

def add_camera():
    bpy.ops.object.camera_add(
        location = (-8.4, 1.3, 1.7),
        rotation = (64.202362, 0.013625, 48.533962)
    )
    bpy.context.active_object.name = 'Camera'
    return

def save_scene(outputdir):
    blend_outfile = outputdir + '/iEEG_surface.blend'
    bpy.ops.wm.save_mainfile(filepath=blend_outfile)

    json_outfile = outputdir + '/iEEG_surface.json'
    bpy.ops.export_scene.b4w_json(filepath=json_outfile)

    return

def add_contacts(contactpath, color):
    with open(contactpath, 'r') as f:
        for line in f:
            a, b, c, d, e = line.split("\t")
            if "D" in e:
                bpy.ops.mesh.primitive_uv_sphere_add(
                    size = 2,
                    location = (float(b), float(c), float(d))
                )
            else:
                bpy.ops.mesh.primitive_cylinder_add(
                    vertices = 32,
                    radius = 2,
                    depth = 1.5,
                    location = (float(b), float(c), float(d))
                )
            ob = bpy.context.object
            ob.name = a
            ob.scale = (0.02, 0.02, 0.02)
            set_material(ob, color)
    return


def make_material(name, diffuse, specular, alpha):
    mat = bpy.data.materials.new(name)
    mat.diffuse_color = diffuse
    mat.diffuse_shader = 'LAMBERT'
    mat.diffuse_intensity = 1.0
    mat.specular_color = specular
    mat.specular_shader = 'COOKTORR'
    mat.specular_intensity = 0.5
    mat.alpha = alpha
    mat.ambient = 1
    return mat


def set_material(ob, mat):
    me = ob.data
    me.materials.append(mat)
    return


def add_prior_stim_sites(filepath):
    effect_sizes = get_normalized_effects(filepath)
    i = 0
    with open(filepath, 'r') as f:
        next(f) # skip header
        for line in f:
            subject, contact, experiment, deltarec, enhancement, x, y, z = line.split(',')
            x = 0.02 * float(x)
            y = 0.02 * float(y)
            z = 0.02 * float(z)
            bpy.ops.mesh.primitive_uv_sphere_add(size=2, location=(x, y, z))
            object = bpy.context.object
            object.name = ":".join([subject, experiment, contact, str(round(float(deltarec), 1))])
            object.scale = (0.02, 0.02, 0.02)
            if enhancement == "FALSE":
                scaled_pos_color = make_material('scaled_blue',
                                                 (1 - effect_sizes[i],
                                                  1 - effect_sizes[i],
                                                  1),
                                                 (1,1,1),
                                                 1)
                set_material(object, scaled_pos_color)
            else:
                scaled_neg_color = make_material('scaled_red',
                                                 (1,
                                                  1 - effect_sizes[i],
                                                  1 - effect_sizes[i]),
                                                 (1,1,1),
                                                 1)
                set_material(object, scaled_neg_color)
            i += 1
    return

def get_normalized_effects(filepath):
    effects = []
    with open(filepath, 'r') as f:
        next(f) # skip header
        for line in f:
            subject, contact, experiment, deltarec, enhancement, x, y, z = line.split(',')
            effects.append(float(deltarec))

    # Truncate endpoints to emphasize non-outliers
    effects = [-50 if el < -50 else el for el in effects]
    effects = [50 if el > 50 else el for el in effects]

    # Project onto [0,1] range
    effects = [el / max(effects) if el >= 0 else el / min(effects) for el in effects]

    return effects


if __name__ == "__main__":
    # get the args passed to blender after "--", all of which are ignored by
    # blender so scripts may receive their own arguments
    args = sys.argv

    if "--" not in args:
        args = []  # as if no args are passed
    else:
        args = args[args.index("--") + 1:]  # get all args after "--"

    if len(args) == 6:
        subject = args[0]
        subject_num = args[1]
        cortex = args[2]
        contact = args[3]
        output = args[4]
        stimfile = args[5]
        gen_blender_scene(cortex, output, stimfile, contactdir=contact,
                          subject=subject, subject_num=subject_num)

    elif len(args) == 3:
        cortex = args[0]
        output = args[1]
        stimfile = args[2]
        gen_blender_scene(cortex, output, stimfile)

    else:
        raise RuntimeError("Invalid number of arguments passed")

