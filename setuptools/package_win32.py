import os
import sys
import shutil
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

    setup_dir = os.path.join(script_dir, "setup")
    if os.path.exists(setup_dir):
        logger.info("Deleting folder %s..." % setup_dir)
        rmtree(setup_dir)
    os.makedirs(setup_dir)

    version_str = "%sqt%s%s" % \
        (pkg_version, qtinfo.version.replace(".", "")[0:3], debug and "dbg" or "")
    
    vars = {
        "sources_dir": sources_dir,
        "templates_dir": templates_dir,
        "install_dir": install_dir,
        "build_dir": build_dir,
        "setup_dir": setup_dir,
        "libs_dir": libs_dir,
        "qt_bin_dir": qtinfo.bins_dir,
        "qt_plugins_dir": qtinfo.plugins_dir,
        "qt_imports_dir": qtinfo.imports_dir,
        "qt_translations_dir": qtinfo.translations_dir,
        "version": version_str,
    }
    
    # Prepare package sources
    logger.info("Preparing package sources...")
    for f in os.listdir(templates_dir):
        copyfile("${templates_dir}/%s" % f, "${setup_dir}/%s" % f,
            logger=logger, force=True, vars=vars)
    
    # <install>/lib/site-packages/PySide/* -> <setup>/PySide
    copydir(
        "${install_dir}/lib/site-packages/PySide",
        "${setup_dir}/PySide",
        logger=logger, vars=vars)
    if debug:
        # <build>/pyside/PySide/*.pdb -> <setup>/PySide
        copydir(
            "${build_dir}/pyside/PySide",
            "${setup_dir}/PySide",
            filter=["*.pdb"],
            recursive=False, logger=logger, vars=vars)

    # <install>/lib/site-packages/pysideuic/* -> <setup>/pysideuic
    copydir(
        "${install_dir}/lib/site-packages/pysideuic",
        "${setup_dir}/pysideuic",
        force=False, logger=logger, vars=vars)

    # <install>/bin/pyside-uic -> PySide/scripts/uic.py
    makefile(
        "${setup_dir}/PySide/scripts/__init__.py",
        logger=logger, vars=vars)
    copyfile(
        "${install_dir}/bin/pyside-uic",
        "${setup_dir}/PySide/scripts/uic.py",
        force=False, logger=logger, vars=vars)

    # <install>/bin/*.exe,*.dll -> PySide/
    copydir(
        "${install_dir}/bin/",
        "${setup_dir}/PySide",
        filter=["*.exe", "*.dll"],
        recursive=False, logger=logger, vars=vars)

    # <install>/lib/*.lib -> PySide/
    copydir(
        "${install_dir}/lib/",
        "${setup_dir}/PySide",
        filter=["*.lib"],
        recursive=False, logger=logger, vars=vars)

    # <install>/share/PySide/typesystems/* -> <setup>/PySide/typesystems
    copydir(
        "${install_dir}/share/PySide/typesystems",
        "${setup_dir}/PySide/typesystems",
        logger=logger, vars=vars)

    # <install>/include/* -> <setup>/PySide/include
    copydir(
        "${install_dir}/include",
        "${setup_dir}/PySide/include",
        logger=logger, vars=vars)

    # libs/* -> <setup>/PySide/
    copyfile("${libs_dir}/libeay32.dll", "${setup_dir}/PySide/libeay32.dll",
        force=False, logger=logger, vars=vars)
    copyfile("${libs_dir}/ssleay32.dll", "${setup_dir}/PySide/ssleay32.dll",
        force=False, logger=logger, vars=vars)

    # <qt>/bin/*.dll -> <setup>/PySide
    copydir("${qt_bin_dir}", "${setup_dir}/PySide",
        filter=[
            "*.dll",
            "designer.exe",
            "linguist.exe",
            "lrelease.exe",
            "lupdate.exe",
            "lconvert.exe"],
        ignore=["*d4.dll"],
        recursive=False, logger=logger, vars=vars)
    if debug:
        # <qt>/bin/*d4.dll -> <setup>/PySide
        copydir("${qt_bin_dir}", "${setup_dir}/PySide",
            filter=["*d4.dll"],
            recursive=False, logger=logger, vars=vars)

    # <qt>/plugins/* -> <setup>/PySide/plugins
    copydir("${qt_plugins_dir}", "${setup_dir}/PySide/plugins",
        filter=["*.dll"],
        logger=logger, vars=vars)

    # <qt>/imports/* -> <setup>/PySide/imports
    copydir("${qt_imports_dir}", "${setup_dir}/PySide/imports",
        filter=["qmldir", "*.dll"],
        logger=logger, vars=vars)

    # <qt>/translations/* -> <setup>/PySide/translations
    copydir("${qt_translations_dir}", "${setup_dir}/PySide/translations",
        filter=["*.ts"],
        logger=logger, vars=vars)

    if pack_examples:
        # <sources>/pyside-examples/examples/* -> <setup>/PySide/examples
        copydir(
            "${sources_dir}/pyside-examples/examples",
            "${setup_dir}/PySide/examples",
            logger=logger, vars=vars)

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
