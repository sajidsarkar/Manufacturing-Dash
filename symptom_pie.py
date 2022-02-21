import pandas as pd
import requests
import datetime
import numpy as np
import plotly.express as px
from dash import Dash, html, dcc

#INITIAL DATA INGESTION AND SETUP
weekSpan = 52
end = datetime.datetime.today().replace(hour=23,minute=59,second=59)
begin = (end - datetime.timedelta(days=7*(weekSpan-1)) - datetime.timedelta(days=end.weekday())).replace(hour=0, minute=0, second=0)
end = end.strftime("%Y-%m-%d %H:%M:%S")
begin = begin.strftime("%Y-%m-%d %H:%M:%S")
url_PI = "https://nilfisk.visualfactory.net:443/api/public/pipelines/BPK EOL FQC Prod Issues?Lots completed after:=" + begin + "&Lots completed before:=" + end
key_PI = 'APIKEY xyZH9jV6G6GPP0vxraXnX7I9Sz/NSuoH8wm8ARZ/DnU='
headers_PI = {'Authorization': key_PI}
r_PI = requests.get(url_PI, headers = headers_PI)
df = pd.DataFrame(r_PI.json())
df.loc[:,'Issue Created At'] = pd.to_datetime(df['Issue Created At'])

df_symptom = df.loc[~df['Symptom Type'].isin(['Assembly Issue', 'Part Shortage', 'Part Shortage Escalation']), :]
df_symptom = df_symptom[['Issue Created At', 'Symptom Type','Line']].sort_values('Issue Created At')
df_symptom.loc[:, 'Issue Created At'] = df_symptom['Issue Created At'].dt.strftime("%Y %W")
top5 = list(df_symptom.groupby('Symptom Type').count().sort_values('Line', ascending=False).head(5).index.values)
df_symptom = df_symptom.loc[df_symptom['Symptom Type'].isin(top5),:].groupby(['Symptom Type'],sort=False).count().reset_index()
fig = px.pie(df_symptom, values='Line', names='Symptom Type', title='Top Five Symptoms')
fig.show()