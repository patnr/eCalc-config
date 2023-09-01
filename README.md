# Compute emissions for Reek/Drogon based on production time series

![Screenshot](screenshot.png)

- Prerequisite: install **eCalc**.
- Use: run `run-eCalc.py`. Read output from `emissions_total.csv`.

## What does `run-eCalc.py` do?

- Pre-process the simulator output (production data)
- Runs eCalc
- Extract emission results
- Write results
- Plot (optionally)

## About

The difficult part is knowing how to do the configuration in

- `"some-model.yaml"`, which contains all-caps keywords
- the various constitutive relation files (`*.csv`).

The configuration herein is mainly sourced from the examples in the [eCalc docs](https://equinor.github.io/ecalc/docs/about/modelling/examples/).
But I cannot guarantee that the absolute numbers make sense,
or that all factors that impact emissions are logically configured, or even taken into account.

Fortunately, for our purposes, the absolute numbers are only of secondary importance.
What is important, before trying to optimise anything,
it to check that indeed the emissions exhibit sensitivity
to the control parameters that you wish to optimise for.
You should perform this check
by manipulating `df` in `run-eCalc.py:preprocess_prod()` or the raw `.csv` time series,
to reflect the relevant parameters, and then run this script with "plot" as an argument.

### Suggestions for further possibilities to consider

- Gas lift
- Different pump setup (no common manifold)

## How to use in ERT and other ensemble task managers

Before `run-eCalc.py`, ERT must write the relevant input variables:

- Copy this dir into the member dir
- Overwrite whatever `infile` points to
  (currently `"from_geir.csv"`) with ECLIPSE or OPM output.
- Overwrite whatever else gets specified from the ensemble member (state/param.\ vector).
  For ideas, see `model_path` (currently `"reek-model.yaml"`).
