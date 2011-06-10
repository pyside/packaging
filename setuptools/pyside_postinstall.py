# Postinstall script for PySide
#
# Generates the qt.conf file
#
# This file is based on pywin32_postinstall.py file from pywin32 project

import os, sys


try:
    # When this script is run from inside the bdist_wininst installer,
    # file_created() and directory_created() are additional builtin
    # functions which write lines to Python23\pyside-install.log. This is
    # a list of actions for the uninstaller, the format is inspired by what
    # the Wise installer also creates.
    file_created
    is_bdist_wininst = True
except NameError:
    is_bdist_wininst = False # we know what it is not - but not what it is :)
    def file_created(file):
        pass


def install():
    try:
        from PySide import QtCore
        if is_bdist_wininst:
            # Run from inside the bdist_wininst installer
            import distutils.sysconfig
            exec_prefix = distutils.sysconfig.get_config_var("exec_prefix")
        else:
            # Run manually
            exec_prefix = os.path.dirname(sys.executable)
        qtconf_path = os.path.join(exec_prefix, "qt.conf")
        print "Generating file %s..." % qtconf_path
        f = open(qtconf_path, 'wt')
        file_created(qtconf_path)
        pyside_path = os.path.dirname(QtCore.__file__)
        pyside_path = pyside_path.replace("\\", "/")
        pyside_path = pyside_path.replace("lib/site-packages", "Lib/site-packages")
        print "PySide installed in %s..." % pyside_path
        f.write("""[Paths]
Prefix = %s
Binaries = .
Plugins = plugins
Translations = translations
            """ % (pyside_path))
        print "The PySide extensions were successfully installed."
    except ImportError:
        print "The PySide extensions were not installed!"


def uninstall():
    print "The PySide extensions were successfully uninstalled."


def usage():
    msg = \
"""%s: A post-install script for the PySide extensions.
    
This should be run automatically after installation, but if it fails you
can run it again with a '-install' parameter, to ensure the environment
is setup correctly.
"""
    print msg.strip() % os.path.basename(sys.argv[0])


# NOTE: If this script is run from inside the bdist_wininst created
# binary installer or uninstaller, the command line args are either
# '-install' or '-remove'.

# Important: From inside the binary installer this script MUST NOT
# call sys.exit() or raise SystemExit, otherwise not only this script
# but also the installer will terminate! (Is there a way to prevent
# this from the bdist_wininst C code?)

if __name__ == '__main__':
    if len(sys.argv)==1:
        usage()
        sys.exit(1)

    arg_index = 1
    while arg_index < len(sys.argv):
        arg = sys.argv[arg_index]
        if arg == "-install":
            install()
        elif arg == "-remove":
            # bdist_msi calls us before uninstall, so we can undo what we
            # previously did.  Sadly, bdist_wininst calls us *after*, so
            # we can't do much at all.
            if not is_bdist_wininst:
                uninstall()
        else:
            print "Unknown option:", arg
            usage()
            sys.exit(0)
        arg_index += 1
