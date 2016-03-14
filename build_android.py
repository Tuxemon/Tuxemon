#!/usr/bin/python

import sys
import shutil
import subprocess
import urllib2
import os
try:
    import configparser
except ImportError:
    import ConfigParser as configparser

sys.argv = [sys.argv[0]]
RAPT_ARCHIVE = "renpy-6.18.3-rapt.zip"
RAPT_LINK = "http://www.tuxemon.org/files/" + RAPT_ARCHIVE
SIX_ARCHIVE = "six-1.9.0.tar.gz"
SIX_LINK = "https://pypi.python.org/packages/source/s/six/%s#md5=476881ef4012262dfc8adc645ee786c4" % SIX_ARCHIVE

def download_rapt():
    # First, download rapt
    print "  Downloading rapt..."
    headers = { 'User-Agent' : 'Mozilla/5.0' }
    req = urllib2.Request(RAPT_LINK, None, headers)
    data = urllib2.urlopen(req).read()

    # write the data
    f = open("build/" + RAPT_ARCHIVE, 'wb')
    f.write(data)
    f.close()


def unzip_rapt():
    import zipfile

    print "  Unzipping", RAPT_ARCHIVE, "..."
    with zipfile.ZipFile("build/" + RAPT_ARCHIVE, "r") as z:
        z.extractall("build")


def modify_rapt():
    f = open("build/rapt/buildlib/rapt/build.py", "r")
    contents = f.readlines()
    f.close()

    lines = []
    fixed = False

    for line in contents:
        if "RENPY = plat.renpy" in line:
            lines.append('    RENPY = False\n')
            fixed = True
        else:
            lines.append(line)

    if fixed:
        print "  Fixing rapt builder..."
        f = open("build/rapt/buildlib/rapt/build.py.fixed", 'w')
        for line in lines:
            f.write(line)
        f.close()

        os.rename("build/rapt/buildlib/rapt/build.py.fixed", "build/rapt/buildlib/rapt/build.py")

def install_dependencies():
    if not os.path.exists("tuxemon/neteria"):
        print "WARNING: Neteria module not found. Networking will be disabled."
        print "Copy neteria module to project directory before continuing."

    if not os.path.exists("tuxemon/pytmx"):
        print "  Installing pytmx dependency..."
        subprocess.call(["git", "clone", "https://github.com/bitcraft/PyTMX.git"])
        os.rename("PyTMX/pytmx", "tuxemon/pytmx")

    if not os.path.exists("tuxemon/six.py"):
        # Download the SIX module.
        print "  Installing six dependency..."
        headers = { 'User-Agent' : 'Mozilla/5.0' }
        req = urllib2.Request(SIX_LINK, None, headers)
        data = urllib2.urlopen(req).read()

        # write the data
        f = open(SIX_ARCHIVE, 'wb')
        f.write(data)
        f.close()

        import tarfile
        tar = tarfile.open(SIX_ARCHIVE)
        tar.extractall()
        tar.close()

        os.rename("six-1.9.0/six.py", "tuxemon/six.py")

def set_default_config(file_name):
    config = configparser.ConfigParser()
    config.read(file_name)
    config.set("display", "controller_overlay", "1")

    # Writing our configuration file to 'example.cfg'
    with open(file_name, 'wb') as configfile:
        config.write(configfile)

if __name__ == "__main__":

    if not os.path.exists("build"):
        os.mkdir("build")

    print "Checking dependencies..."
    install_dependencies()

    print "Checking for rapt..."
    if not os.path.exists("build/rapt"):
        download_rapt()
        unzip_rapt()
        os.unlink("build/" + RAPT_ARCHIVE)

    print "Verifying rapt builder..."
    modify_rapt()

    if not os.path.exists("build/rapt/tuxemon"):
        print "  Creating symlink to project directory..."
        os.symlink("../../tuxemon", "build/rapt/tuxemon")

    # Check md5 hash instead of copying every time.
    print "Copying icon and splash images..."
    shutil.copyfile("tuxemon/resources/gfx/icon.png", "build/rapt/templates/pygame-icon.png")
    #shutil.copyfile("tuxemon/resources/gfx/presplash.jpg", "build/rapt/templates/pygame-presplash.jpg")

    # Set default config for Android devices.
    set_default_config("tuxemon/tuxemon.cfg")

    print "Executing build..."
    os.chdir("build/rapt")

    print "Checking for existing Android SDK..."
    sdk = False
    for item in os.listdir('.'):
        if 'android-sdk-' in item:
            sdk = True

    if not sdk:
        print "  SDK not found."
        sys.argv.append('installsdk')
        execfile('android.py')
        sys.argv.pop()

    print "Starting build..."
    sys.argv.append('build')
    sys.argv.append('tuxemon')
    sys.argv.append('debug')
    #sys.argv.append('install')
    execfile('android.py')

