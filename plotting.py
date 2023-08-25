"""Plotting tools."""

import matplotlib.pyplot as plt
import numpy as np


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


