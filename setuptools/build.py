import sys
import os
import stat
import errno
import shutil
import subprocess
import optparse
import traceback
import distutils.sysconfig
import logging
import platform

from utils import *
from qtinfo import QtInfo
from package import make_package


logger = logging.getLogger('setuptools')

VERSION = '1.1.1'

# Modules
giturl = "https://git.gitorious.org/pyside"
modules = {
    'master': [
        ["shiboken", "master", giturl + "/shiboken.git", True],
        ["pyside", "master", giturl + "/pyside.git", True],
        ["pyside-tools", "master", giturl + "/pyside-tools.git", True],
    ],
    '1.1.1': [
        ["shiboken", "1.1.1", giturl + "/shiboken.git", True],
        ["pyside", "1.1.1", giturl + "/pyside.git", True],
        ["pyside-tools", "0.2.14", giturl + "/pyside-tools.git", True],
    ],
}
examples_module = ["pyside-examples", "master", giturl + "/pyside-examples.git", False]

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
        logger.info("Checking " + prg + "...")
        f = find_executable(prg)
        if not f:
            logger.error("You need the program \"" + prg + "\" on your system path to compile PySide.")
            sys.exit(1)
        else:
            logger.info('Found %s' % f)


def process_modules(build_module, download, modules, script_dir, sources_dir, build_dir, install_dir,
    qtinfo, py_executable, py_include_dir, py_library, build_type):
    
    for module in modules:
        if build_module is None or build_module.lower() == module[0].lower():
            process_module(download, module, script_dir, sources_dir, build_dir, install_dir,
                qtinfo, py_executable, py_include_dir, py_library, build_type)


def download_module(sources_dir, module_name, repo, branch):
    module_src_dir = os.path.join(sources_dir, module_name)
    
    if os.path.exists(module_src_dir):
        logger.info("Deleting module source folder %s..." % module_src_dir)
        rmtree(module_src_dir)
    
    # Clone sources from git repository
    os.chdir(sources_dir)
    logger.info("Cloning repository " + repo)
    if run_process(["git", "clone", repo], logger) != 0:
        raise Exception("Error cloning " + repo)
    
    # Checkout branch
    os.chdir(module_src_dir)
    logger.info("Changing to branch " + branch + " in " + module_name)
    if run_process(["git", "checkout", branch], logger) != 0:
        raise Exception("Error changing to branch " + branch + " in " + module_name)


def process_module(download, module, script_dir, sources_dir, build_dir, install_dir, qtinfo,
    py_executable, py_include_dir, py_library, build_type):
    
    module_name = module[0]
    repo = module[2]
    branch = module[1]
    
    logger.info("Processing module %s..." % module_name)
    
    if download:
        download_module(sources_dir, module_name, repo, branch)
    
    build_module = module[3]
    if not build_module:
        return
    
    os.chdir(build_dir)
    module_build_dir = os.path.join(build_dir,  module_name)
    if os.path.exists(module_build_dir):
        logger.info("Deleting module build folder %s..." % module_build_dir)
        rmtree(module_build_dir)
    logger.info("Creating module build folder %s..." % module_build_dir)
    os.mkdir(module_build_dir)
    os.chdir(module_build_dir)
    
    module_src_dir = os.path.join(sources_dir, module_name)
    
    if sys.platform == "win32":
        cmake_generator = "NMake Makefiles"
        make_cmd = "nmake"
    else:
        cmake_generator = "Unix Makefiles"
        make_cmd = "make"
    cmake_cmd = [
        "cmake",
        "-G", cmake_generator,
        "-DQT_QMAKE_EXECUTABLE=%s" % qtinfo.qmake_path,
        "-DBUILD_TESTS=False",
        "-DDISABLE_DOCSTRINGS=True",
        "-DCMAKE_BUILD_TYPE=%s" % build_type,
        "-DCMAKE_INSTALL_PREFIX=%s" % install_dir,
        module_src_dir
    ]
    if sys.version_info[0] > 2:
        cmake_cmd.append("-DPYTHON3_EXECUTABLE=%s" % py_executable)
        cmake_cmd.append("-DPYTHON3_INCLUDE_DIR=%s" % py_include_dir)
        cmake_cmd.append("-DPYTHON3_LIBRARY=%s" % py_library)
        if build_type.lower() == 'debug':
            cmake_cmd.append("-DPYTHON3_DBG_EXECUTABLE=%s" % py_executable)
            cmake_cmd.append("-DPYTHON3_DEBUG_LIBRARY=%s" % py_library)
    else:
        cmake_cmd.append("-DPYTHON_EXECUTABLE=%s" % py_executable)
        cmake_cmd.append("-DPYTHON_INCLUDE_DIR=%s" % py_include_dir)
        cmake_cmd.append("-DPYTHON_LIBRARIES=%s" % py_library)
        if build_type.lower() == 'debug':
            cmake_cmd.append("-DPYTHON_DEBUG_LIBRARY=%s" % py_library)
    if module_name.lower() == "shiboken":
        cmake_cmd.append("-DCMAKE_INSTALL_RPATH_USE_LINK_PATH=yes")
        if sys.version_info[0] > 2:
            cmake_cmd.append("-DUSE_PYTHON3=ON")
    
    logger.info("Configuring module %s (%s)..." % (module_name,  module_src_dir))
    if run_process(cmake_cmd, logger) != 0:
        raise Exception("Error configuring " + module_name)
    
    logger.info("Compiling module %s..." % module_name)
    if run_process(make_cmd, logger) != 0:
        raise Exception("Error compiling " + module_name)
    
    logger.info("Testing module %s..." % module_name)
    if run_process("ctest", logger) != 0:
        logger.error("Some " + module_name + " tests failed!")
    
    logger.info("Installing module %s..." % module_name)
    if run_process([make_cmd, "install/fast"], logger) != 0:
        raise Exception("Error pseudo installing " + module_name)


def main():
    # Setup logger
    logger.setLevel(logging.DEBUG)
    # Create console handler and set level to debug
    chandler = logging.StreamHandler()
    chandler.setLevel(logging.DEBUG)
    # Create file handler and set level to debug
    fhandler = logging.FileHandler('build.log')
    fhandler.setLevel(logging.DEBUG)
    # Create formatter
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    # Add formatter to handlers
    chandler.setFormatter(formatter)
    fhandler.setFormatter(formatter)
    # Add handlers to logger
    logger.addHandler(chandler)
    logger.addHandler(fhandler)
    
    try:
        optparser = optparse.OptionParser(usage="build [options]", version="PySide package builder")
        optparser.add_option("-e", "--check-environ", dest="check_environ",                         
                             action="store_true", default=False, help="Check the environment.")
        optparser.add_option("-q", "--qmake", dest="qmake_path",                         
                             default=None, help="Locate qmake")
        optparser.add_option("-d", "--download", dest="download",
                             action="store_true", default=False, help="Download sources from git repository.")
        optparser.add_option("-m", "--modules-version", dest="modules_version",
                             default=VERSION, help="Specify what version of modules to checkout from git repository: 'master' or '" + VERSION + "'. Default is '" + VERSION + "'.")
        optparser.add_option("-p", "--package-version", dest="package_version",
                             default=VERSION, help="Specify package version. Default is %s" % VERSION)
        optparser.add_option("-u", "--debug", dest="debug",
                             action="store_true", default=False, help="Build the debug version of pyside binaries.")
        optparser.add_option("-b", "--build-module", dest="build_module",
                             default=None, help="Specify what module to build")
        optparser.add_option("-o", "--only-package", dest="only_package",
                             action="store_true", default=False, help="Create a distribution package only using existing binaries.")
        optparser.add_option("-x", "--pack-exmaples", dest="pack_examples",
                             action="store_true", default=True, help="Add pyside examples to package.")
        options, args = optparser.parse_args(sys.argv)
        
        build_type = "Release"
        if options.debug:
            build_type = "Debug"
        
        py_version = "%s.%s" % (sys.version_info[0], sys.version_info[1])
        py_include_dir = distutils.sysconfig.get_config_var("INCLUDEPY")
        py_prefix = distutils.sysconfig.get_config_var("prefix")
        py_executable = sys.executable
        
        dbgPostfix = ""
        if build_type == "Debug":
            dbgPostfix = "_d"
            py_executable = py_executable[:-4] + "_d.exe"
        
        if sys.platform == "win32":
            py_library = os.path.join(py_prefix, "libs/python%s%s.lib" % \
                (py_version.replace(".", ""), dbgPostfix))
        else:
            py_library = os.path.join(py_prefix, "lib/libpython%s.so" % \
                (py_version, dbgPostfix))
        
        if not os.path.exists(py_library):
            logger.error("Failed to locate the Python library %s" % py_library)
            sys.exit(1)
        
        if not options.modules_version in modules:
            logger.error("Invalid modules version specified [%s]. Available options: [%s]" % \
                (options.modules_version, ', '.join(modules.keys())))
            sys.exit(1)
        
        qtinfo = QtInfo(options.qmake_path)
        if not qtinfo.qmake_path or not os.path.exists(qtinfo.qmake_path):
            logger.error("Failed to find qmake. Please specify the path to qmake with --qmake parameter.")
            sys.exit(1)
        
        # Update os.path
        paths = os.environ['PATH'].lower().split(os.pathsep)
        def updatepath(path):
            if not path.lower() in paths:
                logger.info("Adding path \"%s\" to environment" % path)
                paths.append(path)
        qt_dir = os.path.dirname(qtinfo.qmake_path)
        updatepath(qt_dir)
        os.environ['PATH'] = os.pathsep.join(paths)
        
        qt_version = qtinfo.version
        
        if not qt_version:
            logger.error("Failed to query the Qt version with qmake %s" % qtinfo.qmake_path)
            sys.exit(1)
        
        build_name = "py%s-qt%s-%s-%s" % \
            (py_version, qt_version, platform.architecture()[0], build_type.lower())
        
        script_dir = os.getcwd()
        sources_dir = os.path.join(script_dir, "sources")
        build_dir = os.path.join(script_dir, os.path.join("build", "%s" % build_name))
        install_dir = os.path.join(script_dir, os.path.join("install", "%s" % build_name))
        
        logger.info("------------------------------------------")
        logger.info("Build type: %s" % build_type)
        if options.build_module:
            logger.info("Build module: %s" % options.build_module)
        if options.download:
            logger.info("Download modules version: %s" % options.modules_version)
        logger.info("Package version: %s" % options.package_version)
        logger.info("Python prefix: %s" % py_prefix)
        logger.info("Python version: %s" % py_version)
        logger.info("Python executable: %s" % py_executable)
        logger.info("Python includes: %s" % py_include_dir)
        logger.info("Python library: %s" % py_library)
        logger.info("Script directory: %s" % script_dir)
        logger.info("Sources directory: %s" % sources_dir)
        logger.info("Build directory: %s" % build_dir)
        logger.info("Install directory: %s" % install_dir)
        logger.info("Qt qmake: %s" % qtinfo.qmake_path)
        logger.info("Qt version: %s" % qt_version)
        logger.info("Qt bins: %s" % qtinfo.bins_dir)
        logger.info("Qt plugins: %s" % qtinfo.plugins_dir)
        logger.info("------------------------------------------")
        
        check_env(options.download)
        if options.check_environ:
            return
        
        # Prepare folders
        if not os.path.exists(sources_dir):
            logger.info("Creating sources folder %s..." % sources_dir)
            os.makedirs(sources_dir)
        if not os.path.exists(build_dir):
            logger.info("Creating build folder %s..." % build_dir)
            os.makedirs(build_dir)
        if not os.path.exists(install_dir):
            logger.info("Creating install folder %s..." % install_dir)
            os.makedirs(install_dir)
        
        if options.pack_examples:
            for k in modules:
                modules[k].append(examples_module)
        
        if not options.only_package:
            process_modules(options.build_module, options.download, modules[options.modules_version],
                script_dir, sources_dir, build_dir, install_dir, qtinfo, py_executable, py_include_dir, py_library, build_type)
        
        if options.build_module is None and options.package_version is not None:
            make_package(options.package_version, script_dir, sources_dir, build_dir, install_dir, py_version,
                options.pack_examples, options.debug, qtinfo, logger)
    
    except Exception:
        logger.error(''.join(traceback.format_exception(*sys.exc_info())))
        sys.exit(1)
    
    sys.exit(0)


if __name__ == "__main__":
    main()
