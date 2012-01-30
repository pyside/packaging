import os
import sys
import subprocess
import shutil
import datetime
import traceback

from utils import *
from qtinfo import QtInfo


def make_package(pkg_version, script_dir, modules_dir, install_dir, py_version, qtinfo, logger):
    logger.info("Generating python distribution package...")

    os.chdir(script_dir)

    pkgsrc_dir = os.path.join(script_dir, "src")
    if os.path.exists(pkgsrc_dir):
        logger.info("Deleting folder %s..." % pkgsrc_dir)
        rmtree(pkgsrc_dir)
    os.mkdir(pkgsrc_dir)

    dist_dir = os.path.join(script_dir, "dist")
    if os.path.exists(dist_dir):
        logger.info("Deleting old packages in %s..." % dist_dir)
        rmtree(dist_dir)

    build_dir = os.path.join(script_dir, "build")
    if os.path.exists(build_dir):
        logger.info("Deleting folder %s..." % build_dir)
        rmtree(build_dir)

    # <install>/lib/site-packages/PySide/* -> src/PySide
    src = os.path.join(install_dir, "lib/site-packages/PySide")
    logger.info("Copying PySide sources from %s" % (src))
    copytree(src, os.path.join(pkgsrc_dir, "PySide"))

    # <install>/lib/site-packages/pysideuic/* -> src/pysideuic
    src = os.path.join(install_dir, "lib/site-packages/pysideuic")
    if os.path.exists(src):
        logger.info("Copying pysideuic sources from %s" % (src))
        copytree(src, os.path.join(pkgsrc_dir, "pysideuic"))
    else:
        logger.info("Skiping pysideuic.")

    # <install>/bin/pyside-uic -> src/PySide/scripts/uic.py
    src = os.path.join(install_dir, "bin/pyside-uic")
    dst = os.path.join(pkgsrc_dir, "PySide/scripts")
    os.mkdir(dst)
    f = open(os.path.join(dst, "__init__.py"), "wt")
    f.write("# Package")
    f.close()
    dst = os.path.join(dst, "uic.py")
    if os.path.exists(src):
        logger.info("Copying pyside-uic script from %s to %s" % (src, dst))
        shutil.copy(src, dst)
    else:
        logger.info("Skip uic file")

    def cpbin(name):
        src = os.path.join(install_dir, "%s" % name)
        if os.path.exists(src):
            file_name = os.path.basename(name)
            logger.info("Copying %s from %s" % (file_name, src))
            shutil.copy(src, os.path.join(pkgsrc_dir, "PySide/%s" % file_name))
        else:
            logger.info("Skiping %s..." % src)

    # <install>/... -> src/PySide/
    cpbin("bin/apiextractor.dll")
    cpbin("bin/generatorrunner.exe")
    cpbin("bin/genrunner.dll")
    cpbin("bin/pyside-lupdate.exe")
    cpbin("bin/pyside-rcc.exe")
    cpbin("bin/pyside.dll")
    cpbin("bin/pyside-python%s.dll" % py_version)
    cpbin("bin/shiboken.exe")
    cpbin("bin/shiboken.dll")
    cpbin("bin/shiboken-python%s.dll" % py_version)
    cpbin("lib/generatorrunner/shiboken_generator.dll")

    # <qt>/bin/*.dll -> src/PySide
    def cp_qt_bin(name):
        src = os.path.join(qtinfo.bins_dir, name)
        logger.info("Copying %s from %s" % (name, src))
        shutil.copy(src, os.path.join(pkgsrc_dir, "PySide/%s" % name))
    src = qtinfo.bins_dir
    dst = os.path.join(pkgsrc_dir, "PySide")
    logger.info("Copying Qt binaries from %s" % (src))
    for name in os.listdir(src):
        # Ignore debug dlls
        if name.endswith(".dll") and not name.endswith("d4.dll"):
            srcname = os.path.join(src, name)
            dstname = os.path.join(dst, name)
            logger.info("Copying \"%s\"" % (srcname))
            shutil.copy(srcname, dstname)
    cp_qt_bin("designer.exe")
    cp_qt_bin("linguist.exe")
    cp_qt_bin("lrelease.exe")
    cp_qt_bin("lupdate.exe")
    cp_qt_bin("lconvert.exe")
    
    # <qt>/plugins/* -> src/PySide/plugins
    src = qtinfo.plugins_dir
    logger.info("Copying Qt plugins from %s" % (src))
    copytree(src, os.path.join(pkgsrc_dir, "PySide/plugins"), ignore=ignore_patterns('*.pdb', '*.exp', '*.ilk', '*.lib', '*d4.dll'))

    # <qt>/imports/* -> src/PySide/imports
    src = qtinfo.imports_dir
    logger.info("Copying QML imports from %s" % (src))
    copytree(src, os.path.join(pkgsrc_dir, "PySide/imports"), ignore=ignore_patterns('*.pdb', '*.exp', '*.ilk', '*.lib', '*d4.dll'))

    # <qt>/translations/* -> src/PySide/translations
    src = qtinfo.translations_dir
    logger.info("Copying Qt translations from %s" % (src))
    dst = os.path.join(pkgsrc_dir, "PySide/translations")
    if not os.path.exists(dst):
        os.mkdir(dst)
    for name in os.listdir(src):
        if name.endswith(".ts"):
            srcname = os.path.join(src, name)
            dstname = os.path.join(dst, name)
            logger.info("Copying \"%s\"" % (srcname))
            shutil.copy(srcname, dstname)

    # <modules>/examples/* -> src/PySide/examples
    src = os.path.join(modules_dir, "examples")
    if os.path.exists(src):
        logger.info("Copying PySide examples from %s" % (src))
        copytree(src, os.path.join(pkgsrc_dir, "PySide/examples"))

    # Prepare setup.py
    logger.info("Preparing setup.py...")
    version_str = "%sqt%s" % (pkg_version, qtinfo.version.replace(".", "")[0:3])
    replace_in_file("setup.py.in", "setup.py", { "${version}": version_str })

    # Build package
    logger.info("Building distribution package...")
    if run_process([sys.executable, "setup.py", "bdist_wininst", "--target-version=%s" % py_version], logger) != 0:
        raise Exception("Error building distribution package ")


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
        if len(sys.argv) < 4 or len(sys.argv) > 5:
            logger.error("Usage: package.py <package_version> <build_dir> <install_dir> [<qmake_path>]")
            sys.exit(2)

        py_version = "%s.%s" % (sys.version_info[0], sys.version_info[1])
        pkg_version = "%s.%s" % (sys.argv[1], datetime.date.today().strftime('%Y%m%d'))
        script_dir = sys.argv[2]
        modules_dir = os.path.join(script_dir, "modules")
        install_dir = sys.argv[3]
        if len(sys.argv) >= 5:
            qinfo = QtInfo(sys.argv[4])
        else:
            qinfo = QtInfo()

        make_package(pkg_version,
                     script_dir,
                     modules_dir,
                     install_dir,
                     py_version,
                     qinfo,
                     logger)
        
    except Exception:
        logger.error(''.join(traceback.format_exception(*sys.exc_info())))
        sys.exit(1)
    
    sys.exit(0)
