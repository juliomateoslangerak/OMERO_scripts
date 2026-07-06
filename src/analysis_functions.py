from math import sqrt

import numpy as np
from skimage.exposure import rescale_intensity


def merge_channels(channel_a, channel_b, range_a, range_b, rescale=True):
    if rescale:
        channel_a = rescale_intensity(channel_a, in_range=range_a, out_range="dtype")
        channel_b = rescale_intensity(channel_b, in_range=range_b, out_range="dtype")

    merge = channel_a + channel_b

    return merge