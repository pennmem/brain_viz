# 3-D Brain Visualization Pipeline
This repository contains source code for generating web-based 3D brain visualizations of localized surface and depth electrodes for RAM subjects. At a high level, the following steps are taken in order to build these visualizations:

1. Convert object files from freesurfer to Wavefront format
2. Split the cortical surface into independent regions
3. Build underlying data files
4. Create the blender scene and required files for the web viewer

The final output can be viewed in two ways:
1. Access the publicly-available standalone web page for a particular subject: http://memory.psych.upenn.edu/public/reports/r1/subjects/[SUBJECT_NUM]/iEEG_surface/iEEG_surface.html
2. Access the privately-hosted CML web app from the UPenn network: http://rhino2.psych.upenn.edu:8080/brain/

The public and private views use the same underlying data, but the views may be slightly different because the UI for the privately-hosted web app is built dynamically to only display UI elements relevant to the contents of the underlying blender file. For example, if prior stim locations are unavailable for a subject, that UI button will not be displayed. In contrast, the standalone public versions display all UI elements by default.

## Installation
The current pipeline uses the following tools to build the 3D visualizations

- ANTS
- Freesurfer
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


## Running
The easiest way to build a new visualization is through the web application: http://rhino2.psych.upenn.edu:8080/brain/build

However, this option requires that the user be located on the UPenn network and have been provided login credentials for trigger brain visualization builds.

If all dependencies are successfully installed, the pipeline can be triggered using the luigi CLI. For example, to trigger building a 3D localization visualization for R1001P, you would execute the following from the same directory as the README:


```PYTHONPATH="." luigi --module src.pipeline GenBlenderScene --SUBJECT R1001P --SUBJECT-NUM 001 --local-scheduler```

## Testing
From the same directory as the README:
1. Execute all unit and functional tests: ```pytest tests/```
2. Include coverage report: ```py.test --cov-report html --cov=brain_viz tests/```

The full testing suite takes between 30 and 40 minutes to run. The primary bottleneck is the functional test of the part in the pipeline where all previous stimulated contact locations are mapped from one subject's space to anothers. To dramatically cut down the testing time, ignore the test_pipeline module.

## Details

## External Links
- [Old Instructions for Building Manually](https://memory.psych.upenn.edu/InternalWiki/Electrode_Visualizations_using_Blender_and_Blend4Web)
- [General Information about the Localization Pipeline](https://memory.psych.upenn.edu/InternalWiki/Neuroradiology_Core)

