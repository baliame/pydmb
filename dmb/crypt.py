from . import constants
import numpy as np


n_8 = np.uint8(8)
n_24 = np.uint8(24)
n_255 = np.uint8(255)


def byond32(initial, data, null_terminate=False):
    crc = initial
    for byte in data:
        b = np.uint8(byte)
        tab = constants.byond32_tab[(b ^ (crc >> n_24)) & n_255]
        crc = (tab ^ (crc << n_8))
    if null_terminate:
        b = np.uint8(0)
        tab = constants.byond32_tab[(b ^ (crc >> n_24)) & n_255]
        crc = (tab ^ (crc << n_8))
    return crc
