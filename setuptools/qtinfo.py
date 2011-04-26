import subprocess
import os
import sys

# LINKS:
#   http://snippets.dzone.com/posts/show/6313
def find_executable(executable, path=None):
    """Try to find 'executable' in the directories listed in 'path' (a
    string listing directories separated by 'os.pathsep'; defaults to
    os.environ['PATH']).  Returns the complete filename or None if not
    found
    """
    if path is None:
        path = os.environ['PATH']
    paths = path.split(os.pathsep)
    extlist = ['']
    if os.name == 'os2':
        (base, ext) = os.path.splitext(executable)
        # executable files on OS/2 can have an arbitrary extension, but
        # .exe is automatically appended if no dot is present in the name
        if not ext:
            executable = executable + ".exe"
    elif sys.platform == 'win32':
        pathext = os.environ['PATHEXT'].lower().split(os.pathsep)
        (base, ext) = os.path.splitext(executable)
        if ext.lower() not in pathext:
            extlist = pathext
    for ext in extlist:
        execname = executable + ext
        if os.path.isfile(execname):
            return execname
        else:
            for p in paths:
                f = os.path.join(p, execname)
                if os.path.isfile(f):
                    return f
    else:
        return None


class QtInfo(object):
    def __init__(self, qmake_path=None):
        if qmake_path:
            self._qmake_path = qmake_path
        else:
            self._qmake_path = find_executable("qmake")

    def getQMakePath(self):
        return self._qmake_path

    def getVersion(self):
        return self.getProperty("QT_VERSION")

    def getBinsPath(self):
        return self.getProperty("QT_INSTALL_BINS")

    def getPluginsPath(self):
        return self.getProperty("QT_INSTALL_PLUGINS")

    def getImportsPath(self):
        return self.getProperty("QT_INSTALL_IMPORTS")

    def getProperty(self, prop_name):
        p = subprocess.Popen([self._qmake_path, "-query", prop_name], shell=False, stdout=subprocess.PIPE)
        prop = p.communicate()[0]
        if p.returncode != 0:
            return None
        return prop.strip()

    version = property(getVersion)
    bins_dir = property(getBinsPath)
    plugins_dir = property(getPluginsPath)
    qmake_path = property(getQMakePath)
    imports_dir = property(getImportsPath)

