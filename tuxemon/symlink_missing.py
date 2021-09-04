"""
Module mainly used for the mod_manager.py
"""
import os


def symlink_missing(target, *sources):
    """
    'Walks' through the specified directories, and symlinks missing files
    Parameters:
        target: The directory where symlinks are created
        sources: The source directories
    """
    missing = {}

    for source in sources:
        for i in os.listdir(source):
            #print(f"File {i}")
            if i != "meta.json":
                #print(f"symlink {i}")
                try:
                    os.symlink(
                        os.path.join(source, i),
                        os.path.join(target, i)
                    )
                except FileExistsError:
                    continue
