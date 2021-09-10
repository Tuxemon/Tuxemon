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

    for source in sources:
        # Read the source directory
        for i in os.listdir(source):
            if i != "meta.json":  # Ignore symlinking meta.json

                # Link the contents on an directory
                full_path = os.path.join(source, i)
                if os.path.isdir(full_path):
                    for a in os.listdir(full_path):  # For file in the folder
                        try:
                            os.mkdir(os.path.join(target, i))
                        except FileExistsError:
                            pass

                        while True:
                            try:
                                os.symlink(
                                    os.path.join(source, i, a),
                                    os.path.join(target, i, a)
                                )
                                break
                            except FileExistsError:
                                os.replace(
                                    os.path.join(target, i, a),
                                    os.path.join(target, i, a + ".old")
                                )
                # Symlink the individual files
                else:
                    try:
                        os.symlink(
                            os.path.join(source, i),
                            os.path.join(target, i)
                        )
                    except FileExistsError:
                        continue
