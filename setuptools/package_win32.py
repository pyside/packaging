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


def make_package(pkg_version, script_dir, sources_dir, build_dir, install_dir,
    py_version, pack_examples, debug, qtinfo, logger):
    
    logger.info("Generating python distribution package...")

    os.chdir(script_dir)

    templates_dir = os.path.join(script_dir, "templates")
    
    libs_dir = os.path.join(script_dir, "libs/%s" % platform.architecture()[0])

    dist_dir = os.path.join(script_dir, "packages")

    setup_dir = "%s-distribution" % install_dir
    if os.path.exists(setup_dir):
        logger.info("Deleting folder %s..." % setup_dir)
        rmtree(setup_dir)
    os.makedirs(setup_dir)

    version_str = "%sqt%s%s" % \
        (pkg_version, qtinfo.version.replace(".", "")[0:3], debug and "dbg" or "")
    
    # Prepare package sources
    logger.info("Preparing package sources...")
    for f in [
        "MANIFEST.in",
        "pyside_postinstall.py",
        "README.txt",
        "setup.py"]:
        replace_in_file(os.path.join(templates_dir, f), os.path.join(setup_dir, f), {
            "${version}": version_str,
        })
    
    # <install>/lib/site-packages/PySide/* -> src/PySide
    src = os.path.join(install_dir, "lib/site-packages/PySide")
    logger.info("Copying PySide libs from %s" % (src))
    copytree(src, os.path.join(setup_dir, "PySide"))
    '''
    if debug:
        # TODO:
        # <build>/pyside/PySide/*.pdb -> src/PySide
        src = os.path.join(build_dir, "pyside/PySide")
        logger.info("Copying PySide pdb from %s" % (src))
        copytree(src, os.path.join(setup_dir, "PySide"))
    '''

    # <install>/lib/site-packages/pysideuic/* -> src/pysideuic
    src = os.path.join(install_dir, "lib/site-packages/pysideuic")
    if os.path.exists(src):
        logger.info("Copying pysideuic sources from %s" % (src))
        copytree(src, os.path.join(setup_dir, "pysideuic"))
    else:
        logger.info("Skiping pysideuic.")

    # <install>/bin/pyside-uic -> src/PySide/scripts/uic.py
    src = os.path.join(install_dir, "bin/pyside-uic")
    dst = os.path.join(setup_dir, "PySide/scripts")
    os.makedirs(dst)
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
            shutil.copy(src, os.path.join(setup_dir, "PySide/%s" % file_name))
        else:
            logger.info("Skiping %s..." % src)

    # <install>/... -> src/PySide/
    cpbin("bin/pyside-lupdate.exe")
    cpbin("bin/pyside-rcc.exe")
    cpbin("bin/pyside.dll")
    cpbin("bin/pyside-python%s.dll" % py_version)
    cpbin("bin/shiboken.exe")
    cpbin("bin/shiboken.dll")
    cpbin("bin/shiboken-python%s.dll" % py_version)
    cpbin("lib/pyside.lib")
    cpbin("lib/pyside-python%s.lib" % py_version)
    cpbin("lib/shiboken.lib")
    cpbin("lib/shiboken-python%s.lib" % py_version)
    
    # <install>/share/PySide/typesystems/* -> src/PySide/typesystems
    src = os.path.join(install_dir, "share/PySide/typesystems")
    logger.info("Copying PySide typesystems from %s" % (src))
    copytree(src, os.path.join(setup_dir, "PySide/typesystems"))
    
    # <install>/include/* -> src/PySide/include
    src = os.path.join(install_dir, "include")
    logger.info("Copying C++ headers from %s" % (src))
    copytree(src, os.path.join(setup_dir, "PySide/include"))
    
    def cplib(name):
        src = os.path.join(libs_dir, "%s" % name)
        if os.path.exists(src):
            file_name = os.path.basename(name)
            logger.info("Copying %s from %s" % (file_name, src))
            shutil.copy(src, os.path.join(setup_dir, "PySide/%s" % file_name))
        else:
            logger.info("Skiping %s..." % src)

    # libs/* -> src/PySide/
    cplib("libeay32.dll")
    cplib("ssleay32.dll")
    
    # <qt>/bin/*.dll -> src/PySide
    def cp_qt_bin(name):
        src = os.path.join(qtinfo.bins_dir, name)
        logger.info("Copying %s from %s" % (name, src))
        shutil.copy(src, os.path.join(setup_dir, "PySide/%s" % name))
    src = qtinfo.bins_dir
    dst = os.path.join(setup_dir, "PySide")
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
    copytree(src, os.path.join(setup_dir, "PySide/plugins"), ignore=ignore_patterns('*.pdb', '*.exp', '*.ilk', '*.lib', '*d4.dll'))

    # <qt>/imports/* -> src/PySide/imports
    src = qtinfo.imports_dir
    logger.info("Copying QML imports from %s" % (src))
    copytree(src, os.path.join(setup_dir, "PySide/imports"), ignore=ignore_patterns('*.pdb', '*.exp', '*.ilk', '*.lib', '*d4.dll'))

    # <qt>/translations/* -> src/PySide/translations
    src = qtinfo.translations_dir
    logger.info("Copying Qt translations from %s" % (src))
    dst = os.path.join(setup_dir, "PySide/translations")
    if not os.path.exists(dst):
        os.makedirs(dst)
    for name in os.listdir(src):
        if name.endswith(".ts"):
            srcname = os.path.join(src, name)
            dstname = os.path.join(dst, name)
            logger.info("Copying \"%s\"" % (srcname))
            shutil.copy(srcname, dstname)

    if pack_examples:
        # <modules>/pyside-examples/examples/* -> src/PySide/examples
        src = os.path.join(sources_dir, "pyside-examples/examples")
        if os.path.exists(src):
            logger.info("Copying PySide examples from %s" % (src))
            copytree(src, os.path.join(setup_dir, "PySide/examples"))

    # Build package
    os.chdir(setup_dir)
    logger.info("Building distribution package...")
    if run_process([sys.executable,
        "setup.py",
        "bdist_wininst",
        "--target-version=%s" % py_version,
        "--dist-dir=%s" % dist_dir,
        ], logger) != 0:
        raise Exception("Error building distribution package ")
    
    # Clean-up
    os.chdir(script_dir)
    if os.path.exists(setup_dir):
        logger.info("Deleting folder %s..." % setup_dir)
        rmtree(setup_dir)
