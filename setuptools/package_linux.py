import os
import sys
import subprocess
import shutil
import datetime
import traceback
import optparse
import platform

from utils import *
from qtinfo import QtInfo


def make_package(pkg_version, script_dir, modules_dir, install_dir, py_version,
    pack_examples, qtinfo, logger):
    raise NotImplementedError()
