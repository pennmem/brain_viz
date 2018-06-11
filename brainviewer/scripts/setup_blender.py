""" Basic setup script for setting some variables in the Blender runtime

This python script is run using Blender's python runtime

"""
import os
import bpy
from bpy import context

path = os.path.expanduser("~/bin/blend4web_ce/")
context.user_preferences.filepaths.script_directory = path
bpy.ops.wm.save_userpref()
