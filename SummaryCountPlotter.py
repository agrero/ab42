import plotly.graph_objects as go

import pandas as pd

from sklearn.preprocessing import RobustScaler

import os

class _SummaryCountPlotter:
    def __init__(
            self,
            font_family:str = "Courier",
            title_size:int = 22,
            subplot_title_size:int=14,
            axis_title_size:int = 14,
            axis_tick_size:int = 12,
            legend_size:int = 12,
            ) -> None:
                # PLOT VARIABLES
        self.font_family = font_family

        self.title_size = title_size

        self.subplot_title_size = subplot_title_size

        self.axis_title_size = axis_title_size
        self.axis_tick_size = axis_tick_size

        self.legend_size = legend_size

        # PLOT DICTS
        self.title_font = dict(
            family=self.font_family, 
            size=self.title_size
        )

        self.legend_font = dict(
            family=self.font_family, 
            size=self.legend_size
        )

        self.axis_title_font = dict(
            family=self.font_family, 
            size=self.axis_title_size
        )
        self.axis_tick_font = dict(
            family=self.font_family, 
            size=self.axis_tick_size
        )

class SummaryCountPlotter(_SummaryCountPlotter):
    def __init__(self, X:pd.DataFrame) -> None:
        super().__init__()

        self.X = X

    def plot_columnwise(self, scale_outliers=True) -> None:

        self.fig = go.Figure()

        if scale_outliers:
            y = RobustScaler().fit_transform(self.X.values[1:]).flatten()
        else:
            y = self.X.values.flatten()[1:] # NOTE CHANGE ME ONCE YOU FIX THE DATA EXTRACTION CODE
        
        
        x = [ndx for ndx, _ in enumerate(y)]

        data = go.Bar(
            y=y,
            name="Counts",
            marker=dict(
                color=y,
                colorscale="Portland",
                showscale=False
            )
        )

        self.fig.add_trace(data)

        # ADD MEAN LINE
        # NOTE ADD THIS TO THE PARENT CLASS LATER
        mean = go.Scatter(
            x=[x[0], x[-1]],
            y=[y.mean(), y.mean()],
            mode="lines",
            line=dict(
                color="red",
                width=2,
                dash="dash",
            ),
            name="Mean Counts"
        )
        self.fig.add_trace(mean)

        # UPDATE TITLE

        self.fig.update_layout(
            title = dict(
                text = "Prevalence of Random Coiling Across The Sequence",
                font=self.title_font
            )
        )

        # # UPDATE AXES
        self.fig.update_yaxes(
            title_text="Count",
            title_font=self.axis_title_font,
            tickfont=self.axis_tick_font,
        )

        self.fig.update_xaxes(
            title_text="Sequence Position",
            title_font=self.axis_title_font,
            tickfont=self.axis_tick_font,
        )

    def plot_rowwise(self, seq_length:int=42, scale_outliers:bool=True) -> None:
        
        self.fig = go.Figure()


        y = self.X.value_counts().sort_index() # NOTE CHANGE ME ONCE YOU FIX THE DATA EXTRACTION CODE
        x = y.index.get_level_values(0)
        if scale_outliers:
            y = RobustScaler().fit_transform(y.to_frame()).flatten()
        
        bar = go.Bar(
            x = x, y = y,
            marker=dict(
                color=y,
                colorscale="Portland",
                showscale=False
            )
        )

        self.fig.add_trace(bar)

        # ADD MEAN LINE
        # NOTE ADD THIS TO THE PARENT CLASS LATER
        mean = go.Scatter(
            x=[x[0], x[-1]],
            y=[y.mean(), y.mean()],
            mode="lines",
            line=dict(
                color="red",
                width=2,
                dash="dash",
            ),
            name="Mean Counts",
            hoverinfo="text"
        )
        self.fig.add_trace(mean)

        # UPDATE TITLE

        self.fig.update_layout(
            title = dict(
                text = "Disordered Residue Counts Across Sequence Dataset",
                font=self.title_font
            )
        )

        # # UPDATE AXES
        self.fig.update_yaxes(
            title_text="Count of Sequences with N Disordered Residues",
            title_font=self.axis_title_font,
            tickfont=self.axis_tick_font,
        )

        self.fig.update_xaxes(
            title_text="N Residues Disordered in Sequence",
            title_font=self.axis_title_font,
            tickfont=self.axis_tick_font,
        )




if __name__ == "__main__":

    pdir = "data"
    cols = os.path.join(pdir, "2dary_summary_cols.parquet")
    rows = os.path.join(pdir, "2dary_summary_rows.parquet")

    # NOTE I THINK WE SHOULD ADD A METHOD FOR TAKING THE TOTAL 2NDARY COUNTS 
    # AND CONVERTING IT TO WHAT WE HAVE HERE

    rows = pd.read_parquet(rows)
    plot = SummaryCountPlotter(rows)

    writepath = os.path.join("plots", "2dary_summary_cols.json")
    plot.plot_rowwise(scale_outliers=False)
    plot.fig.write_json(writepath)

    cols = pd.read_parquet(cols)
    plot = SummaryCountPlotter(cols)
    
    writepath = os.path.join("plots", "2dary_summary_rows.json")
    plot.plot_columnwise(scale_outliers=False)
    plot.fig.write_json(writepath)

    
