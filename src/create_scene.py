# Script to make a scene in Blender using Freesurfer cortical meshes and
# monopolar and bipolar electrode contact coordinates.
# Written by Joel Stein
# June 2016 - March 2017

import sys
import bpy
import glob

bpy.ops.wm.addon_enable(module='blend4web')


def generate_brain_image(subject, subject_num, cortex, contact, output):
    cortexdir = cortex
    contactdir = contact
    outdir = output

    red = makeMaterial('Red',(1,0,0),(1,1,1),1)
    blue = makeMaterial('Blue',(0,0,1),(1,1,1),1)
    green = makeMaterial('Green',(0,1,0),(1,1,1),1)
    white = makeMaterial('White',(1,1,1),(1,1,1),1)

    bpy.data.materials["White"].game_settings.alpha_blend = "ALPHA"
    bpy.data.materials["White"].use_transparency = True

    print('Importing meshes...')
    for line in glob.glob(cortexdir + '/*.obj'):
        cortexpath = line
        bpy.ops.import_scene.obj(filepath=cortexpath)

    for ob in bpy.context.scene.objects:
        setMaterial(ob, white)
        ob.select = True
    bpy.ops.object.shade_smooth()
    for ob in bpy.context.scene.objects:
        ob.select = False

    for o in bpy.data.objects:
        o.rotation_euler[0] = 0
        o.scale[0] = 0.02
        o.scale[1] = 0.02
        o.scale[2] = 0.02

    # make empty object for surface electrodes to orient towards
    bpy.ops.object.empty_add(type='PLAIN_AXES')

    # parent left and right hemisphere meshes to objects lh and rh
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

    # now add the monopolar, bipolar and initial position monopolar contacts from list of format name, x, y, z, type
    print('Adding contacts...')
    addContacts(contactdir + '/monopolar_blender.txt', red)
    addContacts(contactdir + '/bipolar_blender.txt', blue)
    addContacts(contactdir + '/monopolar_start_blender.txt', green)

    for o in bpy.data.objects:
        o.b4w_selectable=True
        o.b4w_outlining=True
        o.b4w_do_not_batch=True

    # here comes the sun!
    bpy.ops.object.lamp_add(
        type='SUN',
        location = (7.48113, -6.50764, 5.34367)
    )
    bpy.context.active_object.name = 'Sun'

    # final camera position may need manual inspection and tweaking
    bpy.ops.object.camera_add(
        location = (-8.4, 1.3, 1.7),
        rotation = (64.202362, 0.013625, 48.533962)
    )
    bpy.context.active_object.name = 'Camera'

    # save .blend file and export .json file
    blend_outfile = outdir + '/iEEG_surface.blend'
    bpy.ops.wm.save_mainfile(filepath=blend_outfile)

    json_outfile = outdir + '/iEEG_surface.json'
    bpy.ops.export_scene.b4w_json(filepath=json_outfile)
    return

def addContacts(contactpath, color):
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
            setMaterial(ob, color)


def makeMaterial(name, diffuse, specular, alpha):
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

def setMaterial(ob, mat):
    me = ob.data
    me.materials.append(mat)

if __name__ == "__main__":
    # get the args passed to blender after "--", all of which are ignored by
    # blender so scripts may receive their own arguments
    args = sys.argv

    if "--" not in args:
        args = []  # as if no args are passed
    else:
        args = args[args.index("--") + 1:]  # get all args after "--"

    subject = args[0]
    subject_num = args[1]
    cortex = args[2]
    contact = args[3]
    output = args[4]

    generate_brain_image(subject, subject_num, cortex, contact, output)

