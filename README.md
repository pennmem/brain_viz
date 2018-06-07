# 3-D Brain Visualization Pipeline
This repository contains the pipeline code for generating all of the underlying
files necessary to produce a 3D rendering of a RAM subject's brain.

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
running by re-using the same pipelining and task execution framework as for
web-based reports. The downside to this approach is that the cml_pipelines
framework is more suited towards computational pipelines and not I/O heavy
pipelines.

## Installation

The brainviewer pipeline code can be installed from conda:

```
conda env create -y -n brainviewer python=3
conda install -c pennmem brainviewer
```



## Overview
1. Convert object files from freesurfer to Wavefront format
2. Split the cortical surface into independent regions
3. Build underlying data files
4. Create the blender scene and required files for the web viewer

The final output can be viewed in two ways:
1. Access the publicly-available standalone web page for a particular subject (ex: [341](http://memory.psych.upenn.edu/public/reports/r1/subjects/341/reports/iEEG_surface/iEEG_surface.html))
2. Access the privately-hosted [CML web app](http://rhino2.psych.upenn.edu:8080/brain/) from the UPenn network 

The public and private views use the same underlying data, but the views may be slightly different because the UI for the privately-hosted web app is built dynamically to only display UI elements relevant to the contents of the underlying blender file. For example, if prior stim locations are unavailable for a subject, that UI button will not be displayed. In contrast, the standalone public versions display all UI elements by default.

## Installation
The current pipeline uses the following tools to build the 3D visualizations

- ANTS
- Freesurfer
- c3D
- Octave (to be removed)
- Blender
- Blend4Web SDK
- Python

To install the necessary python dependencies, use conda environments

```conda create -f environment.yml```

Activate the environment:

```source activate brain_viz```

Once the baseline set of packages are installed, you will need to install PTSA separately:

 ```conda install -c pennmem ptsa```
 
 There are two places where paths are hard-coded. Both are related to logging. Update the logging_conf_file field in luigi.cfg.
 This file should point to the logging.conf file in your local repository. Next, update the args() field in the handler_outfile
 section of the logging.conf file. The first argument should point to a location on disk where the logs from the luigi tasks
 should be stored.


## Running
The easiest way to build a new visualization is through the [web application](http://rhino2.psych.upenn.edu:8080/brain/build). However, this option requires that the user be located on the UPenn network and have been provided login credentials for trigger brain visualization builds.

If all dependencies are successfully installed, the pipeline can be triggered using the luigi CLI. For example, to trigger building a 3D localization visualization for R1001P, you would execute the following from the same directory as the README:


```PYTHONPATH="." luigi --module src.pipeline GenBlenderScene --SUBJECT R1001P --SUBJECT-NUM 001 --local-scheduler```

## Testing
Download test data from RHINO. Update pytest.ini with your full path to
the mock directory structure.

pytest brainviewer/ -x

From the same directory as the README:
1. Execute all unit and functional tests: ```pytest tests/```
2. Include coverage report: ```pytest tests/ --cov-report html --cov=src ```

The full testing suite takes between 30 and 40 minutes to run. The primary bottleneck is the functional test of the part in the pipeline where all previous stimulated contact locations are mapped from one subject's space to anothers. To dramatically cut down the testing time, ignore the test_pipeline module.

## External Links
- [Old Instructions for Building Manually](https://memory.psych.upenn.edu/InternalWiki/Electrode_Visualizations_using_Blender_and_Blend4Web)
- [General Information about the Localization Pipeline](https://memory.psych.upenn.edu/InternalWiki/Neuroradiology_Core)

