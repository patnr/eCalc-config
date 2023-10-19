# Compute emissions for Reek/Drogon based on production time series

![Screenshot](screenshot.png)

*NB*: this is very much work in process, subject to major changes.

## What does `run-eCalc.py` do?

- Pre-process the simulator output (production data)
- Runs eCalc
- Extract emission results
- Write results
- Plot (optionally)

Except for the pre-processing,
these steps can all be found (in some shape or form)
among the example scripts distributed with eCalc.

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
to reflect the relevant parameters, and then do `./run-eCalc.py plot`.

### Suggestions for further possibilities to consider

- Gas lift
- Different pump setup (no common manifold)

## Usage with ERT, PET, and other ensemble task managers

Prerequisites

- Install **eCalc** (in its own virtual env)
- Fix the shebang in `run-eCalc.py` and run it with argument "plot".  
  Alternatively, active the virtual env and do `python run-eCalc.py plot`.
- Change `model_path` in `run-eCalc.py`.
  Examples: `reek-model.yaml`, `drogn.yaml`.
- If this is
    - Drogon: disable/delete line `prod_df = preprocess_prod(...)`.
    - Reek, or some other field, adapt the preprocessing to suit your needs.
      As you can see from the current implementation, the pre-processing
      does some simple arithmetics to compute some new time series
      (aka. "production data") and rename some of the columns.

ERT/PET will need to

- Copy contents of this dir into the member dir
- Write the eCalc input variables from the ensemble member.
    - ECLIPSE/OPM output in `infile`.
    - Other relevant parameters in `model_path`.
- Run `run-eCalc.py`.
- Read output from `emissions.csv`.
