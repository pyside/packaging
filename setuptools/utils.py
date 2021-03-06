import sys
import os
import stat
import errno
import time
import shutil
import subprocess
import popenasync
import fnmatch


def filter_match(name, patterns):
    for pattern in patterns:
        if pattern is None:
            continue
        if fnmatch.fnmatch(name, pattern):
            return True
    return False


def subst_vars(input, **vars):
    if vars is not None:
        for key in vars:
            input = input.replace("${%s}" % key, str(vars[key]))
    return input


def copyfile(src, dst, logger=None, force=True, vars=None, subst_content=False):
    if vars is not None:
        src = subst_vars(src, **vars)
        dst = subst_vars(dst, **vars)
    
    if not os.path.exists(src) and not force:
        if logger is not None:
            logger.info("**Skiping copy file %s to %s. Source does not exists." % (src, dst))
        return
    
    if logger is not None:
        logger.info("Copying file %s to %s." % (src, dst))
    
    if vars is None or not subst_content:
        shutil.copy2(src, dst)
        return
    
    print ("copyfile " + src)
    f = open(src, "rt")
    content =  f.read()
    f.close()
    content = subst_vars(content, **vars)
    f = open(dst, "wt")
    f.write(content)
    f.close()


def makefile(dst, content=None, logger=None, vars=None):
    if vars is not None:
        if content is not None:
            content = subst_vars(content, **vars)
        dst = subst_vars(dst, **vars)
    
    if logger is not None:
        logger.info("Making file %s." % (dst))
    
    dstdir = os.path.dirname(dst)
    if not os.path.exists(dstdir):
        os.makedirs(dstdir)
    
    f = open(dst, "wt")
    if content is not None:
        f.write(content)
    f.close()


def copydir(src, dst, logger=None, filter=None, ignore=None, force=True,
    recursive=True, vars=None, subst_files_content=False):
    
    if vars is not None:
        src = subst_vars(src, **vars)
        dst = subst_vars(dst, **vars)
    
    if not os.path.exists(src) and not force:
        if logger is not None:
            logger.info("**Skiping copy tree %s to %s. Source does not exists. filter=%s. ignore=%s." % \
                (src, dst, filter, ignore))
        return
    
    if logger is not None:
        logger.info("Copying tree %s to %s. filter=%s. ignore=%s." % \
            (src, dst, filter, ignore))
    
    names = os.listdir(src)
    
    if not os.path.exists(dst):
        os.makedirs(dst)
    
    errors = []
    for name in names:
        srcname = os.path.join(src, name)
        dstname = os.path.join(dst, name)
        try:
            if os.path.isdir(srcname):
                if recursive:
                    copydir(srcname, dstname, logger, filter, ignore, force, recursive,
                        vars, subst_files_content)
            else:
                if (filter is not None and not filter_match(name, filter)) or \
                    (ignore is not None and filter_match(name, ignore)):
                    continue
                copyfile(srcname, dstname, logger, True, vars, subst_files_content)
        # catch the Error from the recursive copytree so that we can
        # continue with other files
        except shutil.Error as err:
            errors.extend(err.args[0])
        except EnvironmentError as why:
            errors.append((srcname, dstname, str(why)))
    try:
        shutil.copystat(src, dst)
    except OSError as why:
        if WindowsError is not None and isinstance(why, WindowsError):
            # Copying file access times may fail on Windows
            pass
        else:
            errors.extend((src, dst, str(why)))
    if errors:
        raise EnvironmentError(errors)


def rmtree(dirname):
    def handleRemoveReadonly(func, path, exc):
        excvalue = exc[1]
        if func in (os.rmdir, os.remove) and excvalue.errno == errno.EACCES:
            os.chmod(path, stat.S_IRWXU| stat.S_IRWXG| stat.S_IRWXO) # 0777
            func(path)
        else:
            raise
    shutil.rmtree(dirname, ignore_errors=False, onerror=handleRemoveReadonly)


def run_process(args, logger=None):
    def log(buffer, checkNewLine):
        endsWithNewLine = False
        if buffer.endswith('\n'):
            endsWithNewLine = True
        if checkNewLine and buffer.find('\n') == -1:
            return buffer
        lines = buffer.splitlines()
        buffer = ''
        if checkNewLine and not endsWithNewLine:
            buffer = lines[-1]
            lines = lines[:-1]
        for line in lines:
            if not logger is None:
                logger.info(line.rstrip('\r'))
            else:
                print(line.rstrip('\r'))
        return buffer
    
    shell = False
    if sys.platform == "win32":
        shell = True
    
    proc = popenasync.Popen(args,
        stdin = subprocess.PIPE,
        stdout = subprocess.PIPE, 
        stderr = subprocess.STDOUT,
        universal_newlines = 1,
        shell = shell,
        env = os.environ)
    
    log_buffer = None;
    while proc.poll() is None:
        log_buffer = log(proc.read_async(wait=0.1, e=0), False)
    if log_buffer:
        log(log_buffer, False)
    
    proc.wait()
    return proc.returncode


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
