import pandas as pd
import requests
import datetime
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

df_ipqc = df.loc[~df['Workstation'].isin(['Final Quality Check','Production Review']) & df['RaisedBy'].isin(['Abraham Xiong','Jose Flores','Benson Moua','Mustapha Lumeh'])].sort_values('Issue Created At')
df_ipqc.loc[:,'Issue Created At'] = df_ipqc['Issue Created At'].dt.strftime("%Y %W")
df_ipqc = df_ipqc[['Issue Created At','Line']].groupby('Issue Created At',sort=False).count().expanding().mean()

df_fqcpr = df.loc[df['Workstation'].isin(['Final Quality Check','Production Review'])].sort_values('Issue Created At')
df_fqcpr.loc[:,'Issue Created At'] = df_fqcpr['Issue Created At'].dt.strftime("%Y %W")
df_fqcpr = df_fqcpr[['Issue Created At','Line']].groupby('Issue Created At',sort=False).count().expanding().mean()

df_ipqc_fqcpr = df_ipqc.merge(df_fqcpr, how='inner', left_on='Issue Created At', right_on='Issue Created At').reset_index()
df_ipqc_fqcpr.columns = ['Week #', 'IPQC', 'FQC+PR']
fig = px.line(df_ipqc_fqcpr, x='Week #', y=['IPQC','FQC+PR'], title="Average Defect Count - 'IPQC vs FQC+PR'")
fig.show()