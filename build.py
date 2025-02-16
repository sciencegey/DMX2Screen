# This build file is designed to be used with cx_freeze (version 6.12 as of writing).
# Install cx_freeze https://cx-freeze.readthedocs.io/en/stable/ then simply run:
# "python build.py build"

import sys
from cx_Freeze import setup, Executable

build_exe_options = {"includes": ["numpy","cv2"], "include_files":["config.ini","fixtures/"], "build_exe": "build\\DMX2Screen"}

base = None

setup(name = "DMX2Screen",
    version = "0.3.0",
    description = "https://github.com/sciencegey/DMX2Screen",
    options = {"build_exe": build_exe_options},
    executables = [Executable("main.py", base=base, target_name="DMX2Screen")])