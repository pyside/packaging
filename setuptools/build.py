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


PYSIDE_VERSION = "1.0.8"


# Modules
modules = {
    'dev': [
        ["Apiextractor", "master", "https://github.com/PySide/Apiextractor.git"],
        ["Generatorrunner", "master", "https://github.com/PySide/Generatorrunner.git"],
        ["Shiboken", "master", "https://github.com/PySide/Shiboken.git"],
        ["PySide", "master", "https://github.com/PySide/PySide.git"],
        ["Tools", "master", "https://github.com/PySide/Tools.git"],
    ],
    'stable': [
        ["Apiextractor", "0.10.8", "https://github.com/PySide/Apiextractor.git"],
        ["Generatorrunner", "0.6.14", "https://github.com/PySide/Generatorrunner.git"],
        ["Shiboken", "1.0.9", "https://github.com/PySide/Shiboken.git"],
        ["PySide", "1.0.8", "https://github.com/PySide/PySide.git"],
        ["Tools", "0.2.13", "https://github.com/PySide/Tools.git"],
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
        print("Checking " + prg + "...")
        f = find_executable(prg)
        if not f:
            print("You need the program \"" + prg + "\" on your system path to compile PySide.")
            sys.exit(1)
        else:
            print('Found %s' % f)


def process_modules(build_module, download, modules, modules_dir, install_dir, qtinfo, py_include_dir, py_library):
    if not os.path.exists(install_dir):
        print("Creating install folder %s..." % install_dir)
        os.mkdir(install_dir)
    
    for module in modules:
        if build_module is None or build_module.lower() == module[0].lower():
            process_module(download, module, modules_dir, install_dir, qtinfo, py_include_dir, py_library)


def process_module(download, module, modules_dir, install_dir, qtinfo, py_include_dir, py_library):
    module_name = module[0]
    print("Processing module %s..." % module_name)
    
    if not os.path.exists(modules_dir):
        os.mkdir(modules_dir)
    os.chdir(modules_dir)
    
    if download:
        if os.path.exists(module_name):
            print("Deleting module folder %s..." % module_name)
            rmtree(module_name)
        
        # Clone sources from git repository
        repo = module[2]
        print("Downloading " + module_name + " sources at " + repo)
        if run_process("git", "clone", repo) != 0:
            raise Exception("Error cloning " + repo)
        os.chdir(modules_dir + "/" + module_name)
    
        # Checkout branch
        branch = module[1]
        print("Changing to branch " + branch + " in " + module_name)
        if run_process("git", "checkout", branch) != 0:
            raise Exception("Error changing to branch " + branch + " in " + module_name)
    
    build_dir = os.path.join(os.path.join(modules_dir, module_name),  "build")
    if os.path.exists(build_dir):
        print("Deleting build folder %s..." % build_dir)
        rmtree(build_dir)
    print("Creating build folder %s..." % build_dir)
    os.mkdir(build_dir)
    os.chdir(build_dir)
    
    # Compile
    if sys.platform == "win32":
        cmake_generator = "NMake Makefiles"
        make_cmd = "nmake"
    else:
        cmake_generator = "Unix Makefiles"
        make_cmd = "make"
    
    print("Configuring " + module_name + " in " + os.getcwd() + "...")
    args = [
        "cmake",
        "-G", cmake_generator,
        "-DQT_QMAKE_EXECUTABLE=%s" % qtinfo.qmake_path,
        "-DBUILD_TESTS=False",
        "-DCMAKE_BUILD_TYPE=Release",
        "-DCMAKE_INSTALL_PREFIX=%s" % install_dir,
        ".."
    ]
    if sys.version_info[0] > 2:
        args.append("-DPYTHON3_EXECUTABLE=%s" % sys.executable)
        args.append("-DPYTHON3_INCLUDE_DIR=%s" % py_include_dir)
        args.append("-DPYTHON3_LIBRARY=%s" % py_library)
    else:
        args.append("-DPYTHON_EXECUTABLE=%s" % sys.executable)
        args.append("-DPYTHON_INCLUDE_DIR=%s" % py_include_dir)
        args.append("-DPYTHON_LIBRARY=%s" % py_library)
    if module_name.lower() == "generatorrunner":
        args.append("-DCMAKE_INSTALL_RPATH_USE_LINK_PATH=yes")
    if module_name.lower() == "shiboken" and sys.version_info[0] > 2:
        args.append("-DUSE_PYTHON3=ON")
    if run_process(*args) != 0:
        raise Exception("Error configuring " + module_name)
    
    print("Compiling " + module_name + "...")
    if run_process(make_cmd) != 0:
        raise Exception("Error compiling " + module_name)
    
    print("Testing " + module_name + "...")
    if run_process("ctest") != 0:
        print("Some " + module_name + " tests failed!")
    
    print("Installing " + module_name + "...")
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
        optparser.add_option("-b", "--build-module", dest="build_module",
                             default=None, help="Specify what module to build")
        optparser.add_option("-o", "--only-package", dest="only_package",
                             action="store_true", default=False, help="Create a distribution package only using existing binaries.")
        options, args = optparser.parse_args(sys.argv)
        
        py_version = "%s.%s" % (sys.version_info[0], sys.version_info[1])
        
        py_include_dir = distutils.sysconfig.get_config_var("INCLUDEPY")
        
        py_prefix = distutils.sysconfig.get_config_var("prefix")
        if sys.platform == "win32":
            py_library = os.path.join(py_prefix, "libs/python%s.lib" % py_version.replace(".", ""))
        else:
            py_library = os.path.join(py_prefix, "lib/libpython%s.so" % py_version)
        if not os.path.exists(py_library):
            print("Failed to locate the Python library %s" % py_library)
        
        if not options.pyside_version in modules:
            print("Invalid pyside version specified [%s]. Available options: [%s]" % \
                (options.pyside_version, ', '.join(modules.keys())))
            sys.exit(1)
        
        script_dir = os.getcwd()
        
        modules_dir = os.path.join(script_dir, "modules")
        
        qtinfo = QtInfo(options.qmake_path)
        if not qtinfo.qmake_path or not os.path.exists(qtinfo.qmake_path):
            print("Failed to find qmake. Please specify the path to qmake with --qmake parameter.")
            sys.exit(1)
        
        # Add path to this version of Qt to environment if it's not there.
        # Otherwise the "generatorrunner" will not find the Qt libraries
        paths = os.environ['PATH'].lower().split(os.pathsep)
        qt_dir = os.path.dirname(qtinfo.qmake_path)
        if not qt_dir.lower() in paths:
            print("Adding path \"%s\" to environment" % qt_dir)
            paths.append(qt_dir)
        os.environ['PATH'] = os.pathsep.join(paths)
        
        if not qtinfo.version:
            print("Failed to query the Qt version with qmake %s" % qtinfo.qmake_path)
            sys.exit(1)
        
        install_dir = os.path.join(script_dir, "install-py%s-qt%s") % (py_version, qtinfo.version)
        
        print("------------------------------------------")
        if options.build_module:
            print("Build module: %s" % options.build_module)
        print("Generate package version: %s" % options.package_version)
        if options.download:
            print("Download modules version: %s" % options.pyside_version)
        print("Python version: %s" % py_version)
        print("Python executable: %s" % sys.executable)
        print("Python includes: %s" % py_include_dir)
        print("Python library: %s" % py_library)
        print("Script directory: %s" % script_dir)
        print("Modules directory: %s" % modules_dir)
        print("Install directory: %s" % install_dir)
        print("qmake path: %s" % qtinfo.qmake_path)
        print("Qt version: %s" % qtinfo.version)
        print("Qt bins: %s" % qtinfo.bins_dir)
        print("Qt plugins: %s" % qtinfo.plugins_dir)
        print("------------------------------------------")
        
        check_env(options.download)
        if options.check_environ:
            return
        
        if not options.only_package:
            process_modules(options.build_module, options.download, modules[options.pyside_version], modules_dir, install_dir, qtinfo, py_include_dir, py_library)
        
        if options.build_module is None and options.package_version is not None:
            from package import make_package
            make_package(options.package_version, script_dir, modules_dir, install_dir, py_version, qtinfo)
    
    except Exception:
        print(traceback.print_exception(*sys.exc_info()))
        sys.exit(1)
    
    sys.exit(0)


if __name__ == "__main__":
    main()
