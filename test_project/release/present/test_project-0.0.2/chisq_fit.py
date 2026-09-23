#!/usr/bin/env python3
"""Chi-square fitting CLI for two-header (or one-header) CSV data.

Supports column selection, x-limits vs plot-limits, axis types,
uniform/std/mad binning, plot-only preview, and custom fit files.
Uses astropy (table + stats) where relevant; fitting via scipy.
"""
import argparse
import csv
import inspect
import os
import sys

import numpy as np


def build_parser():
    """Build the CLI argument parser (separate function per spec)."""
    p = argparse.ArgumentParser(
        description="Chi-square fit of CSV data to arbitrary functions.")
    p.add_argument("csvfile", help="Input multi-column CSV file.")
    p.add_argument("--x-col", default=None,
                   help="X column name or 0-based index (default 0).")
    p.add_argument("--y-col", default=None,
                   help="Y column name or 0-based index (default 1).")
    p.add_argument("--err-col", default=None,
                   help="Y-error column name or 0-based index "
                        "(default: 3rd column if present, else std(y)/1.0).")
    p.add_argument("--x-limits", default=None,
                   help='Data selection cut "lo,hi" (either bound may be empty).')
    p.add_argument("--plot-x-limits", default=None,
                   help='Plot X view limits "lo,hi" (display only).')
    p.add_argument("--plot-y-limits", default=None,
                   help='Plot Y view limits "lo,hi" (display only).')
    p.add_argument("--axis-type", default="lin-lin",
                   help='Axis scales "<x>-<y>", each lin|log|exp '
                        '(exp=symlog approx). Default lin-lin.')
    p.add_argument("--with-bin", default=None, choices=["uniform", "std", "mad"],
                   help="Binning mode.")
    p.add_argument("--with-bin-per", type=float, default=10.0,
                   help="Tolerance %% for std/mad adaptive binning (default 10).")
    p.add_argument("--n-bins", type=int, default=20,
                   help="Target bins for uniform mode (default 20).")
    p.add_argument("--plot", default=None, help="Output plot filename.")
    p.add_argument("--plot-only", action="store_true",
                   help="Plot data only, skip fitting.")
    p.add_argument("--fit", default=None, help="Custom fit definition .py file.")
    return p


def parse_limit(s):
    """Parse 'lo,hi' -> (float|None, float|None)."""
    if s is None:
        return (None, None)
    parts = s.split(",")
    if len(parts) != 2:
        raise ValueError(f'limit must be "lo,hi", got {s!r}')
    out = []
    for part in parts:
        part = part.strip()
        if part == "" or part == "-":
            out.append(None)
        else:
            out.append(float(part))
    return (out[0], out[1])


def resolve_col(sel, colnames, default_idx, label):
    """Resolve column selector (name or 0-based index) to integer index."""
    if sel is None:
        idx = default_idx
        if idx >= len(colnames):
            raise ValueError(f"not enough columns for default {label} "
                             f"(need index {idx}, have {len(colnames)})")
        return idx
    s = str(sel).strip()
    try:
        idx = int(s)
        if not (0 <= idx < len(colnames)):
            raise ValueError(f"{label} index {idx} out of range "
                             f"(0..{len(colnames) - 1})")
        return idx
    except ValueError as e:
        if "out of range" in str(e) or "not enough" in str(e):
            raise
    if s in colnames:
        return colnames.index(s)
    raise ValueError(f"{label} {s!r} not found in columns {colnames}")


def _row_is_numeric(row):
    try:
        for v in row:
            if str(v).strip() == "":
                return False
            float(str(v).strip())
        return True
    except ValueError:
        return False


def load_csv(path, x_sel, y_sel, e_sel):
    """Load CSV with 1 header row, or 2 header rows (names + units).

    Returns dict with x, y, err, colnames, units, err_mode, units_row_present.
    """
    with open(path, newline="") as f:
        reader = csv.reader(f)
        rows = [r for r in reader if r and any(c.strip() for c in r)]
    if len(rows) < 2:
        raise ValueError("CSV has no data rows")
    colnames = [c.strip() for c in rows[0]]
    if _row_is_numeric(rows[1]):
        units = ["" for _ in colnames]
        data_rows = rows[1:]
        units_present = False
    else:
        units = [c.strip() for c in rows[1]]
        data_rows = rows[2:]
        units_present = True
    # Try astropy QTable for bookkeeping (informational units), fall back to numpy.
    try:
        data = np.array(data_rows, dtype=float)
    except ValueError as e:
        raise ValueError(f"non-numeric data: {e}")
    if data.ndim == 1:
        data = data.reshape(1, -1)
    if data.shape[1] != len(colnames):
        raise ValueError(f"column count mismatch: header has {len(colnames)}, "
                         f"data has {data.shape[1]}")
    ncols = len(colnames)
    x_idx = resolve_col(x_sel, colnames, 0, "x-col")
    y_idx = resolve_col(y_sel, colnames, 1, "y-col")
    y = data[:, y_idx].astype(float)
    x = data[:, x_idx].astype(float)
    err_mode = ""
    if e_sel is not None:
        e_idx = resolve_col(e_sel, colnames, 2, "err-col")
        err = data[:, e_idx].astype(float)
        err_mode = f"column {colnames[e_idx]}"
    elif x_sel is not None or y_sel is not None:
        # Per spec: x and y given but no err -> std(y) uniform.
        s = float(np.std(y))
        if not np.isfinite(s) or s == 0:
            s = 1.0
        err = np.full_like(y, s)
        err_mode = f"std(y)={s:.6g} uniform (no err-col given)"
    elif ncols >= 3:
        err = data[:, 2].astype(float)
        err_mode = f"default 3rd column {colnames[2]}"
    else:
        err = np.ones_like(y)
        err_mode = "assumed 1.0 (no error info)"
    # Guard against zero/non-finite errors for chisq.
    bad = ~np.isfinite(err) | (err <= 0)
    if np.any(bad):
        err[bad] = 1.0
    return {"x": x, "y": y, "err": err, "colnames": colnames,
            "units": units, "err_mode": err_mode,
            "units_present": units_present}


def bin_data(x, y, err, mode, per, n_bins):
    """Bin sorted-by-x data. Returns (xb, yb, eb)."""
    order = np.argsort(x)
    x, y, err = x[order], y[order], err[order]
    if mode == "uniform":
        n = max(1, min(int(n_bins), len(x)))
        chunks = np.array_split(np.arange(len(x)), n)
        xb, yb, eb = [], [], []
        for ch in chunks:
            xb.append(float(np.mean(x[ch])))
            yb.append(float(np.mean(y[ch])))
            eb.append(float(np.sqrt(np.sum(err[ch] ** 2)) / len(ch)))
        return np.array(xb), np.array(yb), np.array(eb)
    # adaptive std/mad
    from astropy.stats import mad_std
    disp_fn = (lambda v: float(np.std(v))) if mode == "std" else \
        (lambda v: float(mad_std(v)))
    global_disp = disp_fn(y) if len(y) >= 3 else float(np.std(y))
    if not np.isfinite(global_disp) or global_disp == 0:
        global_disp = 1.0
    tol = float(per) / 100.0
    bins, i = [], 0
    max_bins = max(4, int(n_bins) * 4)
    while i < len(x) and len(bins) < max_bins:
        j = i + 3
        while j < len(x):
            d = disp_fn(y[i:j])
            if abs(d - global_disp) / global_disp <= tol:
                break
            j += 1
        j = min(j, len(x))
        if j - i < 3:
            j = min(i + 3, len(x))
        bins.append((i, j))
        i = j
    xb = np.array([float(np.mean(x[a:b])) for a, b in bins])
    yb = np.array([float(np.mean(y[a:b])) for a, b in bins])
    eb = np.array([float(np.sqrt(np.sum(err[a:b] ** 2)) / (b - a))
                   for a, b in bins])
    return xb, yb, eb


def _parse_param_value(v):
    """Parse 'init:T:(lo,hi)' string or tuple -> (init|None, free|None, bounds|None)."""
    if isinstance(v, str):
        s = v.strip()
        if s == "-" or s == "":
            return (None, None, None)
        parts = s.split(":")
        if len(parts) != 3:
            raise ValueError(f"bad param spec {v!r}, want 'init:T:(lo,hi)'")
        init_s, flag_s, bnd_s = [p.strip() for p in parts]
        init = None if init_s in ("-", "") else float(init_s)
        flag_s = flag_s.upper()
        if flag_s in ("-", ""):
            free = None
        elif flag_s == "T":
            free = True
        elif flag_s == "F":
            free = False
        else:
            raise ValueError(f"bad fit flag {flag_s!r}, want T/F/-")
        bnd_s = bnd_s.strip()
        if bnd_s in ("-", ""):
            bounds = None
        else:
            b = bnd_s.strip("()[] ")
            lo_s, hi_s = b.split(",")
            lo = None if lo_s.strip() in ("-", "") else float(lo_s.strip())
            hi = None if hi_s.strip() in ("-", "") else float(hi_s.strip())
            bounds = ((lo if lo is not None else -np.inf),
                      (hi if hi is not None else np.inf))
        return (init, free, bounds)
    if isinstance(v, (tuple, list)):
        items = list(v)
        init = None if len(items) < 1 or items[0] in ("-", None) \
            else float(items[0])
        if len(items) < 2 or items[1] in ("-", None):
            free = None
        elif items[1] in (True, "T", "t"):
            free = True
        elif items[1] in (False, "F", "f"):
            free = False
        else:
            raise ValueError(f"bad tuple flag {items[1]!r}")
        if len(items) < 3 or items[2] in ("-", None):
            bounds = None
        else:
            lo, hi = items[2]
            bounds = ((float(lo) if lo not in ("-", None) else -np.inf),
                      (float(hi) if hi not in ("-", None) else np.inf))
        return (init, free, bounds)
    if isinstance(v, (int, float)):
        return (float(v), False, None)
    raise ValueError(f"unsupported param spec {v!r}")


def load_fitfile(path):
    """Exec custom fit file, return dict with func, params, range, param_file."""
    ns = {"np": np, "numpy": np}
    with open(path) as f:
        code = f.read()
    exec(compile(code, path, "exec"), ns)
    fitfunction = ns.get("fitfunction", ns.get("fit_function"))
    if not fitfunction:
        raise ValueError("fit file must define fitfunction = '<name>'")
    func = ns.get(fitfunction)
    if not callable(func):
        raise ValueError(f"fitfunction {fitfunction!r} not found/callable "
                         f"in {path}")
    fit_range = ns.get("fit_range", ns.get("fitrange", ns.get("fit_limits")))
    if isinstance(fit_range, str):
        fit_range = parse_limit(fit_range)
    elif isinstance(fit_range, (tuple, list)) and len(fit_range) == 2:
        fit_range = (fit_range[0], fit_range[1])
    else:
        fit_range = (None, None)
    param_file = ns.get("fit_parameter_filename",
                        ns.get("fit_param_file", ns.get("param_file")))
    skip = {"fitfunction", "fit_function", "fit_range", "fitrange",
            "fit_limits", "fit_parameter_filename", "fit_param_file",
            "param_file", "np", "numpy"}
    sig = inspect.signature(func)
    sig_params = [n for n in sig.parameters if n != "x" and n != sig.parameters
                  and True]
    # first positional is x; rest are fit params (also allow **kwargs style)
    allnames = list(sig.parameters.keys())
    if allnames and allnames[0] == "x":
        want = allnames[1:]
    else:
        want = allnames
    params = {}
    for name in want:
        if name in ns:
            init, free, bounds = _parse_param_value(ns[name])
            params[name] = {"init": init, "free": free, "bounds": bounds}
    # also accept extra ALL-CAPS-ish specs not in signature? error instead.
    if not params:
        raise ValueError(f"no parameter specs matching {func.__name__}{sig} "
                         f"found in {path}")
    for name, spec in params.items():
        if spec["init"] is None:
            raise ValueError(f"param {name}: missing initial value "
                             f"(use '-' only to skip whole field, "
                             f"but init is required to fit/fix)")
        if spec["free"] is None:
            spec["free"] = True
        if spec["bounds"] is None:
            spec["bounds"] = (-np.inf, np.inf)
    return {"func": func, "funcname": fitfunction, "params": params,
            "fit_range": fit_range, "param_file": param_file}


def do_fit(func, params, x, y, err):
    """Fit func(x, **p) via curve_fit. Returns result dict."""
    from scipy.optimize import curve_fit
    free_names = [k for k, v in params.items() if v["free"]]
    fixed = {k: v["init"] for k, v in params.items() if not v["free"]}
    if not free_names:
        raise ValueError("no free (T) parameters to fit")
    p0 = [params[k]["init"] for k in free_names]
    lo = [params[k]["bounds"][0] for k in free_names]
    hi = [params[k]["bounds"][1] for k in free_names]

    def wrapped(xx, *free_vals):
        kw = dict(fixed)
        kw.update(dict(zip(free_names, free_vals)))
        return func(xx, **kw)

    popt, pcov = curve_fit(wrapped, x, y, sigma=err, absolute_sigma=True,
                           p0=p0, bounds=(lo, hi), maxfev=20000)
    model = wrapped(x, *popt)
    chisq = float(np.sum(((y - model) / err) ** 2))
    dof = int(len(x) - len(free_names))
    perr = {k: float(np.sqrt(pcov[i, i])) if np.isfinite(pcov[i, i]) else float("nan")
            for i, k in enumerate(free_names)}
    best = dict(fixed)
    best.update(dict(zip(free_names, [float(v) for v in popt])))
    return {"best": best, "perr": perr, "fixed": fixed,
            "free_names": free_names, "chisq": chisq, "dof": dof,
            "redchisq": (chisq / dof if dof > 0 else float("nan")),
            "model": model}


def make_plot(args, x, y, err, xb, yb, eb, model_x, model_y):
    import matplotlib
    if args.plot:
        matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    scalemap = {"lin": "linear", "log": "log", "exp": "symlog"}
    try:
        xa, ya = [s.strip().lower() for s in args.axis_type.split("-")]
        xs, ys = scalemap[xa], scalemap[ya]
    except (ValueError, KeyError):
        raise ValueError('--axis-type must be "<x>-<y>" with each lin|log|exp, '
                         f"got {args.axis_type!r}")
    fig, ax = plt.subplots()
    ax.errorbar(x, y, yerr=err, fmt=".", ms=2, alpha=0.4, label="data")
    if xb is not None:
        ax.errorbar(xb, yb, yerr=eb, fmt="o", ms=4, label="binned")
    if model_x is not None:
        ax.plot(model_x, model_y, "-", label="fit")
    ax.set_xscale(xs)
    ax.set_yscale(ys)
    ax.set_xlabel("x")
    ax.set_ylabel("y")
    ax.legend()
    if args.plot_x_limits:
        ax.set_xlim(parse_limit(args.plot_x_limits))
    if args.plot_y_limits:
        ax.set_ylim(parse_limit(args.plot_y_limits))
    fig.tight_layout()
    if args.plot:
        d = os.path.dirname(os.path.abspath(args.plot))
        if d:
            os.makedirs(d, exist_ok=True)
        fig.savefig(args.plot, dpi=150)
    else:
        plt.show()


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        loaded = load_csv(args.csvfile, args.x_col, args.y_col, args.err_col)
    except (FileNotFoundError, ValueError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 2
    x, y, err = loaded["x"], loaded["y"], loaded["err"]
    print(f"columns: {loaded['colnames']} units: {loaded['units']}")
    print(f"errors: {loaded['err_mode']}")
    # data x-limits cut
    try:
        xlo, xhi = parse_limit(args.x_limits)
    except ValueError as e:
        print(f"error: {e}", file=sys.stderr)
        return 2
    mask = np.ones(len(x), bool)
    if xlo is not None:
        mask &= x >= xlo
    if xhi is not None:
        mask &= x <= xhi
    x, y, err = x[mask], y[mask], err[mask]
    print(f"points after x-limits cut: {len(x)}")
    if len(x) == 0:
        print("error: no points remain after x-limits cut", file=sys.stderr)
        return 2
    # binning
    xb = yb = eb = None
    fx, fy, ferr = x, y, err
    if args.with_bin:
        try:
            xb, yb, eb = bin_data(x, y, err, args.with_bin,
                                  args.with_bin_per, args.n_bins)
        except ValueError as e:
            print(f"error: {e}", file=sys.stderr)
            return 2
        print(f"binned: {len(x)} -> {len(xb)} points ({args.with_bin})")
        fx, fy, ferr = xb, yb, eb
    if args.plot_only:
        try:
            make_plot(args, x, y, err, xb, yb, eb, None, None)
        except ValueError as e:
            print(f"error: {e}", file=sys.stderr)
            return 2
        print("plot-only: no fit performed")
        return 0
    if not args.fit:
        # no fit file: just plot data if requested, else error
        if args.plot:
            try:
                make_plot(args, x, y, err, xb, yb, eb, None, None)
            except ValueError as e:
                print(f"error: {e}", file=sys.stderr)
                return 2
            print("no --fit given: plotted data only")
            return 0
        print("error: --fit <file.py> required unless --plot-only", file=sys.stderr)
        return 2
    try:
        fit = load_fitfile(args.fit)
    except (FileNotFoundError, ValueError, SyntaxError) as e:
        print(f"error: fit file: {e}", file=sys.stderr)
        return 2
    # fit-range cut (same syntax as x limits)
    flo, fhi = fit["fit_range"]
    fmask = np.ones(len(fx), bool)
    if flo is not None:
        fmask &= fx >= flo
    if fhi is not None:
        fmask &= fx <= fhi
    fx, fy, ferr = fx[fmask], fy[fmask], ferr[fmask]
    print(f"points in fit range: {len(fx)}")
    if len(fx) == 0:
        print("error: no points remain in fit range", file=sys.stderr)
        return 2
    try:
        res = do_fit(fit["func"], fit["params"], fx, fy, ferr)
    except (ValueError, RuntimeError) as e:
        print(f"error: fit failed: {e}", file=sys.stderr)
        return 2
    print(f"fit function: {fit['funcname']}")
    for k in res["best"]:
        pe = res["perr"].get(k)
        tag = "fixed" if k in res["fixed"] and k not in res["free_names"] else "fit"
        print(f"  {k} = {res['best'][k]:.6g} +/- "
              f"{pe if pe is not None else '-'} [{tag}]")
    print(f"chisq = {res['chisq']:.6g} dof = {res['dof']} "
          f"reduced = {res['redchisq']:.6g}")
    # model curve + plot
    mx = np.linspace(float(np.min(fx)), float(np.max(fx)), 200)
    kw = res["best"]
    try:
        my = fit["func"](mx, **kw)
    except (ValueError, OverflowError) as e:
        print(f"error: model eval failed: {e}", file=sys.stderr)
        return 2
    if args.plot:
        try:
            make_plot(args, x, y, err, xb, yb, eb, mx, my)
        except ValueError as e:
            print(f"error: {e}", file=sys.stderr)
            return 2
        print(f"plot saved: {args.plot}")
    # param file
    if fit["param_file"]:
        d = os.path.dirname(os.path.abspath(fit["param_file"]))
        if d:
            os.makedirs(d, exist_ok=True)
        with open(fit["param_file"], "w") as f:
            f.write(f"# fitfunction {fit['funcname']}\n")
            f.write(f"# input {args.csvfile}\n")
            for k in res["best"]:
                pe = res["perr"].get(k, float("nan"))
                f.write(f"{k} = {res['best'][k]!r} +/- {pe!r}\n")
            f.write(f"chisq = {res['chisq']!r}\n")
            f.write(f"dof = {res['dof']}\n")
            f.write(f"reduced_chisq = {res['redchisq']!r}\n")
        print(f"params saved: {fit['param_file']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
