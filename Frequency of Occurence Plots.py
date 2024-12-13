# -*- coding: utf-8 -*-
"""
Created on Tue Apr 21 14:17:18 2020

@author: tobia
"""

import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
from statsmodels.gam.api import GLMGam, BSplines
from patsy import dmatrix

# Read data
stomachs = pd.read_csv("C:/Users/tobing12/Documents/PhD/Data/Stomachs/Stomach_17_03_2021.csv")

# Create Sizeclass column
stomachs['Sizeclass'] = np.where(
    stomachs['Length'] < 13, '<13cm',
    np.where(stomachs['Length'] <= 19, '13-19cm', '>19cm')
)

# Select columns for FO
FO = stomachs.iloc[:, 65:81].assign(
    Month=stomachs['Month'],
    Season=stomachs['Season'],
    Daytime=stomachs['Daytime'],
    Area=stomachs['Area'],
    Length=stomachs['Length'],
    Depth=stomachs['Depth']
)

# Group by and add counts
FO['Length_n'] = FO.groupby(['Cohort', 'Sizeclass'])['Length'].transform('count')

# Add Depth category
FO['Depth_cat'] = np.where(
    FO['Depth'] < 153, 'shallow',
    np.where(FO['Depth'] < 231, 'medium', 'deep')
)

# Add additional group counts
for group_col in ['Cohort', 'Sizeclass', 'Depth_cat', 'Area', 'Daytime', 'Season']:
    FO[f'n_{group_col}'] = FO.groupby(group_col)['Depth'].transform('count')

# Rename a column
FO.rename(columns={'Chaetog0th_ap': 'Chaetognaths_ap'}, inplace=True)

# Create summarized columns
FO['Others'] = FO[['Other_ap', 'Sand_ap', 'Gastropod_ap', 'Debri_ap']].sum(axis=1)
FO['Fish'] = FO[['Fish_ap', 'Fishscales_ap', 'Myctophid_ap']].sum(axis=1)
FO['Euphasiids'] = FO[['Crustaceans_ap', 'Euphasiids_ap']].sum(axis=1)
FO['Amphipods'] = FO[['Themisto_ap', 'Phronima_ap', 'Amphipods_ap']].sum(axis=1)
FO['Cephalopods'] = FO[['Cephalopod_ap', 'Loligo_ap']].sum(axis=1)
FO['Chaetognaths'] = FO['Chaetognath_ap']
FO['Munida'] = FO['Munida_ap']

# Binary conversion
for col in ['Others', 'Fish', 'Euphasiids', 'Amphipods', 'Cephalopods', 'Chaetognaths', 'Munida']:
    FO[col] = np.where(FO[col] >= 1, 1, 0)

# Reshape data (long format)
FO_long = pd.melt(FO, id_vars=['Cohort', 'Sizeclass'], value_vars=['Others', 'Fish', 'Euphasiids', 'Amphipods', 'Cephalopods', 'Chaetognaths', 'Munida'],
                  var_name='Preytype', value_name='Preytype_counts')

# Add Subgroup column
FO_long['Subgroup'] = np.where(
    FO_long['Preytype'].isin(['Themisto', 'Phronima', 'Amphipods']), 'Amphipoda',
    np.where(FO_long['Preytype'] == 'Fishscales', 'Fish',
    np.where(FO_long['Preytype'].isin(['Debri', 'Sand']), 'Other',
    np.where(FO_long['Preytype'] == 'Loligo', 'Decapoda', FO_long['Preytype'])))
)

# Filter non-zero counts
FO_long = FO_long[FO_long['Preytype_counts'] != 0]

# Summarize data
FO_summary = FO_long.groupby(['Subgroup', 'Cohort', 'Sizeclass'], as_index=False).agg(
    Sum_counts=('Preytype_counts', 'sum'),
    n=('Preytype_counts', 'count')
)
FO_summary['FO'] = FO_summary['Sum_counts'] / FO_summary['n'] * 100
FO_summary1 = FO_summary[FO_summary['FO'] != 0]
FO_summary1.sort_values('Depth_cat', ascending=False, inplace=True)

# Save summary data
FO_summary.to_csv("FO_Length_overall.csv", index=False)

# Plot Frequency of Occurrence by Preytype
sns.barplot(data=FO_summary, x='Preytype', y='FO', hue='Cohort', dodge=True)
plt.xticks(rotation=-90)
plt.ylabel("FO[%]")
plt.legend(loc='lower center')
plt.show()

# GAM model using statsmodels
# Example: Define spline basis for Depth
X_spline = dmatrix("bs(Depth, df=4)", data=FO_summary1, return_type='dataframe')
gam_model = GLMGam.from_formula("FO ~ Preytype * Depth", data=FO_summary1, smoother=BSplines(X_spline, df=[4], degree=[3]))
gam_results = gam_model.fit()
print(gam_results.summary())

# Save final figure
plt.savefig("Frequency_of_occurence_per_DML_Linetype.png", dpi=300)

# Boxplot for Depth
sns.boxplot(y=FO['Depth'])
plt.show()

# Summary statistics
print(FO['Depth'].describe())
