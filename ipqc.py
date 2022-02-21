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

