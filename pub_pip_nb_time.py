
import os
import sys
import shutil

# Ensure dependencies
# os.system(f"{sys.executable} -m pip install --user --upgrade setuptools wheel twine")

# Delete previous build
import time
import git_nb_time_github

shutil.rmtree("dist", ignore_errors=True)

# Build
os.system(f"{sys.executable} setup.py sdist bdist_wheel")

# Upload
os.system(f"{sys.executable} -m twine upload dist/*")

shutil.rmtree("build", ignore_errors=True)



time.sleep(100000)

