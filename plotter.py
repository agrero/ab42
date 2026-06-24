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

    def plot2(self, ncols:int=3, nrows:int=2, n_keep:int=10, sec_struc_sort:str="AlphaHelix") -> None:
        
        self.fig = make_subplots(
            rows=nrows, cols=ncols,
            subplot_titles=self._col_order,
            vertical_spacing=0.2,
            showlegend=False
        )

        self.fig.update_annotations(
            font=self.subtitle_font
        )

        data = self.mean.sort_values(by=sec_struc_sort, ascending=False)
        if n_keep > data.shape[0]: n_keep = data.shape[0]

        data = data.iloc[:n_keep]
        error = self.error.loc[data.index, :]

        for sec_struc_label in self._col_order:
            x = data.index.get_level_values("motif")
            y = data.loc[:,sec_struc_label]
            error_high = error.loc[:,sec_struc_label]
            error_low = np.where(
                y - error_high < 0,
                y, error_high
            )
  
            bar = go.Bar(
                x = x,
                y = y,
                name=sec_struc_label,
                error_y=dict(
                    type="data",
                    symmetric=False,
                    array=error_high,
                    arrayminus=error_low
                )
            )

            self.fig.add_trace(
                trace=bar,
                row=self.row_cols[sec_struc_label][0],
                col=self.row_cols[sec_struc_label][1]
            )
 
        # UPDATE PLOT TITLE
        self.fig.update_layout(
            title = dict(
                text=f"Motif Length: {self._motif_len * 3}",
                font=self.title_font
            )
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

        # ADD AXES LABELS TO INITIAL PLOT

        self.fig.update_yaxes(
            title_text="Counts",
            row=2,col=1
        )

        self.fig.update_xaxes(
            title_text="Motif",
            row=2, col=1
        )


    def plot(self, ncols:int=3, nrows:int=2, n_keep:int=20) -> None:

        self.fig = make_subplots(
            rows=nrows, cols=ncols,
            subplot_titles=self._col_order,
            vertical_spacing=0.15
        )

        self.fig.update_annotations(
            font=self.subtitle_font
        )

        for sec_struc_label in self._col_order:

            data = self.mean.loc[:,[sec_struc_label]]
            data = data.sort_values(by=sec_struc_label, ascending=False)

            error = self.error.loc[data.index, sec_struc_label]
            error_low = np.where(
                data[sec_struc_label]-error < 0, data[sec_struc_label], error
            )

            if n_keep > data.shape[0]: n_keep = data.shape[0]
            data = data.iloc[:n_keep]

            for ndx, motif in enumerate(data.index.get_level_values("motif")):

                bar = go.Bar(
                    x=[ndx],
                    y=data.loc[motif,[sec_struc_label]],
                    legendgroup=motif,
                    legendgrouptitle_text=motif,
                    name=sec_struc_label,
                    error_y=dict(
                        type="data",
                        symmetric=False,
                        array=self.error.loc[motif, [sec_struc_label]],
                        arrayminus=error_low[[ndx]]
                    ),
                    marker_color=self.motif_colors[motif],
                    hovertemplate=f"<b>Motif:</b> {motif}<br><extra></extra>"
                )

                self.fig.add_trace(
                    trace=bar,
                    row=self.row_cols[sec_struc_label][0],
                    col=self.row_cols[sec_struc_label][1]
                )

        self.fig.update_layout(legend=dict(groupclick="toggleitem"))


        # UPDATE PLOT TITLE
        self.fig.update_layout(
            title = dict(
                text=f"Motif Length: {self._motif_len * 3}",
                font=self.title_font
            ),
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

        # ADD AXES LABELS TO INITIAL PLOT

        self.fig.update_yaxes(
            title_text="Counts",
            row=2,col=1
        )

        self.fig.update_xaxes(
            title_text="Motif",
            row=2, col=1
        )

if __name__ == "__main__":

    root = "motiflen_3"
    pdir = os.path.join("data")
    filename = f"{root}.parquet"
    filepath = os.path.join(pdir, filename)

    writepath = os.path.join("plots", f"{root}_v2.json")

    data = pd.read_parquet(filepath).astype("int64").drop(["PiHelix"], axis=1)

    plotter = MotifSumPlotter(data)

    plotter.plot2()

    plotter.fig.write_json(writepath)
    # plotter.fig.show()