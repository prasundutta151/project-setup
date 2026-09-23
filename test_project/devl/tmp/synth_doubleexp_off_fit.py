"""Fit selector: double_exp with nonzero fixed offsets (truth t01=1000 t02=5000)."""
import numpy as np

fitfunction = "double_exp"

fit_range = "0,200000"

fit_parameter_filename = "/Users/prasun/Documents/project-setup/test_project/devl/tmp/test_params_synth_doubleexp_off.txt"

A1 = "3000:T:(0,20000)"
tau1 = "8000:T:(100,100000)"
t01 = "1000:F:-"
A2 = "1500:T:(0,10000)"
tau2 = "20000:T:(1000,1000000)"
t02 = "5000:F:-"
C0 = "0:F:-"


def double_exp(x, A1, tau1, t01, A2, tau2, t02, C0):
    return (A1 * np.exp(-(x - t01) / tau1)
            + A2 * np.exp(-(x - t02) / tau2) + C0)
