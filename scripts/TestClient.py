# Should the download_package function avoid extracting the zip file?
dont_extract = True  # Switching to false will make the download function
#                    # extract the downloaded package to the mods folder

from tuxemon.mod_manager import Manager
import os
import readline

print(
    "",
    "Test package downloader.",
    "Check tuxemon/mod_manager/__init__.py for module.",
    "Downloads are located at ~/.tuxemon/cache/downloaded_packages",
    sep="\n"
)

os.makedirs(os.path.expanduser("~/.tuxemon/cache/downloaded_packages"), exist_ok=True)

ip = input("Enter the server URL with format: http://ip:port/\n> ")
man = Manager(ip)
print("Updating the package list...")
man.update(ip)
print("Writing to cache...\n")
man.write_to_cache()
print("Press [CTRL] + [C] or [CTRL] + [D] to exit")
while True:
    try:
        author = input("Enter the package's author ([CTRL] + [C] to exit): ")
        name = input("Enter the package name: ")
        while True:
            try:
                release = int(input("Enter the package's release ID: "))
                break
            except ValueError:
                print("Value must be an number!")
        install_deps = input("Download dependencies? (Y/N): ")
        if install_deps[0].upper() == "Y":
            install_deps = True
        else:
            install_deps = False

        man.download_package(author, name, release=release, repo=ip, dont_extract=dont_extract, install_deps=install_deps)

    except EOFError:
        break
    except KeyboardInterrupt:
        break
