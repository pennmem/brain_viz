import os
import sys
import bpy
import glob
import logging

bpy.ops.wm.addon_enable(module='blend4web')


def gen_blender_scene(cortexdir, outputdir, priorstimdir, contactdir=None, subject=None, subject_num=None):
    update_world_settings()
    red, blue, green, white = setup_color_materials()
    load_meshes(cortexdir)
    prettify_objects(white)
    consolidate_hemispheres()

    # Only add contacts for subject-specific brains
    if subject is not None:
        add_contacts(contactdir + '/electrode_coordinates.csv', red, blue, green)
        orient_contacts(contactdir + '/electrode_coordinates.csv')

    add_prior_stim_sites(priorstimdir)
    finalize_object_attributes()
    add_scene_lighting()
    add_camera()
    save_scene(outputdir)
    return

def update_world_settings():
    bpy.context.scene.world.b4w_sky_settings.render_sky = True
    bpy.context.scene.world.use_sky_blend = True
    bpy.context.scene.world.horizon_color = (0.101, 0.181, 0.253)
    bpy.context.scene.world.zenith_color = (0.334, 0.293, 0.276)
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
        if cortexpath.find(".pial") != -1:
            continue # skip lh.pial.obj and rh.pial.obj files
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
    bpy.ops.object.empty_add(type='PLAIN_AXES') # Empty.001
    bpy.ops.object.empty_add(type='PLAIN_AXES') # Empty.002
    bpy.ops.object.empty_add(type='PLAIN_AXES') # Empty.003
    bpy.ops.object.empty_add(type='PLAIN_AXES') # Empty.004

    # If the file name has 'hcp' in it, they should be assigned to different axis
    for ob in bpy.context.scene.objects:
        if ((ob.name[0] is 'l') and (ob.name.find('hcp') == -1)):
            ob.parent = bpy.data.objects["Empty.001"]
        elif ((ob.name[0] is 'l') and (ob.name.find('hcp') != -1)):
            ob.parent = bpy.data.objects["Empty.003"]
        elif ((ob.name[0] is 'r') and (ob.name.find('hcp') == -1)):
            ob.parent = bpy.data.objects["Empty.002"]
        elif ((ob.name[0] is 'r') and (ob.name.find('hcp') != -1)):
            ob.parent = bpy.data.objects["Empty.004"]
        else:
            continue
    
    bpy.data.objects["Empty.001"].name = 'lh'
    bpy.data.objects["Empty.002"].name = 'rh'
    bpy.data.objects["Empty.003"].name = 'lh_hcp'
    bpy.data.objects["Empty.004"].name = 'rh_hcp'
    bpy.data.objects['lh'].b4w_do_not_batch = True
    bpy.data.objects['rh'].b4w_do_not_batch = True
    bpy.data.objects['lh_hcp'].b4w_do_not_batch = True
    bpy.data.objects['rh_hcp'].b4w_do_not_batch = True
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

def add_contacts(contactpath, mono_color, bipo_color, orig_color):
    atlas_color_map = {'monopolar_orig' : orig_color,
                       'monopolar_dykstra': mono_color,
                       'bipolar_dykstra': bipo_color}
    # Empty axes so we can group monopolar, bipolar, and original locations
    bpy.ops.object.empty_add(type='PLAIN_AXES')
    bpy.data.objects["Empty.001"].name = 'monopolar_orig'
    bpy.ops.object.empty_add(type='PLAIN_AXES')
    bpy.data.objects["Empty.001"].name = 'monopolar_dykstra'
    bpy.ops.object.empty_add(type="PLAIN_AXES")
    bpy.data.objects["Empty.001"].name = "bipolar_dykstra"
    with open(contactpath, 'r') as f:
        next(f) # skip header
        for line in f:
            name, _type, x, y, z, atlas, orient_contact = line.split(",")
            atlas = atlas.rstrip()
            bpy.ops.mesh.primitive_cylinder_add(
                vertices = 32,
                radius = 2,
                depth = 1.5,
                location = (float(x), float(y), float(z))
            )
            ob = bpy.context.object
            ob.name = name
            ob.scale = (0.02, 0.02, 0.02)
            set_material(ob, atlas_color_map[atlas])
            ob.parent = bpy.data.objects[atlas]
    return


def orient_contacts(contactpath):
    with open(contactpath, 'r') as f:
        next(f) # skip header
        for line in f:
            name, _type, x, y, z, atlas, orient_contact = line.split(",")
            orient_contact = orient_contact.rstrip()
            if (_type.find("D") == -1):
                orient_towards(bpy.data.objects[name], bpy.data.objects["Empty"])
            elif ((_type.find("D") != -1) & (orient_contact != '')):
                try:
                    orient_towards(bpy.data.objects[name], bpy.data.objects[orient_contact])
                except KeyError as e:
                    logging.error("Unable to find contact %s" % orient_contact)
                    continue
            else:
                orient_towards(bpy.data.objects[name], bpy.data.objects["Empty"])
    return


def orient_towards(contact, to_object):
    bpy.context.scene.objects.active = contact
    bpy.ops.object.constraint_add(type="TRACK_TO")
    contact.constraints["Track To"].target = to_object
    contact.constraints["Track To"].up_axis = "UP_X"
    contact.constraints["Track To"].track_axis = "TRACK_Z"
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
    # Empty axes so we can group positive and negative stim electrodes
    bpy.ops.object.empty_add(type='PLAIN_AXES')
    bpy.data.objects["Empty.001"].name = 'all_stim_pos'
    bpy.ops.object.empty_add(type='PLAIN_AXES')
    bpy.data.objects["Empty.001"].name = 'all_stim_neg'
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
                object.parent = bpy.data.objects["all_stim_neg"]
            else:
                scaled_neg_color = make_material('scaled_red',
                                                 (1,
                                                  1 - effect_sizes[i],
                                                  1 - effect_sizes[i]),
                                                 (1,1,1),
                                                 1)
                set_material(object, scaled_neg_color)
                object.parent = bpy.data.objects["all_stim_pos"]
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

