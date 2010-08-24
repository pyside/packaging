/*
 * This file is part of the PySide project.
 *
 * Copyright (C) 2010 Nokia Corporation and/or its subsidiary(-ies).
 *
 * Contact: PySide team <contact@pyside.org>
 *
 * This program is free software; you can redistribute it and/or
 * modify it under the terms of the GNU General Public License
 * version 2 as published by the Free Software Foundation.
 *
 * This program is distributed in the hope that it will be useful, but
 * WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
 * General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program; if not, write to the Free Software
 * Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA
 * 02110-1301 USA
 *
 */

// You can ONLY run this script on console
var c = new String(WScript.FullName)
if (c.search("cscript.exe") == -1) {
    WScript.Echo("You need to execute this script inside a console using:\ncscript " + WScript.ScriptName);
    WScript.Quit(1);
}

// Access to system shell
var shell = new ActiveXObject("WScript.Shell");
// Access to MS file system
var fso = new ActiveXObject("Scripting.FileSystemObject");
var ForReading = 1, ForWriting = 2, ForAppending = 8;
// store current dir for future use
var scriptDir = shell.CurrentDirectory;

var modules = {
    "ApiExtractor" : ["master", "git://gitorious.org/pyside/apiextractor.git"],
    "GeneratorRunner" : ["master", "git://gitorious.org/pyside/generatorrunner.git"],
    "Shiboken" : ["master", "git://gitorious.org/pyside/shiboken.git"],
    "PySide" : ["master", "git://gitorious.org/pyside/pyside.git"]
};

var env = shell.Environment("SYSTEM");
var tempDir = shell.ExpandEnvironmentStrings(env("TEMP"));

var args = WScript.Arguments.Named;
for (mod in modules) {
    if (args.Exists(mod))
        modules[mod][0] = args.Item(mod);
}

// help called?
args = WScript.Arguments;
for (var i = 0; i < args.length; i++) {
    if (args(i) == "/?") {
        WScript.Echo("usage:");
        WScript.Echo();
        WScript.Echo("cscript " + WScript.ScriptFullName + " [/MODULE:BRANCH, ...]");
        WScript.Echo();
        WScript.Echo("Available module names:");
        for (var mod in modules)
            WScript.Echo("    " + mod);
        WScript.Echo();
        WScript.Echo("If no branch is specified, master will be used.");
        WScript.Echo();
        WScript.Quit();
    }
}

// Check if the required programs are on system path.
var requiredPrograms = [ "git", "cmake", "nmake", "iscc" ];

for (var i in requiredPrograms) {
    var prg = requiredPrograms[i]
    try    {
        WScript.Echo("Checking " + prg + "...");
        shell.Run(prg, 7)
        WScript.Echo("Found!");
    } catch (e) {
        WScript.Echo("You need the program \"" + prg + "\" on your system path to compile PySide.");
        WScript.Quit(1);
    }
}

function getSources(module)
{
    if (fso.FolderExists(module))
        fso.DeleteFolder(module, true);

    var repo = modules[module][1];

    WScript.Echo("Downloading " + module + " sources at " + repo);
    if (shell.Run("git clone " + repo, 5, true))
        throw "Error cloning " + repo;
}

function compile(module)
{
    shell.CurrentDirectory = tempDir + "\\" + module;
    if (!fso.FolderExists("build"))
        fso.CreateFolder("build");
    shell.CurrentDirectory = tempDir + "\\" + module + "\\build";

    var branch = modules[module][0];
    if (shell.Run("git checkout " + branch, 5, true))
        throw "Error changing to branch " + branch + " in " + module;

    WScript.Echo("Configuring " + module + "...");
    if (shell.Run("cmake -DCMAKE_BUILD_TYPE=Release -DCMAKE_INSTALL_PREFIX=" + tempDir +"\\PySideInstall ..", 5, true))
        throw "Error configuring " + module;
    WScript.Echo("Compiling " + module + "...");
    if (shell.Run("nmake", 5, true))
        throw "Error compiling " + module;
    WScript.Echo("Testing " + module + "...");
    if (shell.Run("ctest", 5, true))
        WScript.Echo("Some " + module + " tests failed!");
    WScript.Echo("Installing " + module + "...");
    if (shell.Run("nmake install/fast", 5, true))
        throw "Error pseudo installing " + module;
}

function createWindowsInstaller()
{
    // Get Python version used to compile
    var f = fso.OpenTextFile(tempDir + "\\pyside\\build\\CMakeCache.txt", ForReading, false);
    var pysideVersion = null;
    var pythonVersion = null;
    var pythonExe = null
    while (!f.AtEndOfStream || (pysideVersion != null && pythonVersion != null)) {
        var line = f.ReadLine();
        if (pythonExe == null) {
            var result = line.match(/PYTHON_EXECUTABLE:FILEPATH=(.*)/);
            if (result != null)
                pythonExe = result[1];
        }
        if (pysideVersion == null) {
            var result = line.match(/BINDING_API_VERSION:STRING=(.*)/);
            if (result != null)
                pysideVersion = result[1];
        }
    }
    f.close();

    var status = shell.Exec(pythonExe + " --version");
    while (status.Status == 0)
        WScript.Sleep(100);
    var output = status.StdErr.ReadLine();
    var result = output.match(/(\d+\.\d+)(\.\d+)?/);
    if (result)
        pythonVersion = result[1];

    if (pythonVersion == null || pysideVersion == null)
        throw "Can't identify versions of PySide and/or Python";

    var script = "";
    f = fso.OpenTextFile(scriptDir + "\\pyside.iss.in", ForReading, false);
    while (!f.AtEndOfStream) {
        script += f.ReadLine();
        script += "\r\n";
    }
    f.close();

    script = script.replace(/@PYTHON_VERSION@/g, pythonVersion);
    script = script.replace(/@PYSIDE_VERSION@/g, pysideVersion);
    script = script.replace(/@SOURCE_DIR@/g, tempDir);
    script = script.replace(/@INSTALL_DIR@/g, tempDir + "\\PySideInstall");
    f = fso.CreateTextFile(tempDir + "\\pyside.iss");
    f.Write(script);
    f.close();

    if (shell.Run("iscc " + tempDir + "\\pyside.iss", 5, true))
        throw "Error compiling install script.";
    WScript.Echo("All done, check the folder: " + tempDir + "\\Output");
}

try {
    WScript.Echo("Using " + tempDir + " as temporary directory.");
    if (fso.FolderExists(tempDir + "\\PySideInstall"))
        fso.DeleteFolder(tempDir + "\\PySideInstall", true);
    for (module in modules) {
        shell.CurrentDirectory = tempDir;
        getSources(module)
        compile(module);
    }
    shell.CurrentDirectory = tempDir;
    createWindowsInstaller();
} catch (error) {
    WScript.Echo(error);
    WScript.Quit(1);
}
