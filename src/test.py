import os
import shutil
import subprocess

TESTDIR = os.path.dirname(os.path.abspath('__file__'))


def build_directories(subject, subject_num):
    base = TESTDIR + '/../test_data/{}'.format(subject)
    cortex = base + '/surf/roi'
    contact = base + '/coords'
    tal = base + '/tal'
    output = TESTDIR + '/../test_data/{}/iEEG_surface'.format(subject_num)

    return base, cortex, contact, tal, output


def run_task(subject, subject_num, task, base, cortex, contact, tal, output):
    assert os.path.exists(base)
    assert os.path.exists(contact)
    assert os.path.exists(tal)

    subprocess.run('PYTHONPATH="../src/" luigi --module pipeline {} --local-scheduler\
                   --SUBJECT {}\
                   --BASE {}\
                   --CORTEX {}\
                   --CONTACT {}\
                   --TAL {}\
                   --OUTPUT {}'.format(task, subject, base, cortex, contact, tal, output),
                   check=True,
                   shell=True,
                   stdout=subprocess.PIPE)
    return

def test_can_start():
    subject = 'R1291M_1'
    subject_num = '291_1'
    base, cortex, contact, tal, output = build_directories(subject, subject_num)
    run_task(subject, subject_num, 'CanStart', base, cortex, contact, tal, output)
    return

def test_freesurfer_to_wavefront():
    subject = 'R1291M_1'
    subject_num = '291_1'
    base, cortex, contact, tal, output = build_directories(subject, subject_num)
    run_task(subject, subject_num, 'FreesurferToWavefront', base, cortex, contact, tal, output)
    assert os.path.exists(cortex)
    assert os.path.exists(cortex + '/lh.pial.obj')
    assert os.path.exists(cortex + '/rh.pial.obj')

    shutil.rmtree(cortex)

    return

def test_split_cortical_surface():
    subject = 'R1291M_1'
    subject_num = '291_1'
    base, cortex, contact, tal, output = build_directories(subject, subject_num)
    run_task(subject, subject_num, 'SplitCorticalSurface', base, cortex, contact, tal, output)

    assert os.path.exists(cortex + '/lh.Insula.obj')

    shutil.rmtree(cortex)

    return

def test_gen_coordinates():
    subject = 'R1291M_1'
    subject_num = '291_1'
    base, cortex, contact, tal, output = build_directories(subject, subject_num)
    run_task(subject, subject_num, 'GenElectrodeCoordinatesAndNames', base, cortex, contact, tal, output)

    assert os.path.exists(contact + '/monopolar_start_blender.txt')
    assert os.path.exists(contact + '/monopolar_blender.txt')
    assert os.path.exists(contact + '/bipolar_blender.txt')
    assert os.path.exists(contact + '/monopolar_start_names.txt')
    assert os.path.exists(contact + '/monopolar_names.txt')
    assert os.path.exists(contact + '/bipolar_names.txt')

    os.remove(contact + '/monopolar_start_blender.txt')
    os.remove(contact + '/monopolar_blender.txt')
    os.remove(contact + '/bipolar_blender.txt')
    os.remove(contact + '/monopolar_start_names.txt')
    os.remove(contact + '/monopolar_names.txt')
    os.remove(contact + '/bipolar_names.txt')

    return


def test_build_blender_site():
    subject = 'R1291M_1'
    subject_num = '291_1'
    base, cortex, contact, tal, output = build_directories(subject, subject_num)
    run_task(subject, subject_num, 'BuildBlenderSite', base, cortex, contact, tal, output)

    assert os.path.exists(output + '/iEEG_surface.html')
    assert os.path.exists(output + '/iEEG_surface.js')
    assert os.path.exists(output + '/monopolar_names.txt')
    assert os.path.exists(output + '/monopolar_start_names.txt')
    assert os.path.exists(output + '/bipolar_names.txt')

    shutil.rmtree(output)

    return


def test_gen_blender_scene():
    subject = 'R1291M_1'
    subject_num = '291_1'
    base, cortex, contact, tal, output = build_directories(subject, subject_num)
    run_task(subject, subject_num, 'GenBlenderScene', base, cortex, contact, tal, output)

    assert os.path.exists(output + '/iEEG_surface.blend')
    assert os.path.exists(output + '/iEEG_surface.bin')
    assert os.path.exists(output + '/iEEG_surface.json')

    shutil.rmtree(output)

    return
