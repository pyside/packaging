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


if sys.platform == "win32":
    from package_win32 import make_package
elif sys.platform == "linux":
    from package_linux import make_package
else:
    def make_package(pkg_version, script_dir, modules_dir, install_dir, py_version,
        pack_examples, qtinfo, logger):
        raise NotImplementedError()


if __name__ == "__main__":
    import logging
    # Setup logger
    logger = logging.getLogger('package')
    logger.setLevel(logging.DEBUG)
    # Create console handler and set level to debug
    chandler = logging.StreamHandler()
    chandler.setLevel(logging.DEBUG)
    # Create file handler and set level to debug
    fhandler = logging.FileHandler('package.log')
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
        optparser = optparse.OptionParser(usage="package [options]", version="PySide package creator")
        optparser.add_option("-p", "--package-version", dest="package_version",
                             default=None, help="Specify package version")
        optparser.add_option("-s", "--script-dir", dest="script_dir",
                             default=None, help="Specify script build directory")
        optparser.add_option("-i", "--install-dir", dest="install_dir",
                             default=None, help="Specify install directory")
        optparser.add_option("-q", "--qmake", dest="qmake_path",
                             default=None, help="Locate qmake")
        optparser.add_option("-u", "--debug", dest="debug",
                             action="store_true", default=False, help="Create the debug version of the package.")
        optparser.add_option("-x", "--pack-exmaples", dest="pack_examples",
                             action="store_true", default=False, help="Add pyside examples to package.")
        options, args = optparser.parse_args(sys.argv)
        
        if not options.package_version:
            logger.error("Please specify the package version with --package-version parameter")
            sys.exit(1)
        if not os.path.exists(options.script_dir):
            logger.error("Please specify the script build directory with --script-dir parameter")
            sys.exit(1)
        if not os.path.exists(options.install_dir):
            logger.error("Please specify the install directory with --install-dir parameter")
            sys.exit(1)
        
        build_type = "Release"
        if options.debug:
            build_type = "Debug"
        
        py_version = "%s.%s" % (sys.version_info[0], sys.version_info[1])
        pkg_version = "%s.%s" % (options.package_version, datetime.date.today().strftime('%Y%m%d'))
        script_dir = options.script_dir
        install_dir = options.install_dir
        modules_dir = os.path.join(script_dir, "modules")
        
        qtinfo = QtInfo(options.qmake_path)
        if not qtinfo.qmake_path or not os.path.exists(qtinfo.qmake_path):
            logger.error("Failed to find qmake. Please specify the path to qmake with --qmake parameter.")
            sys.exit(1)
        
        make_package(pkg_version,
                     script_dir,
                     modules_dir,
                     install_dir,
                     py_version,
                     options.pack_examples,
                     qtinfo,
                     logger)
        
    except Exception:
        logger.error(''.join(traceback.format_exception(*sys.exc_info())))
        sys.exit(1)
    
    sys.exit(0)
