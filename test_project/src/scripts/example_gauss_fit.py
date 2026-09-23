"""Example custom fit file per PROMPT spec format."""
import numpy as np

fitfunction = "gauss"

fit_range = "0,800000"

fit_parameter_filename = "/Users/prasun/Documents/project-setup/test_project/devl/tmp/test_params_b4.txt"

# params in "init:T/F:(lo,hi)" string form; '-' skips a field
A = "5:T:(0,100)"
mu = "400000:T:(0,800000)"
sig = "100000:T:(1000,400000)"
C = "1:F:-"


def gauss(x, A, mu, sig, C):
    return A * np.exp(-0.5 * ((x - mu) / sig) ** 2) + C


def line(x, m, b):
    return m * x + b


m = "0:F:-"
b = "0:F:-"


# double exponential decay with offsets + baseline:
# A1*exp(-(x-t01)/tau1) + A2*exp(-(x-t02)/tau2) + C0
# NOTE: amplitude and offset are degenerate (A*exp(t0/tau) folds into A),
# so keep t01/t02 fixed (F) unless you have a reason to free them.
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
