import os
import shutil
import subprocess

TESTDIR = os.path.dirname(os.path.abspath('__file__'))


def build_directories(subject, subject_num):
    base = TESTDIR + '/../test_data/{}'.format(subject)
    cortex = base + '/surf/roi'
    contact = base + '/coords'
    tal = base + '/tal'
    output = TESTDIR + '/../{}/iEEG_surface'.format(subject_num)

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
