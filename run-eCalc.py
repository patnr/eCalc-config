#!path/to/virtualenv/for/eCalc/with/binary/of/python  -- no activation required
"""Compute emissions for Reek/Drogon based on production time series."""

from pathlib import Path
import sys

import pandas as pd

from libecalc.core.ecalc import EnergyCalculator
from libecalc.common.time_utils import Frequency
from libecalc.input.model import YamlModel


def plot_results(results, title, colors={}):
    """Plot columns of `results` (DataFrame), using individual offset/scaling for visibility."""
    fig = plt.figure(num=title, figsize=(10, 5)); fig.clear()
    fig, ax = plt.subplots(num=title)
    fig.suptitle(title)
    markers = ['^', 'P', '+', 'v', '.', 'x', 'o', 's', 'H', 'X', 'd']

    nCols = results.shape[1]
    for i, ((component, data), m) in enumerate(zip(results.items(), markers)):
        ls = "--" if "main_power" in component else "-"
        if "main_power" in component:
            continue

        attrs = results.attrs[component]
        unit = f"{attrs['unit']}"

        if nCols > 1:
            # scale = 1/data.max()
            scale = 1.
            # scale *= (10 + i/len(results))  # for visual distinction
            yy = scale * data
            unit = f"{scale:.3} {unit}"

        lbl = "\n".join([component, f"<{attrs['kind']}>", unit])
        yy.plot(ax=ax, lw=2, ls=ls, marker=m, color=colors.get(component, None), label=lbl, xlabel="time")

    ax.legend(bbox_to_anchor=(1.04, 1), loc="upper left", labelspacing=1.)
    ax.grid(axis="both", which="both")
    ax.set_ylim(0)
    fig.tight_layout()
    return fig

# pd.set_option('display.max_rows', 1000)

try:
    HERE = Path(__file__).parent
except NameError:
    HERE = Path().cwd()  # fallback for ipynb's
HERE = HERE.resolve()


def preprocess_prod(infile, outfile):
    """Manipulate time series in `infile`. Write to `outfile`.

    This approach (pandas) is much more reliable than eCalc's yaml arithmetics syntax.
    """

    df = pd.read_csv(HERE / infile, index_col='dd/mm/yyyy', date_format='%d/%m/%Y')

    # Invent injection pressure since didn't get from Geir
    # TODO: instead: use max of injector WBHP (following Angga) once available
    df['WBHP:INJ'] = df.filter(like='WBHP:OP').mean(1)

    # Filter, reorder
    df = df.reindex(columns=['FOPR', 'FGPR', 'FWPR', 'FWIR', 'FGIR', 'WBHP:INJ'])

    # Compute reinjection of produced water (could be that different pump is used for sea water)
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
    df.to_csv(HERE / outfile, index=True)
    return df


def results_as_df(yaml_model, results, getter) -> pd.DataFrame:
    """Extract relevant values, as well as some meta (`attrs`)."""
    df = {}
    attrs = {}
    for id_hash in results:
        res = results[id_hash]
        res = getter(res)
        component = yaml_model.graph.components[id_hash]
        df[component.name] = res.values
        attrs[component.name] = {'id_hash': id_hash,
                                 'kind': type(component).__name__,
                                 'unit': res.unit}
    df = pd.DataFrame(df, index=res.timesteps)
    df.index.name = "dates"
    df.attrs = attrs
    return df


if __name__ == "__main__":
    ## Run
    # prod_df = preprocess_prod('from_geir.csv', 'reek-prod.csv')

    # Config
    model_path = HERE / "eConf" / "drogn.yaml"  # "drogn.yaml"
    yaml_model = YamlModel(path=model_path, output_frequency=Frequency.NONE)
    # comps = {c.name: id_hash for (id_hash, c) in yaml_model.graph.components.items()}

    # Compute energy, emissions
    model = EnergyCalculator(graph=yaml_model.graph)
    consumer_results = model.evaluate_energy_usage(yaml_model.variables)
    emission_results = model.evaluate_emissions(yaml_model.variables, consumer_results)

    # Extract
    energy    = results_as_df(yaml_model, consumer_results, lambda r: r.component_result.energy_usage)
    emissions = results_as_df(yaml_model, emission_results, lambda r: r['co2_fuel_gas'].rate)

    emissions_total = emissions.sum(1).rename("emissions_total")
    emissions_total.to_csv(HERE / "emissions.csv")


    ## Plot
    # if "plot" in sys.argv:
    if True:
        import matplotlib.pyplot as plt
        plt.ion()

        colors = {'main_power': 'C0',
                  'baseload': 'C1',
                  'boosterpump': 'C2',
                  'compressor_train': 'C3',
                  'wi_lp': 'C4',
                  're-compressors': 'C6'}
        fig1 = plot_results(energy, "Energy usage", colors)
        fig2 = plot_results(emissions, "Emissions", colors)
        plt.pause(3)
