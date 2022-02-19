import pandas as pd
import requests
import datetime
import plotly.express as px
from dash import Dash, html, dcc

def one_hot(x, df, category):
  one_hot_x = []
  one_hot_y = []

  if len(df['Issue Created At'].tolist()) == 0:
    return [0] * len(x)
  i = df['Issue Created At'].tolist()[0]
  for j in x:
    if i > j:
      one_hot_x.append(0)
      one_hot_y.append(0)
    elif i == j:
      one_hot_x.append(1)
      one_hot_y.append(df.loc[df['Issue Created At'] == i,[category]].values[0][0])
    elif i < j and i+1 not in df['Issue Created At'].tolist():
      one_hot_x.append(0)
      one_hot_y.append(0)
      i += 1
    elif i < j and i+1 in df['Issue Created At'].tolist():
      i += 1
      one_hot_x.append(1)
      one_hot_y.append(df.loc[df['Issue Created At'] == i,[category]].values[0][0])
  return one_hot_y

#INITIAL DATA INGESTION AND SETUP
weekSpan = 7
end = datetime.datetime.today().replace(hour=23,minute=59,second=59)
begin = (end - datetime.timedelta(days=7*(weekSpan-1)) - datetime.timedelta(days=end.weekday())).replace(hour=0, minute=0, second=0)
end = end.strftime("%Y-%m-%d %H:%M:%S")
begin = begin.strftime("%Y-%m-%d %H:%M:%S")
url_PI = "https://nilfisk.visualfactory.net:443/api/public/pipelines/BPK EOL FQC Prod Issues?Lots completed after:=" + begin + "&Lots completed before:=" + end
key_PI = 'APIKEY xyZH9jV6G6GPP0vxraXnX7I9Sz/NSuoH8wm8ARZ/DnU='
headers_PI = {'Authorization': key_PI}
r_PI = requests.get(url_PI, headers = headers_PI)
week_begin = datetime.datetime.strptime(begin, "%Y-%m-%d %H:%M:%S").isocalendar()[1]
week_end = datetime.datetime.strptime(end, "%Y-%m-%d %H:%M:%S").isocalendar()[1]
x = pd.Series(list(range(week_begin, week_end + 1, 1)))
df_PI = pd.DataFrame(r_PI.json())
df_PI.loc[:,['Issue Created At']] = pd.to_datetime(df_PI['Issue Created At'])
df_PI_FQCPR = df_PI.loc[((df_PI['Workstation'] == 'Final Quality Check') | (df_PI['Workstation'] == 'Production Review')) & (df_PI['Issue Created At'] >= begin) & (df_PI['Issue Created At'] <= end)].sort_values('Issue Created At', ascending=False)
df_PI_FQCPR.loc[:,'Issue Created At'] = df_PI_FQCPR['Issue Created At'].dt.strftime('%W')
df_PI_IPQC = df_PI.loc[((df_PI['Workstation'] != 'Final Quality Check') & (df_PI['Workstation'] != 'Production Review')) & (df_PI['Issue Created At'] >= begin) & (df_PI['Issue Created At'] <= end) & (df_PI['RaisedBy'].isin(['Abraham Xiong', 'Jose Flores', 'Benson Moua', 'Mustapha Lumeh']))].sort_values('Issue Created At', ascending=False)
df_PI_IPQC.loc[:,'Issue Created At'] = df_PI_IPQC['Issue Created At'].dt.strftime('%W')
df_fqc = df_PI_FQCPR.groupby('Issue Created At').count().reset_index().loc[:,['Issue Created At', 'RouteName']].astype({'Issue Created At': 'int'})
df_ipqc = df_PI_IPQC.groupby('Issue Created At').count().reset_index().loc[:,['Issue Created At', 'RouteName']].astype({'Issue Created At': 'int'})
y_fqc = pd.Series(one_hot(x, df_fqc, 'RouteName')).expanding().mean()
y_ipqc = pd.Series(one_hot(x, df_ipqc, 'RouteName')).expanding().mean()
df_plot = pd.concat([x,y_fqc,y_ipqc], axis=1)
# df_plot = pd.concat([x,df_plot], axis=1)
df_plot.columns = ['Week #','FQC+PR','IPQC']
fig = px.line(df_plot, x='Week #', y=['FQC+PR','IPQC'], markers=True, title='Average Defect Count\nfor FQC+PR vs IPQC')
app = Dash(__name__)
app.layout = html.Div([
  html.H1(children='Welcome to Nilfisk BPK Dashboard'),
  dcc.Graph(
    id='FQC+PR vs IPQC',
    figure = fig
  )
])
if __name__ == '__main__':
  app.run_server(host='0.0.0.0', debug=False)