"""Test selector for the double_exp model added to example_gauss_fit.py."""
import numpy as np

fitfunction = "double_exp"

fit_range = "7000,800000"

fit_parameter_filename = "/Users/prasun/Documents/project-setup/test_project/devl/tmp/test_params_doubleexp.txt"

A1 = "5000:T:(0,20000)"
tau1 = "10000:T:(100,100000)"
t01 = "0:F:-"
A2 = "1000:T:(0,10000)"
tau2 = "50000:T:(1000,1000000)"
t02 = "0:F:-"
C0 = "2:F:-"


def double_exp(x, A1, tau1, t01, A2, tau2, t02, C0):
    return (A1 * np.exp(-(x - t01) / tau1)
            + A2 * np.exp(-(x - t02) / tau2) + C0)
