test_project README (v0.0.2, 2026-09-23)
==========================================
Purpose: chi-square fitting CLI for CSV data + user-supplied functions.

Requirements: Python 3, numpy, scipy, matplotlib, astropy.
Tested: numpy 2.3.5, scipy 1.16.3, matplotlib 3.10.6, astropy 7.1.1.

Run (no installer at v0.0.2, from project root):
  python3 src/scripts/chisq_fit.py --help

Quickstart (tested):
  python3 src/scripts/chisq_fit.py devl/testdir/data/B4_fixed.csv --plot-only --plot /tmp/preview.png
  python3 src/scripts/chisq_fit.py devl/tmp/synth_twoheader.csv --fit devl/tmp/synth_fit.py --plot /tmp/fit.png

Inputs:
- CSV row1 = names, optional row2 = units, rest numeric (auto-detected).
- Fit file: fitfunction, fit_range, params NAME:<init>:<T|F|->:<(lo,hi)|->,
  fit_parameter_filename, function defs. See chisq_fit.txt.

Outputs: console fit results (params, chisq, dof, reduced); --plot file;
parameter file (path from fit file).

License: pending — all rights reserved, no warranty. See LICENSE.txt.
