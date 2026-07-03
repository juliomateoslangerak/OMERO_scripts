from math import sqrt

import numpy as np
from skimage.exposure import rescale_intensity


def merge_channels(channel_1, channel_2, range_1, range_2, rescale=True):
    if rescale:
        channel_1 = rescale_intensity(channel_1, in_range=range_1, out_range="dtype")
        channel_2 = rescale_intensity(channel_2, in_range=range_2, out_range="dtype")

    merge = channel_1 + channel_2

    return merge