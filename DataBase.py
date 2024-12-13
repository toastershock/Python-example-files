import pandas as pd
import pyodbc
from datetime import datetime, timedelta
import numpy as np

# Database connections ---------------------------------------------------
def connect_to_db(dsn):
    return pyodbc.connect(f'DSN={dsn}')

fishdev_conn = connect_to_db('fishdev')
fishtwo_conn = connect_to_db('fishtwo')
obsdta_conn = connect_to_db('ObsDta')

# Load data --------------------------------------------------------------
licencedetails = pd.read_sql('SELECT * FROM vwLicenceDetails', fishdev_conn)
licence = pd.read_sql('SELECT * FROM tblLicence', fishdev_conn)
vessel = pd.read_sql('SELECT * FROM Fish_Vessel', fishtwo_conn)
View3 = pd.read_sql('SELECT * FROM View3', fishtwo_conn).drop_duplicates()

# Load other tables
report_catch = pd.read_sql('SELECT * FROM tblReportCatch', fishdev_conn)
species = pd.read_sql('SELECT * FROM tblSpecies', fishdev_conn)
report_daily = pd.read_sql('SELECT * FROM tblReportDaily', fishdev_conn)
report_effort_types = pd.read_sql('SELECT * FROM tblReportEffortTypes', fishdev_conn)
report_detail = pd.read_sql('SELECT * FROM tblReportDetail', fishdev_conn)
unit_detail = pd.read_sql('SELECT * FROM tblUnitDetail', fishdev_conn)
nation_codes = pd.read_sql('SELECT * FROM tblNationCodes', fishdev_conn)

# Date setup
Date = (datetime.now() - timedelta(days=1)).date()

# Queries and joins ------------------------------------------------------
query = (report_catch
         .merge(species[['SpeciesID', 'SpeciesCode', 'ComName']], on='SpeciesID', how='left')
         .merge(report_daily[['ReportID', 'UnitID', 'ReportDate', 'EffortType']], on='ReportID', how='left')
         .merge(report_effort_types, left_on='EffortType', right_on='EffortID', how='left')
         .merge(report_detail.query('DetailType == 1')[['ReportID', 'DetailValue']].rename(columns={'DetailValue': 'NightGrid'}), on='ReportID', how='left')
         .merge(report_detail.query('DetailType == 2')[['ReportID', 'DetailValue']].rename(columns={'DetailValue': 'DayGrid'}), on='ReportID', how='left')
         # Additional joins for other DetailTypes...
        )

# Add filters and additional columns
query = (query
         .merge(unit_detail.query('DetailType == 1')[['UnitID', 'DetailValue', 'ValidFrom', 'ValidTo']].rename(columns={'DetailValue': 'Callsign'}), on='UnitID', how='left')
         .query('ReportDate >= ValidFrom and ReportDate < ValidTo')
         .drop(columns=['ValidFrom', 'ValidTo'])
         .merge(unit_detail.query('DetailType == 5')[['UnitID', 'DetailValue', 'ValidFrom', 'ValidTo']].rename(columns={'DetailValue': 'Nation'}), on='UnitID', how='left')
         .query('ReportDate >= ValidFrom and ReportDate < ValidTo')
         .merge(nation_codes[['NationCode', 'Descr']], left_on='Nation', right_on='Descr', how='left')
         .query(f'ReportDate == "{Date}"')
        )

# Final processing
Catchfile = query.copy()
Catchfile['ReportDate'] = pd.to_datetime(Catchfile['ReportDate'])
Catchfile['Year'] = Catchfile['ReportDate'].dt.year
Catchfile['Month'] = Catchfile['ReportDate'].dt.month
Catchfile['ComName'] = Catchfile['ComName'].astype('category')
Catchfile['SpeciesCode'] = Catchfile['SpeciesCode'].astype('category')
Catchfile['Callsign'] = Catchfile['Callsign'].astype('category')
Catchfile['LicenceUsed'] = Catchfile['LicenceUsed'].str.upper().fillna('NA').astype('category')

# Read additional CSV file
Gridsquare_Position = pd.read_csv("Y:/R_Code_shares/Useful Scripts (Date and Position from Database)_Tobias Buring/Positions_Gridsquares.csv")
Catchfile['GS'] = Catchfile['DayGrid'].astype(str)
Catchfile = pd.merge(Catchfile, Gridsquare_Position, on='GS', how='inner')

# Replace NA values
Catchfile.fillna('NA', inplace=True)
Catchfile['LicenceUsed'] = Catchfile['LicenceUsed'].apply(lambda x: 'NA' if not x or x == '' else x)

# Save data
Catchfile.to_pickle(f'data4r/catchlog_{Date}.pkl')

# Other data exports -----------------------------------------------------
daily_report_orig = pd.read_sql('SELECT * FROM tblDailyReport', fishdev_conn)
positions_orig = pd.read_sql('SELECT * FROM tblPositions', fishdev_conn)
lines_orig = pd.read_sql('SELECT * FROM tblLines', fishdev_conn)
catch_orig = pd.read_sql('SELECT * FROM tblCatch', fishdev_conn)

# Save to pickle
for df, name in zip([daily_report_orig, positions_orig, lines_orig, catch_orig],
                    ['daily_report_orig', 'positions_orig', 'lines_orig', 'catch_orig']):
    df.to_pickle(f'data4r/{name}_{Date}.pkl')

# Length frequencies -----------------------------------------------------
combined_stations = pd.read_sql('SELECT * FROM Combined_Stations_View_New', obsdta_conn)
lfreq = pd.read_sql('SELECT * FROM LENGTHWT', obsdta_conn).groupby('Species').size().reset_index(name='Count')

too_lfreq_orig = (combined_stations
                  .merge(lfreq, on=['Callsign', 'Station'], how='inner')
                  .query('Species == "TOO"'))

too_lfreq_orig.to_pickle(f'data4r/too_lfreq_orig_{Date}.pkl')

# Age frequencies --------------------------------------------------------
otolith = pd.read_sql('SELECT * FROM OTOLITH', obsdta_conn)
station = pd.read_sql('SELECT * FROM STATION', obsdta_conn)

# Filter and merge
too_age_orig = (combined_stations
                .merge(otolith, on=['Callsign', 'Station'], how='inner')
                .query('Species == "TOO"'))

otolith2 = otolith.groupby('Species').size().reset_index(name='Count')
otolith1 = pd.DataFrame({'Species': ['All'], 'Count': [otolith2['Count'].sum()]})

all_data = pd.concat([otolith2, otolith1], ignore_index=True)

# Export
too_age_orig.to_pickle(f'data4r/too_age_orig_{Date}.pkl')
