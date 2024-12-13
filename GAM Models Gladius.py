# -*- coding: utf-8 -*-
"""
Created on Thu Jun 10 9:11:36 2021

@author: tobia
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pygam import LinearGAM, s, te
from sklearn.metrics import mean_squared_error

# Load data
SI_LOL = pd.read_csv("SI_LOL.csv")

# Grouping and counting stations
stations = SI_LOL.groupby('Station').size().reset_index(name='count')

# Filter data for Type 'Muscle'
muscle_data = SI_LOL[SI_LOL['Type'] == 'Muscle']

# GAM models for d15N
model1a = LinearGAM(te(0, 1) + s(0) + s(1, basis='cc')).fit(muscle_data[['Length', 'Dayj']], muscle_data['d15N'])
model1b = LinearGAM(s(0) + s(1, basis='cc')).fit(muscle_data[['Length', 'Dayj']], muscle_data['d15N'])
model1c = LinearGAM(te(0, 1, basis=['cs', 'cc']) + s(0) + s(1, basis='cc')).fit(muscle_data[['Length', 'Dayj']], muscle_data['d15N'])

# AIC calculations for model comparisons
def calculate_aic(gam, X, y):
    rss = np.sum((y - gam.predict(X))**2)
    n = len(y)
    k = gam.statistics_['n_params']
    return n * np.log(rss / n) + 2 * k

X = muscle_data[['Length', 'Dayj']]
y = muscle_data['d15N']

models = [model1a, model1b, model1c]
aics = [calculate_aic(model, X, y) for model in models]

# Print model summaries
for i, model in enumerate(models):
    print(f"Model {i+1} AIC: {aics[i]}")

# Plotting using seaborn and matplotlib
length_seq = np.linspace(muscle_data['Length'].min(), muscle_data['Length'].max(), 200)
dayj_seq = np.linspace(1, 365, 200)

# Create grid for predictions
data_grid = pd.DataFrame(np.array(np.meshgrid(length_seq, dayj_seq)).T.reshape(-1, 2), columns=['Length', 'Dayj'])

# Predict and plot
predictions = model1c.predict(data_grid)
data_grid['Prediction'] = predictions

grid_pivot = data_grid.pivot('Length', 'Dayj', 'Prediction')
plt.figure(figsize=(12, 6))
sns.heatmap(grid_pivot, cmap="coolwarm", cbar_kws={'label': 'Prediction'}, xticklabels=30, yticklabels=10)
plt.title("GAM Surface Prediction (d15N)")
plt.xlabel("Length")
plt.ylabel("Dayj")
plt.show()

# Filter data for Type 'Gladius'
gladius_data = SI_LOL[SI_LOL['Type'] == 'Gladius']

# GAM models for d13C
gladius_model = LinearGAM(te(0, 1, basis=['cs', 'cc']) + s(0) + s(1, basis='cc')).fit(gladius_data[['Length', 'Dayj']], gladius_data['d13C'])

# Predict for 'Gladius'
gladius_predictions = gladius_model.predict(data_grid)
data_grid['Gladius_Prediction'] = gladius_predictions

grid_pivot_gladius = data_grid.pivot('Length', 'Dayj', 'Gladius_Prediction')
plt.figure(figsize=(12, 6))
sns.heatmap(grid_pivot_gladius, cmap="coolwarm", cbar_kws={'label': 'Prediction'}, xticklabels=30, yticklabels=10)
plt.title("GAM Surface Prediction (d13C)")
plt.xlabel("Length")
plt.ylabel("Dayj")
plt.show()
