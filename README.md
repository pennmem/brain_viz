# 3-D Brain Visualization Pipeline
This repository contains the pipeline code for generating all of the underlying
files necessary to produce a 3D rendering of a RAM subject's brain. This
code is highly dependent upon RHINO and is therefore unlikely to be useful
outside of CML without significant modification and effort.

## Brief History
Version 1.0 of the pipeline used [luigi](https://github.com/spotify/luigi) for
the pipeline framework. Pipelines could be triggered from the CML web-app, which
used a home-grown messaging service to pass the request along, ultimately
triggering a subprocess call.

Version 2.0 of the pipeline uses the Dask + Joblib framework from the
[cml_pipelines](https://github.com/pennmem/cml_pipelines) repository. Pipelines
can still be triggered from the CML web-app. Instead of using a home-grown
solution, we now leverage Celery + RabbitMQ to execute the pipeline.
Alternatively, users can use the command line interface to initiate a pipeline.
This is the same as how web-based reports are produced. The intention of
version 2.0 is to reduce the complexity of getting the various services up and
running by re-using the same pipeline and task execution framework as for
web-based reports. The downside to this approach is that the cml_pipelines
framework is more suited towards computational pipelines and not I/O heavy
pipelines.


## Installation

First time installation requires additional setup because the pipeline depends
on the following software:

- ANTS
- Freesurfer
- c3D
- Matlab Runtime (MCR)
- Blender
- Blend4Web SDK

However, once the environment has been set up, it is easiest to install updates
through conda. Some of these external tools are installed globally on RHINO (freesurfer, Blender,
and Blend4Web SDK) and require no additional installation effort. There are some
utility scripts for installing the dependencies included in the scripts/
folder of this repository. The pipeline requires a very specific version of
ANTS. At one point we attempted to use a version that is publicly-available and
the code no longer functioned, so we remain dependent on the version of ANTS
that was installed by a specific user. c3D and the matlab runtime can be
installed using the provided utility scripts. While it would be ideal to
eliminate the dependency on a matlab runtime, it continues to exist because it
would have taken considerable time to port over all of the matlab code used by
the the annot2dpv, splitsrf, and srf2obj binaries that were compiled from a set
of matlab scripts. At the very least, the runtime is free to install, so the
pipeline is no longer dependent on a paid matlab subscription.

For first time installation, start by cloning the repository and creating a new
conda environment:

```
git clone https://github.com/pennmem/brain_viz.git
conda create -y -n brainviewer python=3
conda install -c pennmem -c conda-forge --file=requirements.txt
source  activate brainviewer
```

Next, run the provided setup script, which will install c3d and the matlab
runtime. Note: all following commands assume you have cloned the repository
into your home directory:

```bash
cd ~/brain_viz/brainviewer/scripts
./setup.sh
```

You should now have all of the necessary dependencies installed assuming that
you are working form RHINO, which already has Freesurfer and Blender installed
globally. If you are setting this up for the first time outside of the CML,
then follow the [Freesufer Installation Instructions](https://surfer.nmr.mgh.harvard.edu/fswiki/DownloadAndInstall)
and run the provided install_blender.sh script included with this repository.
Note: you will also need to update the environment variables for Freesurfer
and blender contained in setup_environment.sh base on how you set up your
system.

Since some of the dependencies have been installed locally, use the
setup_environment.sh script to add some locations to your PATH and set a few
other environment variables that are necessary for the matlab runtime to
function properly.

```bash
source ~/brain_viz/brainviewer/scripts/setup_environment.sh
```

Note: overriding the default LD_LIBRARY_PATH environment variable
(as this setup script does) will wreak havoc on your environment, so
this should only be done while the processing pipeline is being used. For
example, pushing/pulling to remote git repositories will stop working, so if
you notice odd behavior after using the pipeline code, check to see if this
environment variable matches what was set in setup_environment.sh. After
running the environment setup script, check that the required binaries are
available. As a sanity check, each of the following binaries should be found:

```
which blender
which c3d
which mris_convert
```

If all of those binaries are available, you can now install the brainviewer
package locally and test it out:

```bash
source activate brainviewer
cd ~/brain_viz
python setup.py install
```

The brainviewer pipeline uses a REST endpoint in the CML Web App to get the
locations of prior stim results. Check that the two services are
communicating correctly. This test assumes the web application is being
served from RHINO on port 8083:

```bash
curl "http://rhino2.psych.upenn.edu:8083/explorer/1/stream?format=csv&token=CML"
```

A comma-delimited set of values should be returned. For additional checks,
follow the "Testing" section below.


After this initial setup has been complete, the pipeline code can be installed
and updated from conda:

```
source activate brainviewer
conda install -c pennmem brainviewer

# updating
conda update -c pennmem brainviewer
```

## Building or Updating the Average Brain

Updates a CSV file containing the freesurfer average coordinates of all
prior stim sites. If specified, the blender scene for the average brain will be
re-generated using the current snapshot of prior stim sites.

```
usage: build-average-brain [-h] [--blender] [--force]

optional arguments:
  -h, --help     show this help message and exit
  --blender, -b  Generate Blender standalone 3D viewer
  --force, -f    Overwrite blender files if they exist
```

## Building a subject-specific 3D brain

As part of the [neurorad pipeline](https://github.com/pennmem/neurorad_pipeline)
files are produced using freesurfer that allow for reconstructing a 3D
representation of an individual's brain. At a high level, this pipeline does
the following:

- Converts freesurfer-specific files for constructing 3D representations into
  a more general wavefront .obj format that can be used by most 3D graphics
  applications such as blender, Unity, etc.
- Splits left and right hemisphere objects into smaller parcellations based on
  the Desikan-Killany and Human Connectome Project atlases
- Maps the coordinates of prior stim sites into mni space and then into this
  particular subject's coordinate space
- Optionally builds the blender scene that combines the different 3D objects,
  prior stimulation sites, and implanted electrodes

```
usage: build-subject-brain [-h] [--subject SUBJECT]
                           [--localization LOCALIZATION] [--blender] [--force]

optional arguments:
  -h, --help            show this help message and exit
  --subject SUBJECT, -s SUBJECT
                        Subject ID
  --localization LOCALIZATION, -l LOCALIZATION
                        Localization number
  --blender, -b         Generate Blender standalone 3D viewer
  --force, -f           Overwrite blender files if they exist
```

## Testing
Pytest is currently used as the unit testing framework. In order to run the
tests, first update the SUBJECTS_DIR environment variable in the pytest.ini
file. This environment variable is used by Freesurfer to determine where to
lookup/save files. In order to have unit tests that use freesurfer commands,
this must be overridden to point to the brainviewer/tests/data/ folder within
the repository, which is set up to mimic the directory structure assumed by
Freesurfer.

Next, get a copy of the test data. Some of the files are too large to be stored
in a git repository, so we maintain a copy of the necessary files in
`/scratch/zduey/brainviewer_test_data/.` Copy those files into
`brain_viz/brainviewer/tests/data/`.

```bash
cp /scratch/zduey/brainviewer_test_data/ ~/brain_viz/brainviewer/tests/data/
```

The tests require that the LD_LIBRARY_PATH and other environment variables
mentioned in the setup section have been set. If you receiving the following
error:

```error while loading shared libraries: libmwlaunchermain.so: cannot open shared object file: No such file or directory```

it is likely that those have not been correctly set. Temporarily set those
variables before running the test suite:

```bash
source ~/brain_viz/brainviewer/scripts/setup_environment.sh
```

If running the tests from RHINO, do so from a Qlogin session:

```bash
qlogin
source activate brainviewer
source ~/brain_viz/brainviewer/scripts/setup_environment.sh
pytest brainviewer/ --rhino-root /
```

## External Links
- [Old Instructions for Building Manually](https://memory.psych.upenn.edu/InternalWiki/Electrode_Visualizations_using_Blender_and_Blend4Web)
- [General Information about the Localization Pipeline](https://memory.psych.upenn.edu/InternalWiki/Neuroradiology_Core)

