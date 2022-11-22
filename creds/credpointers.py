import streamlit as st
from google.oauth2 import service_account

# pysheet credentials from secrets file
pysheet_creds = dict(zip(st.secrets["pysheet_creds_keys"],st.secrets["pyseet_creds_values"]))

# scopes required to do necessary tasks with google sheets
SCOPES = ('https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive')

# create Google sheets credential object
pysheet_customcreds = service_account.Credentials.from_service_account_info(pysheet_creds,scopes=SCOPES)

# pull redshift database credentials from secrets file
dbcreds = dict(zip(st.secrets["dbcreds_keys"],st.secrets["dbcreds_values"]))

pysheet2_creds = dict(zip(st.secrets["pysheet_creds_keys"],st.secrets["pysheet_2_creds_values"]))


dbcreds_baro = dict(zip(st.secrets["dbcreds_keys"],st.secrets["dbcreds_baro_values"]))
