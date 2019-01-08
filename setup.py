"""
Setup script for prolix
"""
import glob
import os
import shutil
import stat
import sys
from collections import defaultdict
from os.path import join, exists, isdir

try:  # not running python 3, will raise an error later on
    from pathlib import Path
except ImportError:
    pass

from setuptools import setup
from setuptools.command.develop import develop

# define python versions

python_version = (3, 6)  # tuple of major, minor version requirement
python_version_str = str(python_version[0]) + "." + str(python_version[1])

# produce an error message if the python version is less than required
if sys.version_info < python_version:
    msg = "prolix only runs on python version >= %s" % python_version_str
    raise Exception(msg)

# get path references
here = Path(__file__).absolute().parent
version_file = here / "prolix" / "version.py"

# --- get version
with version_file.open() as fi:
    content = fi.read().split("=")[-1].strip()
    __version__ = content.replace('"', "").replace("'", "")


# --- get readme
with open("README.md") as readme_file:
    readme = readme_file.read()


# --- get sub-packages
def find_packages(base_dir="."):
    """ setuptools.find_packages wasn't working so I rolled this """
    out = []
    for fi in glob.iglob(join(base_dir, "**", "*"), recursive=True):
        if isdir(fi) and exists(join(fi, "__init__.py")):
            out.append(fi)
    out.append(base_dir)
    return out


def get_package_data_files():
    """ Gets data """
    data_path = Path("prolix") / "data"
    return list(data_path.rglob('*'))


# --- requirements paths


def read_requirements(path):
    """ Read a requirements.txt file, return a list. """
    with Path(path).open("r") as fi:
        return fi.readlines()


package_req_path = here / "requirements.txt"
test_req_path = here / "tests" / "requirements.txt"


ENTRY_POINTS = {
    'console_scripts': [
        'prolix = prolix.cli:dispatch_cli',
    ]
}

setup(
    name="prolix",
    version=__version__,
    description="program to learn vocab words",
    long_description=readme,
    author="Derrick Chambers",
    author_email="djachambeador@gmail.com",
    url="https://github.com/d-chambers/prolix",
    packages=find_packages("prolix"),
    package_dir={"prolix": "prolix"},
    entry_points=ENTRY_POINTS,
    include_package_data=True,
    data_files=get_package_data_files(),
    license="GNU Public License v3.0 or later (GPLv3.0+)",
    zip_safe=False,
    keywords="vocabulary",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: GNU Public License v3 or later (GPLv3+)",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Topic :: English",
    ],
    test_suite="tests",
    install_requires=read_requirements(package_req_path),
    tests_require=read_requirements(test_req_path),
    setup_requires=["pytest-runner>=2.0"],
    python_requires=">=%s" % python_version_str,
)
