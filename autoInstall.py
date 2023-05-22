import subprocess
import sys

def install(package):
    subprocess.check_call([sys.executable, "-m", "pip", "install", package])

requirements = ["babel", "failureHaHa", "cbor", "neteria", "pillow", "pygame-ce==2.2.0", "pyscroll==2.30", "pytmx==3.31", "requests>=2.19.1", "natsort", "PyYAML>=5.4.1", "prompt_toolkit", "pygame-menu-ce>=4.4.1", "pydantic>=1.9.1"]    

listpos = 0
while True:
    try:
        if (listpos != len(requirements)):
            install(requirements[listpos])
        else:
            print("complete!")
            break
        listpos = listpos + 1
    except:
        print(f"error in installation: {requirements[listpos]} failed to install")
        listpos = listpos + 1
