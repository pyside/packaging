import os
import sys
import subprocess
import shutil
import datetime

from qtinfo import QtInfo

try:
    from shutil import ignore_patterns, copytree
    # Running Python > 2.5
except ImportError:
    # Running Python <= 2.5
    # Imported from Python 2.7 module shutil
    import fnmatch
    def ignore_patterns(*patterns):
        def _ignore_patterns(path, names):
            ignored_names = []
            for pattern in patterns:
                ignored_names.extend(fnmatch.filter(names, pattern))
            return set(ignored_names)
        return _ignore_patterns
    def copytree(src, dst, symlinks=False, ignore=None):
        names = os.listdir(src)
        if ignore is not None:
            ignored_names = ignore(src, names)
        else:
            ignored_names = set()

        os.makedirs(dst)
        errors = []
        for name in names:
            if name in ignored_names:
                continue
            srcname = os.path.join(src, name)
            dstname = os.path.join(dst, name)
            try:
                if symlinks and os.path.islink(srcname):
                    linkto = os.readlink(srcname)
                    os.symlink(linkto, dstname)
                elif os.path.isdir(srcname):
                    copytree(srcname, dstname, symlinks, ignore)
                else:
                    # Will raise a SpecialFileError for unsupported file types
                    shutil.copy2(srcname, dstname)
            # catch the Error from the recursive copytree so that we can
            # continue with other files
            except shutil.Error, err:
                errors.extend(err.args[0])
            except EnvironmentError, why:
                errors.append((srcname, dstname, str(why)))
        try:
            shutil.copystat(src, dst)
        except OSError, why:
            if WindowsError is not None and isinstance(why, WindowsError):
                # Copying file access times may fail on Windows
                pass
            else:
                errors.extend((src, dst, str(why)))
        if errors:
            raise Error, errors

def replace_in_file(src, dst, vars):
    f = open(src, "rt")
    content =  f.read()
    f.close()
    for k in vars:
        content = content.replace(k, vars[k])
    f = open(dst, "wt")
    f.write(content)
    f.close()

def run_process(*args):
    shell = False
    if sys.platform == "win32":
        shell = True
    p = subprocess.Popen(args, shell=shell)
    p.communicate()
    return p.returncode

def create_package(pkg_version, script_dir, output_dir, py_version, qtinfo, cleanup):
    print "Generating python distribution package..."

    os.chdir(script_dir)
    modules_dir = os.path.join(script_dir, "modules")

    pkgsrc_dir = os.path.join(script_dir, "src")
    if os.path.exists(pkgsrc_dir):
        print "Deleting folder %s..." % pkgsrc_dir
        shutil.rmtree(pkgsrc_dir, False)
    os.mkdir(pkgsrc_dir)

    dist_dir = os.path.join(script_dir, "dist")
    if os.path.exists(dist_dir):
        print "Deleting old packages in %s..." % dist_dir
        shutil.rmtree(dist_dir)

    build_dir = os.path.join(script_dir, "build")
    if cleanup and os.path.exists(build_dir):
        print "Deleting folder %s..." % build_dir
        shutil.rmtree(build_dir, False)

    # <output>/lib/site-packages/PySide/* -> src/PySide
    src = os.path.join(output_dir, "lib/site-packages/PySide")
    print "Copying PySide sources from %s" % (src)
    copytree(src, os.path.join(pkgsrc_dir, "PySide"))

    # <output>/lib/site-packages/pysideuic/* -> src/pysideuic
    src = os.path.join(output_dir, "lib/site-packages/pysideuic")
    if os.path.exists(src):
        print "Copying pysideuic sources from %s" % (src)
        copytree(src, os.path.join(pkgsrc_dir, "pysideuic"))
    else:
        print "Skiping pysideuic."

    # <output>/bin/pyside-uic -> src/PySide/scripts/uic.py
    src = os.path.join(output_dir, "bin/pyside-uic")
    dst = os.path.join(pkgsrc_dir, "PySide/scripts")
    os.mkdir(dst)
    f = open(os.path.join(dst, "__init__.py"), "wt")
    f.write("# Package")
    f.close()
    dst = os.path.join(dst, "uic.py")
    if os.path.exists(src):
        print "Copying pyside-uic script from %s to %s" % (src, dst)
        shutil.copy(src, dst)
    else:
        print "Skip uic file"

    def cpbin(name):
        src = os.path.join(output_dir, "bin/%s" % name)
        if os.path.exists(src):
            print "Copying %s from %s" % (name, src)
            shutil.copy(src, os.path.join(pkgsrc_dir, "PySide/%s" % name))
        else:
            print "Skiping %s..." % src

    # <output>/bin/pyside-lupdate.exe -> src/PySide/pyside-lupdate.exe
    cpbin("pyside-lupdate.exe")

    # <output>/bin/pyside-rcc.exe -> src/PySide/pyside-rcc.exe
    cpbin("pyside-rcc.exe")

    # <output>/bin/pyside.dll -> src/PySide/pyside.dll
    cpbin("pyside-python%s.dll" % py_version)

    # <output>/bin/shiboken.dll -> src/PySide/shiboken.dll
    cpbin("shiboken-python%s.dll" % py_version)

    # <qt>/bin/* -> src/PySide
    src = qtinfo.bins_dir
    dst = os.path.join(pkgsrc_dir, "PySide")
    print "Copying Qt binaries from %s" % (src)
    names = os.listdir(qtinfo.bins_dir)
    for name in names:
        # Ignore debug dlls and QtDesigner*.dll files
        if name.endswith(".dll") and not name.endswith("d4.dll") and not name.startswith("QtDesigner"):
            srcname = os.path.join(src, name)
            dstname = os.path.join(dst, name)
            print "Copying \"%s\"" % (srcname)
            shutil.copy(srcname, dstname)

    # <qt>/plugins/* -> src/PySide/plugins
    src = qtinfo.plugins_dir
    print "Copying Qt plugins from %s" % (src)
    copytree(src, os.path.join(pkgsrc_dir, "PySide/plugins"), ignore=ignore_patterns('*.lib', '*d4.dll'))

    # <qt>/imports/* -> src/PySide/imports
    src = qtinfo.imports_dir
    print "Copying QML imports from %s" % (src)
    copytree(src, os.path.join(pkgsrc_dir, "PySide/imports"), ignore=ignore_patterns('*.lib', '*d4.dll'))

    # <modules>/examples/* -> src/PySide/examples
    src = os.path.join(modules_dir, "examples")
    if os.path.exists(src):
        print "Copying PySide examples from %s" % (src)
        copytree(src, os.path.join(pkgsrc_dir, "PySide/examples"))

    # Prepare setup.py
    print "Preparing setup.py..."
    version_str = "%sqt%s" % (pkg_version, qtinfo.version.replace(".", "")[0:3])
    replace_in_file("setup.py.in", "setup.py", { "${version}": version_str })

    # Build package
    print "Building distribution package..."
    if run_process(sys.executable, "setup.py", "bdist_wininst", "--target-version=%s" % py_version) != 0:
        raise Exception("Error building distribution package ")

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print "Usage: package.py <package_version> <build_dir> <install_dir>"
        sys.exit(2)

    qinfo = QtInfo()
    py_version = "%s.%s" % (sys.version_info[0], sys.version_info[1])
    create_package("%s.%s" % (sys.argv[1], datetime.date.today().strftime('%Y%m%d')),
                   sys.argv[2],
                   sys.argv[3],
                   py_version,
                   qinfo,
                   False)
