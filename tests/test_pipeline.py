import os
import pytest
import shutil
import subprocess

TESTDIR = os.path.dirname(os.path.abspath('__file__'))


def build_directories(subject, subject_num):
    base = TESTDIR + '/test_data/{}'.format(subject)
    cortex = base + '/surf/roi'
    contact = base + '/coords'
    tal = base + '/tal'
    output = TESTDIR + '/test_data/{}/iEEG_surface'.format(subject_num)

    return base, cortex, contact, tal, output

def cleanup(cortex, contact, output):
    """ Cycle through subject directory and remove files created as part of pipeline """
    if os.path.exists(output):
        shutil.rmtree(output)

    if os.path.exists(cortex):
        shutil.rmtree(cortex)

    for coor_file in ["/monopolar_start_blender.txt", "/monopolar_blender.txt",
                      "/bipolar_blender.txt", "/monopolar_start_names.txt",
                      "/monopolar_names.txt", "/bipolar_names.txt"]:
        if os.path.exists(contact + coor_file):
            os.remove(contact + coor_file)

    return


def run_task(subject, subject_num, task, base, cortex, contact, tal, output):
    assert os.path.exists(base)
    assert os.path.exists(contact)
    assert os.path.exists(tal)
    command = 'PYTHONPATH="." luigi --module src.pipeline {} --local-scheduler\
               --SUBJECT {}\
               --SUBJECT-NUM {}\
               --BASE {}\
               --CORTEX {}\
               --CONTACT {}\
               --TAL {}\
               --OUTPUT {}'.format(task, subject, subject_num, base, cortex, contact, tal, output)
    subprocess.run(command,
                   check=True,
                   shell=True,
                   stdout=subprocess.PIPE)
    return

@pytest.mark.parametrize("subject,subject_num",[("R1291M_1","291_1")])
def test_can_start(subject, subject_num):
    base, cortex, contact, tal, output = build_directories(subject, subject_num)
    cleanup(cortex, contact, output)
    run_task(subject, subject_num, 'CanStart', base, cortex, contact, tal, output)
    return

@pytest.mark.parametrize("subject,subject_num",[("R1291M_1","291_1")])
def test_freesurfer_to_wavefront(subject, subject_num):
    base, cortex, contact, tal, output = build_directories(subject, subject_num)
    #cleanup(cortex, contact, output)
    run_task(subject, subject_num, 'FreesurferToWavefront', base, cortex, contact, tal, output)

    assert os.path.exists(cortex)
    assert os.path.exists(cortex + '/lh.pial.obj')
    assert os.path.exists(cortex + '/rh.pial.obj')

    return

@pytest.mark.parametrize("subject,subject_num",[("R1291M_1","291_1")])
def test_split_cortical_surface(subject, subject_num):
    base, cortex, contact, tal, output = build_directories(subject, subject_num)
    #cleanup(cortex, contact, output)
    run_task(subject, subject_num, 'SplitCorticalSurface', base, cortex, contact, tal, output)

    assert os.path.exists(cortex + '/lh.Insula.obj')

    return

@pytest.mark.parametrize("subject,subject_num",[("R1291M_1","291_1")])
def test_gen_coordinates(subject, subject_num):
    base, cortex, contact, tal, output = build_directories(subject, subject_num)
    #cleanup(cortex, contact, output)
    run_task(subject, subject_num, 'GenElectrodeCoordinatesAndNames', base, cortex, contact, tal, output)

    assert os.path.exists(contact + '/electrode_coordinates.csv')

    return

@pytest.mark.parametrize("subject,subject_num",[("R1291M_1","291_1")])
def test_build_blender_site(subject, subject_num):
    subject = 'R1291M_1'
    subject_num = '291_1'
    base, cortex, contact, tal, output = build_directories(subject, subject_num)
    #cleanup(cortex, contact, output)
    run_task(subject, subject_num, 'BuildBlenderSite', base, cortex, contact, tal, output)

    assert os.path.exists(output + '/iEEG_surface.html')
    assert os.path.exists(output + '/iEEG_surface.js')

    return

@pytest.mark.parametrize("subject,subject_num",[("R1291M_1","291_1")])
def test_gen_blender_scene(subject, subject_num):
    base, cortex, contact, tal, output = build_directories(subject, subject_num)
    #cleanup(cortex, contact, output)
    run_task(subject, subject_num, 'GenBlenderScene', base, cortex, contact, tal, output)

    assert os.path.exists(output + '/iEEG_surface.blend')
    assert os.path.exists(output + '/iEEG_surface.bin')
    assert os.path.exists(output + '/iEEG_surface.json')

    return

@pytest.mark.parametrize("subject,subject_num",[("R1291M_1","291_1")])
def test_gen_avg_brain(subject, subject_num):
    cortex = TESTDIR + "/average/surf/roi/"
    output = TESTDIR + "/avg/iEEG_surface/"

    # Cleanup
    if os.path.exists(output) == True:
        shutil.rmtree(output)

    command = 'PYTHONPATH="." luigi --module src.pipeline BuildPriorStimAvgBrain --local-scheduler\
               --AVG-ROI {}\
               --OUTPUT {}'.format(cortex, output)
    subprocess.run(command,
                   check=True,
                   shell=True,
                   stdout=subprocess.PIPE)

    assert os.path.exists(output + 'iEEG_surface.blend')
    assert os.path.exists(output + 'iEEG_surface.bin')
    assert os.path.exists(output + 'iEEG_surface.json')

    return
