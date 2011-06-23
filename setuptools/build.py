import sys
import os
import stat
import errno
import shutil
import subprocess
import optparse
import traceback
import distutils.sysconfig

from utils import *
from qtinfo import QtInfo


PYSIDE_VERSION = "1.0.4"


# Modules
modules = {
    'dev': [
        ["apiextractor", "master", "https://github.com/PySide/Apiextractor.git"],
        ["generatorrunner", "master", "https://github.com/PySide/Generatorrunner.git"],
        ["shiboken", "master", "https://github.com/PySide/Shiboken.git"],
        ["pyside", "master", "https://github.com/PySide/PySide.git"],
        ["pyside-tools", "master", "https://github.com/PySide/Tools.git"],
    ],
    'stable': [
        ["apiextractor", "0.10.4", "https://github.com/PySide/Apiextractor.git"],
        ["generatorrunner", "0.6.11", "https://github.com/PySide/Generatorrunner.git"],
        ["shiboken", "1.0.4", "https://github.com/PySide/Shiboken.git"],
        ["pyside", "1.0.4", "https://github.com/PySide/PySide.git"],
        ["pyside-tools", "0.2.10", "https://github.com/PySide/Tools.git"],
    ],
}


# Change the cwd to our source dir
try:
    this_file = __file__
except NameError:
    this_file = sys.argv[0]
this_file = os.path.abspath(this_file)
if os.path.dirname(this_file):
    os.chdir(os.path.dirname(this_file))


def check_env(download):
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


def process_modules(download, modules, modules_dir, install_dir, qtinfo, py_include_dir, py_library):
    if os.path.exists(install_dir):
        print "Deleting install folder %s..." % install_dir
        rmtree(install_dir)
    print "Creating install folder %s..." % install_dir
    os.mkdir(install_dir)
    
    for module in modules:
        process_module(download, module, modules_dir, install_dir, qtinfo, py_include_dir, py_library)


def process_module(download, module, modules_dir, install_dir, qtinfo, py_include_dir, py_library):
    module_name = module[0]
    print "Processing module %s..." % module_name
    
    if not os.path.exists(modules_dir):
        os.mkdir(modules_dir)
    os.chdir(modules_dir)
    
    if download:
        if os.path.exists(module_name):
            print "Deleting module folder %s..." % module_name
            rmtree(module_name)
        
        # Clone sources from git repository
        repo = module[2]
        print "Downloading " + module_name + " sources at " + repo
        if run_process("git", "clone", repo) != 0:
            raise Exception("Error cloning " + repo)
        os.chdir(modules_dir + "/" + module_name)
    
        # Checkout branch
        branch = module[1]
        print "Changing to branch " + branch + " in " + module_name
        if run_process("git", "checkout", branch) != 0:
            raise Exception("Error changing to branch " + branch + " in " + module_name)
    
    build_dir = os.path.join(os.path.join(modules_dir, module_name),  "build")
    if os.path.exists(build_dir):
        print "Deleting build folder %s..." % build_dir
        rmtree(build_dir)
    print "Creating build folder %s..." % build_dir
    os.mkdir(build_dir)
    os.chdir(build_dir)
    
    # Compile
    if sys.platform == "win32":
        cmake_generator = "NMake Makefiles"
        make_cmd = "nmake"
    else:
        cmake_generator = "Unix Makefiles"
        make_cmd = "make"
    
    print "Configuring " + module_name + " in " + os.getcwd() + "..."
    args = [
        "cmake",
        "-G", cmake_generator,
        "-DQT_QMAKE_EXECUTABLE=%s" % qtinfo.qmake_path,
        "-DBUILD_TESTS=False",
        "-DPYTHON_EXECUTABLE=%s" % sys.executable,
        "-DPYTHON_INCLUDE_DIR=%s" % py_include_dir,
        "-DPYTHON_LIBRARY=%s" % py_library,
        "-DCMAKE_BUILD_TYPE=Release",
        "-DCMAKE_INSTALL_PREFIX=%s" % install_dir,
        ".."
    ]
    if module_name == "generatorrunner":
        args.append("-DCMAKE_INSTALL_RPATH_USE_LINK_PATH=yes")
    if run_process(*args) != 0:
        raise Exception("Error configuring " + module_name)
    
    print "Compiling " + module_name + "..."
    if run_process(make_cmd) != 0:
        raise Exception("Error compiling " + module_name)
    
    print "Testing " + module_name + "..."
    if run_process("ctest") != 0:
        print "Some " + module_name + " tests failed!"
    
    print "Installing " + module_name + "..."
    if run_process(make_cmd, "install/fast") != 0:
        raise Exception("Error pseudo installing " + module_name)


def main():
    try:
        optparser = optparse.OptionParser(usage="create_package [options]", version="PySide package creator")
        optparser.add_option("-e", "--check-environ", dest="check_environ",                         
                             action="store_true", default=False, help="Check the environment")
        optparser.add_option("-q", "--qmake", dest="qmake_path",                         
                             default=None, help="Locate qmake")
        optparser.add_option("-d", "--download", dest="download",
                             action="store_true", default=False, help="Download sources from git repository")
        optparser.add_option("-m", "--pyside-version", dest="pyside_version",
                             default="stable", help="Specify what version of modules to download from git repository: 'dev' or 'stable'. Default is 'stable'.")
        optparser.add_option("-p", "--package-version", dest="package_version",
                             default=PYSIDE_VERSION, help="Specify package version. Default is %s" % PYSIDE_VERSION)
        options, args = optparser.parse_args(sys.argv)
        
        py_version = "%s.%s" % (sys.version_info[0], sys.version_info[1])
        
        py_include_dir = distutils.sysconfig.get_config_var("INCLUDEPY")
        
        py_prefix = distutils.sysconfig.get_config_var("prefix")
        if sys.platform == "win32":
            py_library = os.path.join(py_prefix, "libs/python%s.lib" % py_version.replace(".", ""))
        else:
            py_library = os.path.join(py_prefix, "lib/libpython%s.so" % py_version)
        if not os.path.exists(py_library):
            print "Failed to locate the Python library %s" % py_library
        
        if not modules.has_key(options.pyside_version):
            print "Invalid pyside version specified [%s]. Available options: [%s]" % \
                (options.pyside_version, ', '.join(modules.keys()))
            sys.exit(1)
        
        script_dir = os.getcwd()
        
        modules_dir = os.path.join(script_dir, "modules")
        
        qtinfo = QtInfo(options.qmake_path)
        if not qtinfo.qmake_path or not os.path.exists(qtinfo.qmake_path):
            print "Failed to find qmake. Please specify the path to qmake with --qmake parameter."
            sys.exit(1)
        
        # Add path to this version of Qt to environment if it's not there.
        # Otherwise the "generatorrunner" will not find the Qt libraries
        paths = os.environ['PATH'].lower().split(os.pathsep)
        qt_dir = os.path.dirname(qtinfo.qmake_path)
        if not qt_dir.lower() in paths:
            print "Adding path \"%s\" to environment" % qt_dir
            paths.append(qt_dir)
        os.environ['PATH'] = os.pathsep.join(paths)
        
        if not qtinfo.version:
            print "Failed to query the Qt version with qmake %s" % qtinfo.qmake_path
            sys.exit(1)
        
        install_dir = os.path.join(script_dir, "install-py%s-qt%s") % (py_version, qtinfo.version)
        
        print "------------------------------------------"
        print "Generate package version: %s" % options.package_version
        if options.download:
            print "Download modules version: %s" % options.pyside_version
        print "Python version: %s" % py_version
        print "Python executable: %s" % sys.executable
        print "Python includes: %s" % py_include_dir
        print "Python library: %s" % py_library
        print "Script directory: %s" % script_dir
        print "Modules directory: %s" % modules_dir
        print "Install directory: %s" % install_dir
        print "qmake path: %s" % qtinfo.qmake_path
        print "Qt version: %s" % qtinfo.version
        print "Qt bins: %s" % qtinfo.bins_dir
        print "Qt plugins: %s" % qtinfo.plugins_dir
        print "------------------------------------------"
        
        check_env(options.download)
        if options.check_environ:
            return
        
        process_modules(options.download, modules[options.pyside_version], modules_dir, install_dir, qtinfo, py_include_dir, py_library)
        
        if options.package_version is not None:
            from package import make_package
            make_package(options.package_version, script_dir, modules_dir, install_dir, py_version, qtinfo)
    
    except Exception, e:
        print traceback.print_exception(*sys.exc_info())
        sys.exit(1)
    
    sys.exit(0)


if __name__ == "__main__":
    main()
