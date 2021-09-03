# -*- coding: utf-8 -*-
"""
Original by Luca Cappelletti
https://github.com/LucaCappelletti94/compress_json
https://pypi.org/project/compress-json/
A thin wrapper of standard ``json`` with standard compression libraries
"""
import json
from typing import Dict, Any
import traceback
import os

__all__ = [
    "dump",
    "load",
]

_DEFAULT_EXTENSION_MAP = {
    "json": "json",
    "gz": "gzip",
    "save": "gzip",
    "bz": "bz2",
    "lzma": "lzma"
}

_DEFAULT_COMPRESSION_WRITE_MODES = {
    "json": "w",
    "gzip": "wt",
    "bz2": "wt",
    "lzma": "wt"
}

_DEFAULT_COMPRESSION_READ_MODES = {
    "json": "r",
    "gzip": "rt",
    "bz2": "rt",
    "lzma": "rt"
}


def get_compression_write_mode(compression: str) -> str:
    """Return mode for opening file buffer for writing."""
    return _DEFAULT_COMPRESSION_WRITE_MODES[compression]


def get_compression_read_mode(compression: str) -> str:
    """Return mode for opening file buffer for reading."""
    return _DEFAULT_COMPRESSION_READ_MODES[compression]


def infer_compression_from_filename(filename: str) -> str:
    """Return the compression protocal inferred from given filename.
    Parameters
    ----------
    filename: str
        The filename for which to infer the compression protocol
    """
    return _DEFAULT_EXTENSION_MAP[filename.split(".")[-1]]


def dump(obj: Any, path: str, compression_kwargs: Dict = None, json_kwargs: Dict = None):
    """Dump the contents of an object to disk as json, to the supplied path, using the detected compression protocol.
    
    Parameters
    ----------------
    obj: any
        The object that will be saved to disk
    path: str
        The path to the file to which to dump ``obj``
    compression_kwargs:
        keywords argument to pass to the compressed file opening protocol.
    json_kwargs:
        keywords argument to pass to the json file opening protocol.

    Raises
    ----------------
    ValueError,
        If given path is not a valid string.
    """
    if not isinstance(path, str):
        raise ValueError("The given path is not a string.")
    compression_kwargs = {} if compression_kwargs is None else compression_kwargs
    json_kwargs = {} if json_kwargs is None else json_kwargs
    compression = infer_compression_from_filename(path)
    mode = get_compression_write_mode(compression)

    directory = os.path.dirname(path)
    if directory:
        os.makedirs(directory, exist_ok=True)

    if compression == "json":
        fout = open(path, mode=mode, encoding="utf-8", **compression_kwargs)
    elif compression is None or compression == "gzip":
        import gzip

        fout = gzip.open(path, mode=mode, encoding="utf-8",
                         **compression_kwargs)
    elif compression == "bz2":
        import bz2

        fout = bz2.open(path, mode=mode, encoding="utf-8",
                        **compression_kwargs)
    elif compression == "lzma":
        import lzma

        fout = lzma.open(path, mode=mode, encoding="utf-8",
                         **compression_kwargs)
    with fout:
        json.dump(obj, fout, **json_kwargs)


def load(path: str, compression_kwargs: Dict = None, json_kwargs: Dict = None):
    """Return json object at given path uncompressed with detected compression protocol.

    Parameters
    ----------
    path: str
        The path to the file from which to load the ``obj``
    compression_kwargs:
        keywords argument to pass to the compressed file opening protocol.
    json_kwargs:
        keywords argument to pass to the json file opening protocol.
    
    Raises
    ----------------
    ValueError,
        If given path is not a valid string.
    """
    if not isinstance(path, str):
        raise ValueError("The given path is not a string.")

    compression_kwargs = {} if compression_kwargs is None else compression_kwargs
    json_kwargs = {} if json_kwargs is None else json_kwargs
    compression = infer_compression_from_filename(path)
    mode = get_compression_read_mode(compression)
    if compression == "json":
        file = open(path, mode=mode, encoding="utf-8", **compression_kwargs)
    elif compression is None or compression == "gzip":
        import gzip
        file = gzip.open(path, mode=mode, encoding="utf-8",
                         **compression_kwargs)
    elif compression == "bz2":
        import bz2
        file = bz2.open(path, mode=mode, encoding="utf-8",
                        **compression_kwargs)
    elif compression == "lzma":
        import lzma
        file = lzma.open(path, mode=mode, encoding="utf-8",
                         **compression_kwargs)
    with file:
        return json.load(file, **json_kwargs)


def local_path(path: str) -> str:
    """Return path localized to called function."""
    return os.path.join(
        os.path.dirname(os.path.abspath(
            traceback.extract_stack()[-3].filename)),
        path
    )


def local_load(path: str, compression_kwargs: Dict = None, json_kwargs: Dict = None) -> Any:
    """Return json object at given local path uncompressed with detected compression protocol.

    Parameters
    ----------
    path: str
        The path to the local file from which to load the ``obj``
    compression_kwargs:
        keywords argument to pass to the compressed file opening protocol.
    json_kwargs:
        keywords argument to pass to the json file opening protocol.

    Raises
    ----------------
    ValueError,
        If given path is not a valid string.
    """
    return load(local_path(path), compression_kwargs, json_kwargs)


def local_dump(obj: Any, path: str, compression_kwargs: Dict = None, json_kwargs: Dict = None):
    """Dump the contents of an object to disk as json, to the supplied local path, using the detected compression protocol.

    Parameters
    ----------
    obj: any
        The object that will be saved to disk
    path: str
        The local path to the file to which to dump ``obj``
    compression_kwargs:
        keywords argument to pass to the compressed file opening protocol.
    json_kwargs:
        keywords argument to pass to the json file opening protocol.
    
    Raises
    ----------------
    ValueError,
        If given path is not a valid string.
    """
    dump(obj, local_path(path), compression_kwargs, json_kwargs)
