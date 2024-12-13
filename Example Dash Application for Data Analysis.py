# -*- coding: utf-8 -*-
"""
Created on Fri Dec 10 11:38:15 2023

@author: tobia
"""

import pandas as pd
import folium
import plotly.express as px
import dash
from dash import dcc, html
from dash.dependencies import Input, Output

# Load the data
data = pd.read_csv("D.gahi_sampling.csv")

# Create a map centered around the Falkland Islands (latitude: -51.7, longitude: -59.0)
map_center = [-51.7, -59.0]
sampling_map = folium.Map(location=map_center, zoom_start=8)

# Add data points to the map
for _, row in data.iterrows():
    folium.CircleMarker(
        location=[row['latitude'], row['longitude']],
        radius=5,
        color='blue',
        fill=True,
        fill_color='blue',
        fill_opacity=0.6,
        popup=f"Length: {row['length']} mm\nWeight: {row['weight']} g\nSex: {row['sex']}\nMaturity: {row['maturity']}"
    ).add_to(sampling_map)

# Save the map to an HTML file
sampling_map.save("falkland_sampling_map.html")
print("Interactive map saved as 'falkland_sampling_map.html'.")


app = dash.Dash(__name__)
app.title = "Squid Data Dashboard"

app.layout = html.Div([
    html.H1("Falkland Islands Squid Data Dashboard", style={"textAlign": "center"}),

    # Map display
    html.Iframe(id="map", srcDoc=open("falkland_sampling_map.html", "r").read(), width="100%", height="600"),



    html.Div([
        html.Label("Select Analysis Type:"),
        dcc.Dropdown(
            id="analysis-type",
            options=[
                {"label": "Length Distribution", "value": "length-dist"},
                {"label": "Weight vs Length", "value": "weight-vs-length"},
                {"label": "Maturity Distribution by Sex", "value": "maturity-dist"},
                {"label": "Summary Statistics", "value": "summary"}
            ],
            value="length-dist"
        )
    ], style={"width": "50%", "margin": "auto"}),

    # Graph output
    dcc.Graph(id="analysis-plot"),

    # Summary statistics table
    html.Div(id="summary-table")
])


@app.callback(
    [Output("analysis-plot", "figure"), Output("summary-table", "children")],
    [Input("analysis-type", "value")]
)
def update_analysis(selected_analysis):
    if selected_analysis == "length-dist":
        fig = px.histogram(data, x='length', nbins=30, title='Length Distribution of Squid', labels={'length': 'Length (mm)'})
        return fig, ""

    elif selected_analysis == "weight-vs-length":
        fig = px.scatter(data, x='length', y='weight', color='sex', title='Weight vs. Length by Sex',
                         labels={'length': 'Length (mm)', 'weight': 'Weight (g)', 'sex': 'Sex'})
        return fig, ""

    elif selected_analysis == "maturity-dist":
        fig = px.histogram(data, x='maturity', color='sex', barmode='group', title='Maturity Stage Distribution by Sex',
                             labels={'maturity': 'Maturity Stage', 'sex': 'Sex'})
        return fig, ""

    elif selected_analysis == "summary":
        # Summary statistics
        summary_stats = data.groupby(['sex', 'maturity']).agg({
            'length': ['mean', 'std'],
            'weight': ['mean', 'std'],
        }).reset_index()
        summary_stats.columns = ['Sex', 'Maturity', 'Mean Length (mm)', 'Length Std', 'Mean Weight (g)', 'Weight Std']

        table = html.Table([
            html.Tr([html.Th(col) for col in summary_stats.columns])
        ] + [
            html.Tr([html.Td(row[col]) for col in summary_stats.columns]) for _, row in summary_stats.iterrows()
        ])

        return {}, table

    else:
        return {}, ""

if __name__ == "__main__":
    app.run_server(debug=True)
