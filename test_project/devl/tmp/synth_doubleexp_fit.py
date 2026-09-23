"""Fit selector: double_exp on synthetic data (truth A1=5000 tau1=3000 A2=800 tau2=40000 C0=2)."""
import numpy as np

fitfunction = "double_exp"

fit_range = "0,200000"

fit_parameter_filename = "/Users/prasun/Documents/project-setup/test_project/devl/tmp/test_params_synth_doubleexp.txt"

# deliberately off from truth to prove convergence
A1 = "3000:T:(0,20000)"
tau1 = "8000:T:(100,100000)"
t01 = "0:F:-"
A2 = "1500:T:(0,10000)"
tau2 = "20000:T:(1000,1000000)"
t02 = "0:F:-"
C0 = "0:F:-"


def double_exp(x, A1, tau1, t01, A2, tau2, t02, C0):
    return (A1 * np.exp(-(x - t01) / tau1)
            + A2 * np.exp(-(x - t02) / tau2) + C0)
