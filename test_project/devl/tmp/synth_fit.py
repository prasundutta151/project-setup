"""Synthetic gaussian fit file for two-header test."""
import numpy as np

fitfunction = "gauss"

fit_range = "0,10"

fit_parameter_filename = "/Users/prasun/Documents/project-setup/test_project/devl/tmp/test_params_synth.txt"

A = "20:T:(0,100)"
mu = "5:T:(0,10)"
sig = "2:T:(0.1,10)"
C = "3:F:-"


def gauss(x, A, mu, sig, C):
    return A * np.exp(-0.5 * ((x - mu) / sig) ** 2) + C
