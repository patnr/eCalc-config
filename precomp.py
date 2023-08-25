"""
- Preprocess the simulator output to form some new time series
- Run eCalc
- Extract emission results

The difficult part is knowing how to do the configuration, both for the master file
(typically "model.yaml", with all-caps keywords in it)
and the various constituent relation files ("*.csv").
While mainly sourced from the examples in the [docs](https://equinor.github.io/ecalc/docs/about/modelling/examples/)
Actually, I cannot guarantee that the absolute numbers make sense,
or that all factors that impact emissions are logically configured, or even taken into account.

Fortunately, for our purposes, the aboslute numbers are only of secondary importance.
However, before trying to optimise anything,
it is important to check that indeed the emissions exhibit sensitivity
to the control parameters that you wish to optimise for
Do so by changing the numbers in the `reek-prod.csv` -- you don't
have to do this in your editor: see how easy it is to work with `df` hereunder.


Possibilities to consider:

- Gas lift
- Gas injection
- Different pump setup (no common manifold)?
"""

from matplotlib import Path
import pandas as pd

# pd.set_option('display.max_rows', 1000)

## Preprocess
# Read
HERE = Path(__file__).parent.resolve()
df = pd.read_csv(HERE / 'from_geir.csv', index_col='dd/mm/yyyy', date_format='%d/%m/%Y')

# Invent injection pressure since didn't get from Geir
# TODO: instead: use max of injector WBHP (following Angga) once available
df['WBHP:INJ'] = df.filter(like='WBHP:OP').mean(1)

# Filter, reorder
df = df.reindex(columns=['FOPR', 'FGPR', 'FWPR', 'FWIR', 'FGIR', 'WBHP:INJ'])

# Compute reinjection of produced water
x = df['FWPR']
# which cannot be more than total injection
x = x.clip(upper=df['FWIR'])
# and should not happend when uneconomical (pump inefficient for small flow)
x[x < 1500] = 0
# Sea water does the remainder
df['SEA_INJ'] = df['FWIR'] - x
df['WATER_REINJ'] = x
# TODO: right now the pumps don't distinguish which water type is injected
#       See "simple model" case for example on doing so.

def hydrostatic_column(depth, density=1010):
    """Pressure difference (bara) through `depth` to completion (m), `density` (kg/m^3)."""
    gravity     = 9.81  # m/s^2
    pa_per_bar  = 10**5
    hydrostatic = density * gravity * depth / pa_per_bar
    return hydrostatic

# Compute discharge pressure for injection pumps from their BHP
df['INJ-HEADP'] = df['WBHP:INJ'] - hydrostatic_column(300)

# Rename some columns (to conform somewhat with Drogon model.yaml)
aliases = {
    'FGPR':'GAS_PROD',
    'FOPR':'OIL_PROD',
    'FWIR':'WATER_INJ',
}
for old, new in aliases.items():
    df[new] = df[old]
    del df[old]

# Write
df.to_csv(HERE / 'reek-prod.csv', index=True)
