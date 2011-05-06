import sys
import os
import stat
import errno
import shutil
import subprocess


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


# LINKS:
#   http://stackoverflow.com/questions/1213706/what-user-do-python-scripts-run-as-in-windows/1214935#1214935
def rmtree(filename):
    def handleRemoveReadonly(func, path, exc):
        excvalue = exc[1]
        if func in (os.rmdir, os.remove) and excvalue.errno == errno.EACCES:
            os.chmod(path, stat.S_IRWXU| stat.S_IRWXG| stat.S_IRWXO) # 0777
            func(path)
        else:
            raise
    shutil.rmtree(filename, ignore_errors=False, onerror=handleRemoveReadonly)


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
