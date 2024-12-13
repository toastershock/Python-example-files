# -*- coding: utf-8 -*-
"""
Created on Fri Oct 14 15:27:45 2020

@author: tobia
"""

import pandas as pd
import folium
import plotly.express as px
import plotly.graph_objects as go

# Load the data
data = pd.read_csv("D.gahi_sampling.csv")

# Check the first few rows of the data
print(data.head())

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

# Plotly data exploration
# Length distribution
fig_length = px.histogram(data, x='length', nbins=30, title='Length Distribution of Squid', labels={'length': 'Length (mm)'})
fig_length.show()

# Weight vs Length scatter plot
fig_scatter = px.scatter(data, x='length', y='weight', color='sex', title='Weight vs. Length by Sex',
                         labels={'length': 'Length (mm)', 'weight': 'Weight (g)', 'sex': 'Sex'})
fig_scatter.show()

# Maturity stage distribution by sex
fig_maturity = px.histogram(data, x='maturity', color='sex', barmode='group', title='Maturity Stage Distribution by Sex',
                             labels={'maturity': 'Maturity Stage', 'sex': 'Sex'})
fig_maturity.show()

# Summary statistics
summary_stats = data.groupby(['sex', 'maturity']).agg({
    'length': ['mean', 'std'],
    'weight': ['mean', 'std'],
}).reset_index()
summary_stats.columns = ['Sex', 'Maturity', 'Mean Length (mm)', 'Length Std', 'Mean Weight (g)', 'Weight Std']
print("Summary Statistics:")
print(summary_stats)

# Length and weight box plots by sex
fig_box = px.box(data, x='sex', y='length', color='sex', title='Length Distribution by Sex',
                 labels={'sex': 'Sex', 'length': 'Length (mm)'})
fig_box.show()

fig_box_weight = px.box(data, x='sex', y='weight', color='sex', title='Weight Distribution by Sex',
                         labels={'sex': 'Sex', 'weight': 'Weight (g)'})
fig_box_weight.show()

# Save the summary statistics to a CSV file
summary_stats.to_csv("summary_statistics.csv", index=False)
print("Summary statistics saved to 'summary_statistics.csv'.")
