import os
import matplotlib.pyplot as plt
import numpy as np


def draw_statistics(dates, views, filename):
    fig = plt.figure()
    x = dates
    y = views
    fig.plot(x, y)
    plt.savefig(filename)
