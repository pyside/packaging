from shutil import copytree
import os

def create_package(script_dir, pkgsrc_dir, build_dir, output_dir, py_version):
    print "Generating python distribution package..."
    
    os.chdir(script_dir)
    
    pkgsrc_dir = os.path.join(script_dir, "src")
    if os.path.exists(pkgsrc_dir):
        print "Deleting folder %s..." % pkgsrc_dir
        shutil.rmtree(pkgsrc_dir, False)
    os.mkdir(pkgsrc_dir)
    
    build_dir = os.path.join(script_dir, "build")
    if os.path.exists(build_dir):
        print "Deleting folder %s..." % build_dir
        shutil.rmtree(build_dir, False)
    
    # <output>/lib/site-packages/PySide/* -> src/PySide
    src = os.path.join(output_dir, "lib/site-packages/PySide")
    print "Copying PySide sources from %s" % (src)
    copytree(src, os.path.join(pkgsrc_dir, "PySide"))
    
    # <output>/lib/site-packages/pysideuic/* -> src/pysideuic
    src = os.path.join(output_dir, "lib/site-packages/pysideuic")
    print "Copying pysideuic sources from %s" % (src)
    copytree(src, os.path.join(pkgsrc_dir, "pysideuic"))
    
    # <output>/bin/pyside-uic -> src/PySide/scripts/uic.py
    src = os.path.join(output_dir, "bin/pyside-uic")
    dst = os.path.join(pkgsrc_dir, "PySide/scripts")
    os.mkdir(dst)
    f = open(os.path.join(dst, "__init__.py"), "wt")
    f.write("# Package")
    f.close()
    dst = os.path.join(dst, "uic.py")
    print "Copying pyside-uic script from %s to %s" % (src, dst)
    shutil.copy(src, dst)
    
    def cpbin(name):
        src = os.path.join(output_dir, "bin/%s" % name)
        print "Copying %s from %s" % (name, src)
        shutil.copy(src, os.path.join(pkgsrc_dir, "PySide/%s" % name))
    
    # <output>/bin/pyside-lupdate.exe -> src/PySide/pyside-lupdate.exe
    cpbin("pyside-lupdate.exe")
    
    # <output>/bin/pyside-rcc.exe -> src/PySide/pyside-rcc.exe
    cpbin("pyside-rcc.exe")
    
    # <output>/bin/pyside.dll -> src/PySide/pyside.dll
    cpbin("pyside-python%s.dll" % py_version)
    
    # <output>/bin/shiboken.dll -> src/PySide/shiboken.dll
    cpbin("shiboken-python%s.dll" % py_version)
    
    # <qt>/bin/* -> src/PySide
    src = qt_bins_dir
    dst = os.path.join(pkgsrc_dir, "PySide")
    print "Copying Qt binaries from %s" % (src)
    names = os.listdir(qt_bins_dir)
    for name in names:
        # Ignore debug dlls and QtDesigner*.dll files
        if name.endswith(".dll") and not name.endswith("d4.dll") and not name.startswith("QtDesigner"):
            srcname = os.path.join(src, name)
            dstname = os.path.join(dst, name)
            print "Copying \"%s\"" % (srcname)
            shutil.copy(srcname, dstname)
    
    # <qt>/plugins/* -> src/PySide/plugins
    src = qt_plugins_dir
    print "Copying Qt plugins from %s" % (src)
    copytree(src, os.path.join(pkgsrc_dir, "PySide/plugins"), ignore=ignore_patterns('*.lib', '*d4.dll'))
    
    # <modules>/examples/* -> src/PySide/examples
    src = os.path.join(modules_dir, "examples")
    if os.path.exists(src):
        print "Copying PySide examples from %s" % (src)
        copytree(src, os.path.join(pkgsrc_dir, "PySide/examples"))
    
    # Prepare setup.py
    print "Preparing setup.py..."
    version_str = "%sqt%s" % (PKG_VERSION, qt_version.replace(".", "")[0:3])
    replace_in_file("setup.py.in", "setup.py", { "${version}": version_str })
    
    # Build package
    print "Building distribution package..."
    if run_process(sys.executable, "setup.py", "bdist_wininst", "--target-version=%s" % py_version) != 0:
        raise Exception("Error building distribution package ")

