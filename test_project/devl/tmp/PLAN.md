# EXECUTION PLAN

## Objective
Implement the TASK: astropy-assisted chi-square CLI fitter per R1–R12, runnable from `src/scripts/`, validated on `devl/testdir/data/B4_fixed.csv` (plus synthetic two-header CSVs for full-spec coverage).

## Inputs
- Approved: `devl/tmp/TASK.md`, original `devl/tmp/PROMPT.md`.
- Test data: `devl/testdir/data/B4_fixed.csv` — observed: 8001 rows, 1 header row `Time(ns),Counts`, 2 columns, numeric from row 2 (NOT the 2-header names+units format in spec). Must support both 1-header and 2-header files.
- Env (verified): astropy 7.1.1, matplotlib 3.10.6, numpy 2.3.5, scipy (to verify at execution; install only if missing and minor).

## Files to Inspect
- `devl/tmp/TASK.md` (authoritative WHAT) + `devl/tmp/PROMPT.md` (original wording).
- `devl/testdir/data/B4_fixed.csv` head/sample only (already sampled; do not load fully until execution).
- `src/scripts/` (empty — target location).
- During execution only: `python --help`-equivalents for `scipy.optimize.curve_fit`, `astropy.table.QTable`, `astropy.stats.mad_std` as needed.

## Execution Steps
1. Verify `scipy` availability (`python3 -c "import scipy"`); if missing, note as dependency decision (minor, allowed).
2. Create `src/scripts/chisq_fit.py` (single executable, `#!/usr/bin/env python3`):
   - `build_parser()` — separate function returning `argparse.ArgumentParser`. Concrete CLI:
     - positional `csvfile`
     - `--x-col`, `--y-col`, `--err-col`: column name OR 0-based index string; defaults 0,1,2 (2 only if present).
     - `--x-limits "lo,hi"`: data selection cut (either bound may be empty, e.g. `"500,"`).
     - `--plot-x-limits "lo,hi"`, `--plot-y-limits "lo,hi"`: view limits only.
     - `--axis-type "<x>-<y>"`, each in `{lin,log,exp}` (default `lin-lin`); mapping: lin→linear, log→log, exp→symlog (documented approximation for Q5).
     - `--with-bin {uniform,std,mad}`, `--with-bin-per FLOAT default 10.0`, `--n-bins INT default 20` (needed for `uniform`; DECISION — PROMPT omits bin count).
     - `--plot FILENAME`, `--plot-only` (store_true), `--fit FITFILE.py`.
   - `parse_limit(s)`: `"lo,hi"` → `(float|None, float|None)`.
   - `load_csv(path, x_sel, y_sel, e_sel)`: read with `csv` module; detect units row: if row-2 parses fully numeric → no units row; else treat row-2 as units (informational; try `astropy.units`, fall back to plain strings — Q9). Return x,y,err_raw, colnames, units, err_mode flag.
   - Error resolution (R3): if `--err-col` given → use it; elif `--y-col` explicitly given and no err → uniform `std(y)`; elif default 3rd column exists → use it; else ones. Record which path in verbose output.
   - `apply_x_limits()`, binning:
     - sort by x first.
     - `uniform`: `array_split` into `--n-bins` equal-count bins; bin x=mean, y=mean, err=sqrt(sum(err^2))/n.
     - `std`/`mad`: greedy adaptive — accumulate sorted points (min 3/bin), extend bin until bin dispersion (std or `mad_std`) is within `--with-bin-per` % of running target (global std/mad of full selection); cap bins at `--n-bins*4` to avoid runaway; document as approximation for Q6.
   - Custom-fit loader `load_fitfile(path)`: exec file in isolated namespace; require `fitfunction` (str), lookup callable in same namespace; optional `fit_range` (str `"lo,hi"` or 2-tuple) applied as extra cut; optional `fit_parameter_filename`; params: any UPPER/any-case variable whose value is string `"init:T:(lo,hi)"` / `"init:F:-"` / `"-"`-tolerant form, OR tuple `(init, bool|T/F, (lo,hi)|None)`; `T`=free, `F`=fixed, `-`=skip field. Collect p0, bounds, fixed map.
   - Fitter: `scipy.optimize.curve_fit(f, x, y, sigma=err, absolute_sigma=True, p0, bounds)`; on `ValueError` (e.g. log-scale non-positive) report cleanly. Compute `chisq=sum(((y-model)/err)**2)`, `dof=n-nfree`, reduced chisq. Use `astropy` for table (`QTable` for I/O echo) and `mad_std` in binning (satisfies astropy-use constraint).
   - Plot: matplotlib (Agg backend when `--plot` given): data with yerr, binned points if binned, model curve (200 pts across fit/view range); apply axis scales + plot limits; save to `--plot` or `devl/testdir/plots/` default name when `--plot-only` without filename? No — require `--plot` for file; else show.
   - Param output: write text file to `fit_parameter_filename` (if defined): fitfunction, params, errors (from pcov diag), chisq/dof/reduced, fit_range, input file, version. Create parent dirs.
   - `main()`: wire everything, exit codes 0 ok / 2 usage-data errors.
3. Create `src/scripts/example_gauss_fit.py`: sample custom-fit file with two functions (`gauss`, `line`), `fitfunction="gauss"`, `fit_range`, params in spec string format, `fit_parameter_filename` pointing under `devl/tmp/`.
4. Create synthetic two-header test CSV in `devl/tmp/synth_twoheader.csv` (names + units + x,y,err columns) for full-spec coverage (B4 file lacks units row + err col).
5. Test sequence (from `devl/testdir/`, originals untouched, outputs to `devl/tmp/` or `devl/testdir/plots/`):
   - T1 `--help`; T2 default cols on B4; T3 explicit cols + std-fallback; T4 `--x-limits` vs `--plot-x-limits`; T5 `--plot-only --plot`; T6 `--axis-type log-lin`; T7 `--with-bin uniform --n-bins 20 --plot`; T8 `--with-bin std/mad`; T9 `--fit example` end-to-end (check param file + chisq finite); T10 synthetic two-header + err-col; T11 error paths (bad col, bad fit file).
6. Write `devl/tmp/REPORT.md` in required COMPLETION REPORT format + test-data appendix.

## Files Expected to be Created
- `src/scripts/chisq_fit.py` (new, main deliverable)
- `src/scripts/example_gauss_fit.py` (new, sample fit definition)
- `devl/tmp/synth_twoheader.csv` (new, synthetic test input, clearly marked)
- `devl/tmp/REPORT.md` (new)
- Test outputs: `devl/tmp/test_*.png`, `devl/tmp/test_params_*.txt`, `devl/testdir/plots/` preview(s)

## Files Expected to be Modified
- None existing (all targets are new). `devl/tmp/TASK.md` and `PROMPT.md` untouched.

## Validation / Testing
- Each T1–T11 must exit as expected; T5/T7/T9 must produce existing non-empty plot files; T9/T10 must produce param file with finite chisq.
- Distinguish software failure vs unsuitable data: B4 file (single-header, 2-col, many zeros) is valid for plumbing/binning/plot tests but a poor physics fit — a large chisq on B4 is data-expected, not a code fail; synthetic Gaussian data proves fitter correctness.
- If `devl/testdir/data/` gains a true two-header file later, rerun T10 against it.
- Record exact commands + results in REPORT; mark COMPLETED only if T1–T10 pass (T11 error-paths must fail cleanly, not crash).

## Expected Deliverables
- Working `chisq_fit.py` meeting R1–R12 per decisions below.
- Sample fit file + synthetic CSV + plots + param files as evidence.
- `REPORT.md` with status COMPLETED / PARTIALLY COMPLETED / FAILED.

## Risks / Decisions
- D1 (`--n-bins`): PROMPT omits bin count for `uniform` → add `--n-bins default 20` (minor, no re-approval needed).
- D2 (`exp` axis): map to `symlog`; note in help + REPORT (resolves Q5 approximately).
- D3 (units row): auto-detect 1- vs 2-header; units informational only (resolves Q9, mismatch with B4 file).
- D4 (column selectors): accept name or 0-based index (resolves Q8).
- D5 (std/mad binning): greedy tolerance algorithm = approximation of underspecified spec (Q6); recorded as deviation-tolerant.
- D6 (param spec): accept both `"init:T:(lo,hi)"` strings and tuples; `-` skips that field (resolves spec format).
- D7 (fit_range): `"lo,hi"` string or tuple, x-only unless file defines y keys (resolves Q4).
- Risk: B4 data (zeros-heavy, no errors) may give huge/degenerate chisq — mitigate with synthetic data + subset (first 2000 rows) for speed.
- No heavy new deps beyond scipy/matplotlib (already present); no arch/scope change.

## Completion Check
- R1–R12 traceable to code paths; T1–T11 evidence in REPORT; `chisq_fit.py` executable from `devl/testdir/`; no originals modified; deviations from this PLAN listed in REPORT.
