# TASK

## Objective
Build a CLI Python tool (using `astropy` where relevant) that performs chi-square fitting of tabular CSV data to arbitrary user-supplied functions, with optional data binning, y-error handling, x/range limits, axis scaling, plot-only preview, and plot/file outputs.

## Refined Prompt
Create a command-line program with `argparse` (parser built in a separate function) that:

1. Reads a multi-column CSV file where line 1 is column names/descriptions and line 2 is units.
2. Selects x, y, and y-error columns by user input; defaults to first three columns if not given; if x and y given but no error column, use std(y) as uniform error for all y; if no error information at all, assume error = 1 for all points.
3. Supports data limits in x and separate plot limits in x (lower + upper via same CLI syntax).
4. Supports `--plot-only` to preview data without fitting.
5. Supports axis-type selection for combinations of log / lin / exp (e.g. log-exp) — presumed x-y axis scaling.
6. Supports optional binning via `--with-bin {uniform,std,mad}` + `--with-bin-per <pct, default 10>`:
   - `uniform`: same number of data points per bin.
   - `std`: bin boundaries chosen to keep std per bin uniform within given %.
   - `mad`: same using MAD within given %.
7. Supports `--plot <plot-filename>` for output plot.
8. Supports `--fit <custom_fits_file.py>` where the custom file defines:
   - `fitfunction = "<function_name>"` selecting one of multiple fit functions defined in the same file,
   - fit range (same syntax as x limits / plot limits),
   - parameters with initial values, fit/fixed flag, and bounds, e.g. `A:<init_val>:T:(low, high)`, `T`=fit, `F`=fixed at init value, `-` = skip entry,
   - `fit_parameter_filename` (with path) for parameter output.
9. Performs chi-square fitting to the selected function with or without binning and with or without y-errors.

## Requirements
- R1: CLI with `argparse`, parser construction isolated in a separate function.
- R2: CSV reader handling two header rows (names + units), arbitrary multi-column data.
- R3: Column selection: `--x-col`, `--y-col`, `--err-col` (names or indices — to be fixed in PLAN); default first three columns; fallback errors: std(y) if x,y given but no err; 1.0 if no error info.
- R4: X data limits (`--x-limits` or equivalent) and separate plot X limits (`--plot-x-limits` or equivalent), each accepting lower,upper in one CLI option.
- R5: `--plot-only` flag: show/save data plot, skip fitting.
- R6: Axis-type option (e.g. `--axis-type log-exp`): support all combinations of log/lin/exp for x/y.
- R7: Binning: `--with-bin {uniform,std,mad}` + `--with-bin-per <float, default 10>` (% tolerance for std/mad uniformity).
- R8: `--plot <filename>`: save fit/data plot to given file.
- R9: `--fit <file.py>`: load custom fit definition file per format above (fitfunction choice, fit range, parameter specs, fit_parameter_filename, multiple function defs).
- R10: Chi-square fitter (astropy-based, e.g. `astropy.modeling` / units-aware where sensible) working with/without binning and with/without y-errors.
- R11: Parameter output file written to `fit_parameter_filename` path given in custom fit file.
- R12: Sensible exit codes / error messages for missing file, bad columns, bad fit file, empty selection after limits.

## Inputs
- Multi-column CSV: row1 = column names, row2 = units, rest = data.
- CLI args: input CSV path, x/y/err column selectors, x-limits, plot-x-limits, axis-type, with-bin mode + per, plot filename, fit file, plot-only flag.
- Custom fit `.py` file: `fitfunction` string, fit-range spec, parameter lines (`NAME:<init>:<T|F|->:<(low,high)|->`), `fit_parameter_filename`, one or more Python fit function definitions.

## Expected Outputs
- Main executable + modules in `src/scripts/`.
- Console fit results (chi-square, best-fit params) — exact format to be fixed in PLAN.
- Plot file at `--plot` path when requested.
- Parameter file at `fit_parameter_filename` path specified in custom fit file.
- `devl/tmp/REPORT.md` after PLAN execution (with test evidence).

## Constraints
- Python with `astropy`; `argparse` parser as separate function.
- Follow project layout: code → `src/scripts/`, JSON config (if any) → `src/json/`, test plots → `devl/testdir/plots/`, temp artifacts → `devl/tmp/`.
- Do not modify originals in `devl/testdir/data/`.
- Custom-fit file format must match PROMPT spec exactly (including `-` skip and `T/F` semantics).
- No destructive actions, no new heavy dependencies without approval.

## Execution Rules
- Implement minimal, testable CLI first, then binning, then custom-fit loading, then fitting.
- Use user-supplied validation data from `devl/testdir/data/` when available; otherwise minimal synthetic CSV matching the two-header format, clearly marked synthetic.
- Validate each CLI option and each binning mode separately.

## Validation
- Parse sample two-header CSV, check column defaults and explicit selection.
- Test fallbacks: no err-col → std(y); no error info → 1.0.
- Test x-limits vs plot-x-limits separation.
- Test `--plot-only` produces plot without fit.
- Test each `--with-bin` mode + default/custom `--with-bin-per`.
- Test axis-type combinations accepted.
- Test `--fit` with multi-function file: correct `fitfunction` selected, T/F/- honored, parameter file written.
- Run tool end-to-end on test CSV; verify exit code 0, plot file exists, parameter file exists, chi-square finite.

## Completion Criteria
- All R1–R12 implemented and manually tested via CLI.
- `REPORT.md` records commands, test data used, outputs, and any deviations.
- Code placed per project layout and runnable from `devl/testdir/`.

## Questions / Ambiguities
- Q1: "optioations in image" — assumed "operations"; does astropy usage require image (FITS) handling, or only table/units/modeling for 1D fitting? Assumed latter.
- Q2: Exact CLI names/syntax for limits, columns, axis-type, plot, fit not specified — PLAN will propose concrete names (user approval implicit in PLAN).
- Q3: "if x and y are given std in y is taken as err" — interpreted as uniform error = std(y); confirm.
- Q4: "same syntax as limits in x and y for plotting" for fit range — assumed `lower,upper`; confirm whether y-range also fittable.
- Q5: Axis-type `exp` — unusual for matplotlib; confirm meaning (exp scaling vs linear-in-exp?) and whether it applies as x-y pair like `log-lin`.
- Q6: Binning `std`/`mad` "keep same to 10%" — interpreted as adaptive binning with uniformity tolerance; exact algorithm to be fixed in PLAN.
- Q7: `fit_parameter_filename with path will be given in this also` — assumed variable inside custom fit file; confirm variable name.
- Q8: Column selectors: names vs 0/1-based indices? Assumed support both; to fix in PLAN.
- Q9: Units row: must it propagate via astropy.units or informational only? Assumed informational unless trivial.
