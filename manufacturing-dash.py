import pandas as pd
import requests
import datetime
import plotly.express as px
import dash
from dash import dcc
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State
import plotly.figure_factory as ff

#DATA CAPTURE FOR SYMPTOMS
weekSpan = 52
end = datetime.datetime.today().replace(hour=23,minute=59,second=59)
begin = (end - datetime.timedelta(days=7*(weekSpan-1)) - datetime.timedelta(days=end.weekday())).replace(hour=0, minute=0, second=0)
end = end.strftime("%Y-%m-%d %H:%M:%S")
begin = begin.strftime("%Y-%m-%d %H:%M:%S")
url_PI = "https://nilfisk.visualfactory.net:443/api/public/pipelines/BPK EOL FQC Prod Issues?Lots completed after:=" + begin + "&Lots completed before:=" + end
key_PI = 'APIKEY xyZH9jV6G6GPP0vxraXnX7I9Sz/NSuoH8wm8ARZ/DnU='
QQheaders_PI = {'Authorization': key_PI}
r_PI = requests.get(url_PI, headers = headers_PI)
df = pd.DataFrame(r_PI.json())
df['Issue Created At'] = pd.to_datetime(df['Issue Created At'])
product = list(df['RouteName'].unique())

#DATA CAPTURE FOR QUALITY TEST STATUS
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

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
app.layout = html.Div([
    html.H1("Nilfisk-Brooklyn Park Manufacturing Quality Analytics Dashboard", style={"textAlign": "center"}),
    html.Hr(),
    html.H2("Symptom Analytics", style={"textAlign": "center"}),

    html.Div([
        html.P("Select Product(s)", style={"font-wight": "bold"}, className="two columns"),
        html.P("Select Week Span", style={"textAlign": "center", "font-wight": "bold"}, className="ten columns"),
    ]),

    html.Div([
        html.Div([dcc.Checklist(product, product, inline=True, id='checkbox'), ], className="two columns"),
        html.Div([dcc.Slider(2, 52, 2, value=4, id='slider')], className="ten columns"),
    ], className="row"),

    html.Div(id="output-symptoms", children=[]),
    html.Hr(),
    html.H2("Live Qulaity Test & Inspection Status", style={"textAlign": "center"}),
    html.Div([
        dcc.Dropdown(
            id='dropdown',
            options=options,
            multi=True,
            clearable=False,
            searchable=True,
            style={'width': '50%'}
        ),
    ]),
    html.Div([
        dcc.Graph(id="output-test-status")
    ]),

])


@app.callback(
    Output(component_id="output-symptoms", component_property="children"),
    Input(component_id="checkbox", component_property="value"),
    Input(component_id="slider", component_property="value"),
)
def make_graphs1(checkbox, slider):
    # SUNBURST
    end = datetime.datetime.today().replace(hour=23, minute=59, second=59)
    begin = (end - datetime.timedelta(days=7 * (slider - 1)) - datetime.timedelta(days=end.weekday())).replace(hour=0,
                                                                                                               minute=0,
                                                                                                               second=0)
    begin = begin.strftime("%Y-%m-%d %H:%M:%S")
    df_symptoms_sunburst = \
    df[(df['Workstation'].isin(['Final Quality Check', 'Production Review'])) & (df['Issue Created At'] > begin)][
        ['RouteName', 'Symptom Type', 'Symptom']]
    df_symptoms_sunburst['value'] = 1
    fig_sunburst = px.sunburst(df_symptoms_sunburst, path=['RouteName', 'Symptom Type', 'Symptom'], values='value',
                               title="FQC - Overall Symptoms (only based on selected Week Span)")
    #     fig_sunburst.update_layout(width=6,height=6)

    # SYMPTOM TYPE LINE CHART
    df_symptom = df[
        (df['Workstation'].isin(['Final Quality Check', 'Production Review'])) & (df['RouteName'].isin(checkbox)) & (
                    df['Issue Created At'] > begin)][['Issue Created At', 'Symptom Type', 'Symptom']]
    top5_sym_type = df_symptom.groupby('Symptom Type')['Issue Created At'].count().sort_values(ascending=False).head(5)
    top5_sym_type = top5_sym_type.index.to_list()
    top5_sym = df_symptom.groupby('Symptom')['Issue Created At'].count().sort_values(ascending=False).head(5)
    top5_sym = top5_sym.index.to_list()
    symptom_type_line = df_symptom[df_symptom['Symptom Type'].isin(top5_sym_type)]
    symptom_type_line.sort_values('Issue Created At', ascending=True, inplace=True)
    symptom_type_line['Issue Created At'] = symptom_type_line['Issue Created At'].dt.strftime("%Y %W")
    symptom_type_line = symptom_type_line.groupby(['Issue Created At', 'Symptom Type'], sort=False)[
        'Symptom'].count().reset_index()
    symptom_type_line = symptom_type_line.pivot('Issue Created At', 'Symptom Type')
    symptom_type_line = symptom_type_line.fillna(0)['Symptom']
    for col in symptom_type_line.columns:
        symptom_type_line[col + ' avg'] = symptom_type_line[col].expanding().mean()
        symptom_type_line.drop(col, axis=1, inplace=True)
    symptom_type_line = symptom_type_line.reset_index()
    y = symptom_type_line.columns.to_list()
    y.remove('Issue Created At')
    fig_line_symptom_type = px.line(symptom_type_line, x='Issue Created At', y=y,
                                    title="FQC - Top 5 Symptom Types (based on selected Products & Week Span)")
    fig_line_symptom_type.update_xaxes(tickangle=90, title_text='Year Week#')
    fig_line_symptom_type.update_yaxes(title_text='Count of Defects')

    # SYMPTOM LINE CHART
    symptom_line = df_symptom[df_symptom['Symptom'].isin(top5_sym)]
    symptom_line.sort_values('Issue Created At', ascending=True, inplace=True)
    symptom_line['Issue Created At'] = symptom_line['Issue Created At'].dt.strftime("%Y %W")
    symptom_line = symptom_line.groupby(['Issue Created At', 'Symptom'], sort=False)[
        'Symptom Type'].count().reset_index()
    symptom_line = symptom_line.pivot('Issue Created At', 'Symptom')
    symptom_line = symptom_line.fillna(0)['Symptom Type']
    for col in symptom_line.columns:
        symptom_line[col + ' avg'] = symptom_line[col].expanding().mean()
        symptom_line.drop(col, axis=1, inplace=True)
    symptom_line = symptom_line.reset_index()
    y = symptom_line.columns.to_list()
    y.remove('Issue Created At')
    fig_line_symptom = px.line(symptom_line, x='Issue Created At', y=y,
                               title="FQC - Top 5 Symptoms (based on selected Products & Week Span)")
    fig_line_symptom.update_xaxes(tickangle=90, title_text='Year Week#')
    fig_line_symptom.update_yaxes(title_text='Count of Defects')

    return [
        html.Div([
            html.Div([dcc.Graph(figure=fig_line_symptom_type)]),
            html.Div([dcc.Graph(figure=fig_line_symptom)]),
            html.Div([dcc.Graph(figure=fig_sunburst)]), ])]


@app.callback(
    Output(component_id="output-test-status", component_property="figure"),
    Input(component_id="dropdown", component_property="value"),
)
def make_graphs2(dropdown):
    # QUALITY TEST STATUS
    fil_result = result.copy(deep=True)
    fil_result = fil_result[fil_result['Alias'].isin(dropdown)]
    colors = {'EOL In-Progress': 'rgb(230, 230, 230)',
              'EOL Complete': 'rgb(190,190,190)',
              'Untouched': 'rgb(255,69,0)',
              'FQC In-Progress': 'rgb(230,255,220)',
              'FQC Complete': 'rgb(130,130,130)'}
    fig_test_status = ff.create_gantt(fil_result, index_col='Resource', colors=colors, title=None, showgrid_x=True,
                                      group_tasks=True, show_colorbar=True)
    return fig_test_status


if __name__ == '__main__':
    app.run_server(debug=False)