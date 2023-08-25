from pathlib import Path

from libecalc.core.ecalc import EnergyCalculator
from libecalc.common.time_utils import Frequency
from libecalc.input.model import YamlModel

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


def extract(results, getter):
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
    df.attrs = attrs
    return df


def span(ds):
    """Get (min, max) span."""
    a, b = ds.min(), ds.max()
    scale = (b - a)
    offset = a
    if scale < 1e-99:
        scale = 10 ** np.ceil(np.log10(offset))
        offset = 0.
    return scale, offset


def plot_results(results, title, colors={}):
    """Plot columns of `results` (DataFrame), using individual offset/scaling for visibility."""
    fig = plt.figure(num=title, figsize=(10, 5)); fig.clear()
    fig, ax = plt.subplots(num=title)
    fig.suptitle(title)
    markers = ['^', 'P', '+', 'v', '.', 'x', 'o', 's', 'H', 'X', 'd']

    nCols = results.shape[1]
    for (component, data), m in zip(results.items(), markers):
        attrs = results.attrs[component]
        unit = f"{attrs['unit']}"
        if nCols > 1:
            scale, offset = span(data)
            data = (data - offset) / scale
            if offset:
                unit = f"({unit} - {offset:.3})"
            unit += f"/{scale:.3}"
        lbl = "\n".join([component, f"<{attrs['kind']}>", unit])
        data.plot(ax=ax, lw=2, marker=m, color=colors.get(component, None), label=lbl, xlabel="time")

    ax.legend(bbox_to_anchor=(1.04, 1), loc="upper left", labelspacing=1.)
    ax.grid(axis="both", which="both")
    fig.tight_layout()
    return fig


# def main():
if __name__ == "__main__":
    try:
        HERE = Path(__file__).parent
    except NameError:
        # Fallback (attempt) for notebooks
        HERE = Path().cwd()

    ## Config
    # model_path = HERE / "drogn.yaml"
    model_path = HERE / "reek-model.yaml"
    yaml_model = YamlModel(path=model_path, output_frequency=Frequency.NONE)
    comps = {c.name: id_hash for (id_hash, c) in yaml_model.graph.components.items()}
    model = EnergyCalculator(graph=yaml_model.graph)

    ## Compute energy, emissions
    consumer_results = model.evaluate_energy_usage(yaml_model.variables)
    emission_results = model.evaluate_emissions(yaml_model.variables, consumer_results)

    ## Extract
    energy    = extract(consumer_results, lambda r: r.component_result.energy_usage)
    emissions = extract(emission_results, lambda r: r['co2_fuel_gas'].rate)

    ## Plot
    plt.ion()
    colors = {comp: f"C{i}" for i, comp in enumerate(set(energy) | set(emissions))}
    fig1 = plot_results(energy, "Energy usage", colors)
    fig2 = plot_results(emissions, "Emissions", colors)
