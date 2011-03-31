#
# create_package.py
#
# Author: Roman Lacko, backup.rlacko@gmail.com
#

import sys
import os
import shutil
import subprocess
import optparse
import traceback
import distutils.sysconfig
from package import create_package, run_process
from qtinfo import QtInfo, find_executable


# Constants
PKG_VERSION = "1.0.0"


# Modules
modules = [
    ["apiextractor", "master", "git://gitorious.org/pyside/apiextractor.git"],
    ["generatorrunner", "master", "git://gitorious.org/pyside/generatorrunner.git"],
    ["shiboken", "master", "git://gitorious.org/pyside/shiboken.git"],
    ["pyside", "master", "git://gitorious.org/pyside/pyside.git"],
    ["pyside-tools", "master", "git://gitorious.org/pyside/pyside-tools.git"],
]


# Globals
script_version = "PySide package creator version %s" % PKG_VERSION
py_version = "%s.%s" % (sys.version_info[0], sys.version_info[1])
py_include_dir = None
py_library = None
script_dir = None
modules_dir = None
output_dir = None
clean_output = False
download = False

# Change the cwd to our source dir
try:
    this_file = __file__
except NameError:
    this_file = sys.argv[0]
this_file = os.path.abspath(this_file)
if os.path.dirname(this_file):
    os.chdir(os.path.dirname(this_file))

def check_env():
    # Check if the required programs are on system path.
    requiredPrograms = [ "cmake" ];
    if download:
        requiredPrograms.append("git")
    if sys.platform == "win32":
        requiredPrograms.append("nmake")
    else:
        requiredPrograms.append("make")

    for prg in requiredPrograms:
        print "Checking " + prg + "..."
        f = find_executable(prg)
        if not f:
            print "You need the program \"" + prg + "\" on your system path to compile PySide."
            sys.exit(1)
        else:
            print 'Found %s' % f


def get_module(module):
    # Clone sources from git repository
    os.chdir(modules_dir)
    if os.path.exists(module[0]):
        if download:
            print "Deleting folder %s..." % module[0]
            shutil.rmtree(module[0], False)
        else:
            return
    repo = module[2]
    print "Downloading " + module[0] + " sources at " + repo
    if run_process("git", "clone", repo) != 0:
        raise Exception("Error cloning " + repo)


def compile_module(module):
    os.chdir(modules_dir + "/" + module[0])
    if os.path.exists("build") and clean_output:
        print "Deleting build folder..."
        shutil.rmtree("build", False)
    if not os.path.exists("build"):
        os.mkdir("build")
    os.chdir(modules_dir + "/" + module[0] + "/build")

    if modules_dir is None:
        print "Changing to branch " + branch + " in " + module[0]
        branch = module[1]
        if run_process("git", "checkout", branch) != 0:
            raise Exception("Error changing to branch " + branch + " in " + module[0])
    
    if sys.platform == "win32":
        cmake_generator = "NMake Makefiles"
        make_cmd = "nmake"
    else:
        cmake_generator = "Unix Makefiles"
        make_cmd = "make"
    
    print "Configuring " + module[0] + " in " + os.getcwd() + "..."
    args = [
        "cmake",
        "-G", cmake_generator,
        "-DQT_QMAKE_EXECUTABLE=%s" % qmake_path,
        "-DBUILD_TESTS=False",
        "-DPYTHON_EXECUTABLE=%s" % sys.executable,
        "-DPYTHON_INCLUDE_DIR=%s" % py_include_dir,
        "-DPYTHON_LIBRARY=%s" % py_library,
        "-DCMAKE_BUILD_TYPE=Release",
        "-DCMAKE_INSTALL_PREFIX=%s" % output_dir,
        ".."
    ]
    if module[0] == "generatorrunner":
        args.append("-DCMAKE_INSTALL_RPATH_USE_LINK_PATH=yes")
    if run_process(*args) != 0:
        raise Exception("Error configuring " + module[0])
    
    print "Compiling " + module[0] + "..."
    if run_process(make_cmd) != 0:
        raise Exception("Error compiling " + module[0])
    
    print "Testing " + module[0] + "..."
    if run_process("ctest") != 0:
        print "Some " + module[0] + " tests failed!"
    
    print "Installing " + module[0] + "..."
    if run_process(make_cmd, "install/fast") != 0:
        raise Exception("Error pseudo installing " + module[0])




def main():
    optparser = optparse.OptionParser(usage="create_package [options]", version=script_version)
    optparser.add_option("-e", "--check-environ", dest="check_environ",                         
                         action="store_true", default=False, help="Check the environment")
    optparser.add_option("-q", "--qmake", dest="qmake_path",                         
                         default=None, help="Locate qmake")
    optparser.add_option("-c", "--clean", dest="clean",
                         action="store_true", default=False, help="Clean build output")
    optparser.add_option("-d", "--download", dest="download",
                         action="store_true", default=False, help="Download latest sources from git repository")

    options, args = optparser.parse_args(sys.argv)

    try:
        # Setup globals
        global py_include_dir
        py_include_dir = distutils.sysconfig.get_config_var("INCLUDEPY")
        
        global py_library
        py_prefix = distutils.sysconfig.get_config_var("prefix")
        if sys.platform == "win32":
            py_library = os.path.join(py_prefix, "libs/python%s.lib" % py_version.replace(".", ""))
        else:
            py_library = os.path.join(py_prefix, "lib/libpython%s.so" % py_version)
        if not os.path.exists(py_library):
            print "Failed to locate the Python library %s" % py_library
        
        global script_dir
        script_dir = os.getcwd()
        
        global modules_dir
        modules_dir = os.path.join(script_dir, "modules")
        if not os.path.exists("modules"):
            os.mkdir(modules_dir)
        
        global qtinfo
        qtinfo = QtInfo(options.qmake_path)
        if not qtinfo.qmake_path or not os.path.exists(qinfo.qmake_path):
            print "Failed to find qmake. Please specify the path to qmake with --qmake parameter."
            sys.exit(1)
        
        # Add path to this version of Qt to environment if it's not there.
        # Otherwise the "generatorrunner" will not find the Qt libraries
        paths = os.environ['PATH'].lower().split(os.pathsep)
        qt_dir = os.path.dirname(qmake_path)
        if not qt_dir.lower() in paths:
            print "Adding path \"%s\" to environment" % qt_dir
            paths.append(qt_dir)
        os.environ['PATH'] = os.pathsep.join(paths)
        
        if not qtinfo.qt_version:
            print "Failed to query the Qt version with qmake %s" % qmake_path
            sys.exit(1)
               
        global clean_output
        clean_output = options.clean
        
        global download
        download = options.download
        
        global output_dir
        output_dir = os.path.join(modules_dir, "output-py%s-qt%s") % (py_version, qt_version)
        
        print "------------------------------------------"
        print "Python executable: %s" % sys.executable
        print "Python includes: %s" % py_include_dir
        print "Python library: %s" % py_library
        print "Script directory: %s" % script_dir
        print "Modules directory: %s" % modules_dir or "<git repository>"
        print "Output directory: %s" % output_dir
        print "Python version: %s" % py_version
        print "qmake path: %s" % qtinfo.qmake_path
        print "Qt version: %s" % qtinfo.version
        print "Qt bins: %s" % qtinfo.bins_dir
        print "Qt plugins: %s" % qtinfo.plugins_dir
        print "------------------------------------------"
        
        # Check environment
        check_env()
        
        if options.check_environ:
            return
        
        if os.path.exists(output_dir) and clean_output:
            print "Deleting output folder..."
            shutil.rmtree(output_dir, False)
        
        # Get and build modules
        for module in modules:
            get_module(module)
            compile_module(module)
        
        # Create python distribution package
        create_package(PKG_VERSION, script_dir, output_dir, py_version, qtinfo, True)
    
    except Exception, e:
        print traceback.print_exception(*sys.exc_info())
        sys.exit(1)
    
    sys.exit(0)


if __name__ == "__main__":
    main()
