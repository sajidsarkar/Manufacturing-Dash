import pandas as pd
import requests
import datetime
import plotly.figure_factory as ff
from dash import Dash, dcc, html, Input, Output
app = Dash(__name__)
server = app.server

def data_generator(weekSpan, work_segment=False, production_issue=False):
       if work_segment==True and production_issue==True:
              pass
       elif work_segment==True:
              end = datetime.datetime.today().replace(hour=23, minute=59, second=59)
              begin = end - datetime.timedelta(days=weekSpan)
              end = end.strftime("%Y-%m-%d %H:%M:%S")
              begin = begin.strftime("%Y-%m-%d %H:%M:%S")
              url_WS = "https://nilfisk.visualfactory.net:443/api/public/pipelines/BPK EOL FQC Timings?Lots completed after:=" + begin + "&Lots completed before:=" + end
              key_WS = 'APIKEY xyZH9jV6G6GPP0vxraXnX7I9Sz/NSuoH8wm8ARZ/DnU='
              headers_WS = {'Authorization': key_WS}
              r_WS = requests.get(url_WS, headers=headers_WS)
              df = pd.DataFrame(r_WS.json())
              df.loc[:, ['StartTime']] = pd.to_datetime(df.StartTime).dt.tz_localize(None) - pd.Timedelta(hours=6)
              df.loc[:, ['EndTime']] = pd.to_datetime(df.EndTime).dt.tz_localize(None) - pd.Timedelta(hours=6)
              df.loc[:, ['LotOpCompletedAt']] = pd.to_datetime(df.LotOpCompletedAt).dt.tz_localize(None) - pd.Timedelta(
                     hours=6)
              return df
       elif production_issue==True:
              pass
       else: pass
def table_maker(type, resource, station, weekSpan, RouteNames = ['7765','CS7010','SW8000', 'SC8000', 'Liberty', 'SC6500']):
       df = data_generator(weekSpan, work_segment=True)
       if type == 'complete':
              df_out = df.loc[ (df['RouteName'].isin(RouteNames)) & (df['WorkStationName'].isin([station,station.upper()])) & (~df['LotOpCompletedAt'].isna()), ['RouteName','WorksOrderAlias','StartTime','LotOpCompletedAt']].groupby('WorksOrderAlias',sort=False).min().reset_index()
              df_out = df_out.rename(columns={'LotOpCompletedAt': 'Finish', 'WorksOrderAlias': 'Alias', 'RouteName':'Product', 'StartTime':'Start'})
              df_out['Resource'] = resource
              return df_out
       elif type == 'in-progress':
              df_out = df.loc[(df['RouteName'].isin(RouteNames)) & (df['WorkStationName'].isin([station,station.upper()])) & (df['LotOpCompletedAt'].isna()), ['RouteName','WorksOrderAlias','StartTime']].groupby('WorksOrderAlias',sort=False).min().reset_index()
              df_out['Finish'] = pd.Timestamp.now()
              df_out['Resource'] = resource
              df_out = df_out.rename(columns={'WorksOrderAlias': 'Alias', 'RouteName': 'Product', 'StartTime':'Start'})
              return df_out
       elif type == 'livepending' and station == 'Final Quality Check':
              df_c = table_maker('complete','EOL Complete','End of Line', weekSpan)
              df_out = df.loc[(df['RouteName'].isin(RouteNames)) & (df['WorkStationName'].isin([station,station.upper()])), ['RouteName', 'WorksOrderAlias', 'StartTime']].groupby('WorksOrderAlias',sort=False).min().reset_index()
              df_out = df_out.rename(columns={'RouteName':'Product','WorksOrderAlias':'Alias','StartTime':'Start'})
              df_out = df_c.merge(df_out, how='left', left_on='Alias', right_on='Alias',indicator=True).query("_merge == 'left_only'").drop(['Product_y','Start_x','Start_y','_merge'],1)
              df_out = df_out.rename(columns={'Finish':'Start','Product_x':'Product'})
              df_out['Finish'] = pd.Timestamp.now()
              df_out['Resource'] = 'Untouched'
              return df_out
       elif type == 'pastpending' and station == 'Final Quality Check':
              df1 = df.loc[(df['RouteName'].isin(RouteNames)) & (df['WorkStationName'].isin([station,station.upper()])), ['RouteName', 'WorksOrderAlias', 'StartTime']].groupby('WorksOrderAlias',sort=False).min().reset_index()
              df1 = df1.rename(columns={'RouteName':'Product','WorksOrderAlias':'Alias','StartTime':'Start'})
              df2 = table_maker('complete','EOL Complete','End of Line', weekSpan)
              df_out = df2.merge(df1, how='inner', left_on = 'Alias', right_on='Alias').drop(['Start_x','Product_y'],1)
              df_out = df_out.rename(columns={'Product_x':'Product','Start_y':'Finish','Finish':'Start'})
              df_out['Resource'] = 'Untouched'
              return df_out
def organizer(weekSpan):
       df_fqc_c = table_maker('complete','FQC Complete', 'Final Quality Check', weekSpan)
       df_eol_c = table_maker('complete','EOL Complete', 'End of Line',weekSpan)
       df_eol_p = table_maker('in-progress', 'EOL In-Progress', 'End of Line',weekSpan)
       df_fqc_p = table_maker('in-progress', 'FQC In-Progress', 'Final Quality Check',weekSpan)
       df_fqc_s = table_maker('livepending', 'Untouched', 'Final Quality Check',weekSpan)
       df_fqc_s2 = table_maker('pastpending', 'Untouched', 'Final Quality Check',weekSpan)

       result = pd.concat([df_fqc_c, df_eol_c, df_eol_p, df_fqc_p, df_fqc_s, df_fqc_s2], axis=0)
       result['Task'] = result['Product'] + ' ' + result['Alias']
       result['Duration'] = result['Finish'] - result['Start']
       # result = result.loc[result['Alias'].isin(user_input)].sort_values('Resource')
       # result = result.loc[result['Start'] > (pd.Timestamp.now() - pd.Timedelta(days=3))].sort_values('Resource')
       return result

result = organizer(4)
options = list(result['Alias'])

app.layout = html.Div([
       html.Div([
              html.H1(['Time Line View of EOL and FQC Operations']),
              dcc.Dropdown(
                     id='my_dropdown',
                     options=options,
                     multi=True,
                     clearable=False,
                     searchable=True,
                     style={'width':'50%'}
              ),
       ]),
       html.Div([
              dcc.Graph(id='the_graph')
       ]),
])

@app.callback(
       Output(component_id='the_graph',component_property='figure'),
       Input(component_id='my_dropdown',component_property='value'),
)
def update_figure(selected_products):
       fil_result = result.copy(deep=True)
       fil_result = fil_result.loc[fil_result['Alias'].isin(selected_products), :]
       colors = {'EOL In-Progress': 'rgb(230, 230, 230)',
                 'EOL Complete': 'rgb(190,190,190)',
                 'Untouched': 'rgb(255,69,0)',
                 'FQC In-Progress': 'rgb(230,255,220)',
                 'FQC Complete': 'rgb(130,130,130)'}
       fig = ff.create_gantt(fil_result, index_col = 'Resource', colors=colors, title=None, showgrid_x=True, group_tasks=True, show_colorbar=True)
       return fig
if __name__ == '__main__':
       app.run_server(debug=True)