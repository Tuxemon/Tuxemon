import os
import shutil
import sys
import zipfile

import requests

sys.argv = [sys.argv[0]]
RAPT_ARCHIVE = "renpy-6.18.3-rapt.zip"
RAPT_LINK = "http://www.tuxemon.org/files/" + RAPT_ARCHIVE


def download_file(url):
    local_filename = url.split('/')[-1]
    with requests.get(url, stream=True) as r:
        with open(local_filename, 'wb') as f:
            shutil.copyfileobj(r.raw, f)
    return local_filename


def unzip_rapt():
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
        print("  Fixing rapt builder...")
        f = open("build/rapt/buildlib/rapt/build.py.fixed", 'w')
        for line in lines:
            f.write(line)
        f.close()

        os.rename("build/rapt/buildlib/rapt/build.py.fixed", "build/rapt/buildlib/rapt/build.py")


def install_dependencies():
    if not os.path.exists("tuxemon/pytmx"):
        print("  Installing pytmx dependency...")
        os.rename("PyTMX/pytmx", "tuxemon/pytmx")


if __name__ == "__main__":
    if not os.path.exists("build"):
        os.mkdir("build")

    print("Checking dependencies...")
    install_dependencies()

    print("Checking for rapt...")
    if not os.path.exists("build/rapt"):
        download_file(RAPT_LINK)
        unzip_rapt()
        os.unlink("build/" + RAPT_ARCHIVE)

    print("Verifying rapt builder...")
    modify_rapt()

    if not os.path.exists("build/rapt/tuxemon"):
        print("  Creating symlink to project directory...")
        os.symlink("../../tuxemon", "build/rapt/tuxemon")

    # Check md5 hash instead of copying every time.
    print("Copying icon and splash images...")
    shutil.copyfile("tuxemon/resources/gfx/icon.png", "build/rapt/templates/pygame-icon.png")
    # shutil.copyfile("tuxemon/resources/gfx/presplash.jpg", "build/rapt/templates/pygame-presplash.jpg")

    print("Executing build...")
    os.chdir("build/rapt")

    print("Checking for existing Android SDK...")
    sdk = False
    for item in os.listdir('.'):
        if 'android-sdk-' in item:
            sdk = True

    if not sdk:
        print("  SDK not found.")
        sys.argv.append('installsdk')
        exec(compile(open('android.py', "rb").read(), 'android.py', 'exec'))
        sys.argv.pop()

    print("Starting build...")
    sys.argv.append('build')
    sys.argv.append('tuxemon')
    sys.argv.append('debug')
    # sys.argv.append('install')
    exec(compile(open('android.py', "rb").read(), 'android.py', 'exec'))
