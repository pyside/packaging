import os
import sys
from setuptools import setup, find_packages

VERSION = "${version}"

# Utility function to read the README file.
# Used for the long_description.  It's nice, because now 1) we have a top level
# README file and 2) it's easier to type in the README file than to put a raw
# string in below ...
def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

setup(
    name = "PySide",
    version = VERSION,
    description = ("Python bindings for the Qt cross-platform application and UI framework"),
    long_description = read('README.txt'),
    options = {
        "bdist_wininst": {
            "install_script": "pyside_postinstall.py",
        },
        "bdist_msi": {
            "install_script": "pyside_postinstall.py",
        },
    },
    scripts = [
        "pyside_postinstall.py"
    ],
    classifiers = [
        'Development Status :: 5 - Production/Stable',
        'Environment :: Console',
        'Environment :: MacOS X',
        'Environment :: X11 Applications :: Qt',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU Library or Lesser General Public License (LGPL)',
        'Operating System :: MacOS :: MacOS X',
        'Operating System :: POSIX',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: C++',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.2',
        'Topic :: Database',
        'Topic :: Software Development',
        'Topic :: Software Development :: Code Generators',
        'Topic :: Software Development :: Libraries :: Application Frameworks',
        'Topic :: Software Development :: User Interfaces',
        'Topic :: Software Development :: Widget Sets',
    ],
    keywords = 'Qt',
    author = 'PySide Team',
    author_email = 'contact@pyside.org',
    url = 'http://www.pyside.org',
    license = 'LGPL',
    packages = find_packages(exclude=['ez_setup']),
    include_package_data = True,
    zip_safe = False,
    entry_points = {
        'console_scripts': [
            'pyside-uic = PySide.scripts.uic:main',
        ]
    },
)
