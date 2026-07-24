from plotly.subplots import make_subplots
import plotly.graph_objects as go
import plotly.express as px

import pandas as pd
import numpy as np

from typing import Tuple, List

import os


class _MotifSumPlotter:
    def __init__(
            self,
            font_family:str = "Courier",
            title_size:int = 22,
            subplot_title_size:int=14,
            axis_title_size:int = 14,
            axis_tick_size:int = 12,
            legend_size:int = 12,
            nrows:int = 2,
            ncols:int = 3
        ) -> None:

        def _gen_row_col(nstates, nrows, ncols):
            return zip(
                [i // ncols + 1 for i in range(nstates)],
                sum([[i+1 for i in range(ncols)] for j in range(nrows)], [])
            )

        self._col_order = [
            "AlphaHelix", "Strand", "Coil", "310Helix", "Bridge", "Turn"
        ]
        # NOT VERY DRY OF YOU HERE SON
        # PLOT VARIABLES
        self.font_family = font_family

        self.title_size = title_size

        self.subplot_title_size = subplot_title_size

        self.axis_title_size = axis_title_size
        self.axis_tick_size = axis_tick_size

        self.legend_size = legend_size

        # PLOT DICTS
        self.title_font = dict(family=self.font_family, size=self.title_size)

        self.subtitle_font = dict(family=self.font_family, size=self.subplot_title_size)

        self.legend_font = dict(family=self.font_family, size=self.legend_size)

        self.axis_title_font = dict(family=self.font_family, size=self.axis_title_size)
        self.axis_tick_font = dict(family=self.font_family, size=self.axis_tick_size)

        # ROW COLS BECAUSE I CAN'T THINK OF A CLEVER WAY TO DO THIS
        self.row_cols = {
            motif:order for motif, order
            in zip(self._col_order, _gen_row_col(len(self._col_order),nrows,ncols))
        }


class MotifSumPlotter(_MotifSumPlotter):
    def __init__(self, X:pd.DataFrame):

        def _init_data(X:pd.DataFrame, col_order:List[str]) -> Tuple[pd.DataFrame, pd.DataFrame]:

            grouped_data = X.groupby(level="motif")

            mean, error = grouped_data.mean(), grouped_data.std()

            mean, error = mean.loc[:,col_order], error.loc[:,col_order]

            return mean, error

        def _get_motif_len(mean:pd.Series) -> int:
            return len(mean.index.get_level_values("motif")[0].split("_"))

        def assign_colors(motifs:pd.Series) -> dict:
            palette = px.colors.qualitative.Plotly
            return {
                motif:palette[i % len(palette)] for i,motif in enumerate(motifs)
            }

        super().__init__()

        self.mean, self.error = _init_data(X, self._col_order)

        self._motif_len = _get_motif_len(self.mean)
        self.motif_colors = assign_colors(
            self.mean.index.get_level_values("motif")
        )

    def plot_single(self, sec_struc_label:str, n_keep:int) -> None:

        self.fig = go.Figure()

        data = self.mean.sort_values(by=sec_struc_label, ascending=False)
        data = data.iloc[:n_keep]

        error = self.error.loc[data.index, :]

        x = data.index.get_level_values("motif")
        y = data.loc[:, sec_struc_label]

        error_high = error.loc[:, sec_struc_label]
        error_low = np.where(
            y - error_high < 0,
            y, error_high
        )

        bar = go.Bar(
            x = x,
            y = y,
            error_y=dict(
                type="data",
                symmetric=False,
                array=error_high,
                arrayminus=error_low
            )
        )
        self.fig.add_trace(trace=bar)

        # UPDATE PLOT TITLE
        self.fig.update_layout(
            title = dict(
                text=sec_struc_label,
                font=self.title_font
            ),
            xaxis_title="Motif",
            yaxis_title="Mean Count (+/- std dev)"
        )

        # UPDATE AXES FONT
        self.fig.update_yaxes(
            title_font=self.axis_title_font,
            tickfont=self.axis_tick_font,
        )

        self.fig.update_xaxes(
            title_font=self.axis_title_font,
            tickfont=self.axis_tick_font,
        )

if __name__ == "__main__":
    sec_elements = [
        "AlphaHelix",
        "Strand",
        "Coil",
        "310Helix",
        "Bridge",
        "Turn"
    ]
    for i in range(3, 16, 3):
        
        root = f"motiflen_{i}"
        pdir = os.path.join("data")
        data_filename = f"{root}.parquet"
        data_filepath = os.path.join(pdir, data_filename)
        write_dir = os.path.join("plots", root)


        data = pd.read_parquet(data_filepath).astype("int64").drop(["PiHelix"], axis=1)

        plotter = MotifSumPlotter(data)

        os.makedirs(os.path.join(write_dir), exist_ok=True)

        for sec_element in sec_elements:
            root_element = f"{root}_{sec_element}"
            writepath = os.path.join(write_dir, f"{root_element}.json")
            plotter.plot_single(sec_element, n_keep=15)  
            plotter.fig.write_json(writepath)
