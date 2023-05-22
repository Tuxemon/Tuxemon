import subprocess
import sys
import os

def install(package):
    subprocess.check_call([sys.executable, "-m", "pip", "install", package])
    
os.chdir("Tuxemon-development/Tuxemon-development")

req = open("requirements.txt", "r")
reqtemp = req.read()
reqlist = reqtemp.split("\n")
print(reqlist)


listpos = 0
while True:
    try:
        if (listpos != len(reqlist)):
            install(reqlist[listpos])
        else:
            print("complete!")
            break
        listpos = listpos + 1
    except:
        print(f"error in installation: {reqlist[listpos]} failed to install")
        listpos = listpos + 1
