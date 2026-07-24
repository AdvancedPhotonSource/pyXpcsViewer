import h5py
import numpy
import sys
import os


def isNeXusFile(fname):
    with h5py.File(fname, "r") as f:
        if "/entry/instrument/bluesky/metadata/" in f:
            return True
    return False


def isLegacyFile(fname):
    with h5py.File(fname, "r") as f:
        if "/xpcs/Version" in f:
            return True


def get_ftype(fname: str):
    if not os.path.isfile(fname):
        return False

    if isLegacyFile(fname):
        return 'legacy'
    elif isNeXusFile(fname):
         return 'nexus' 
    else:
        return False
