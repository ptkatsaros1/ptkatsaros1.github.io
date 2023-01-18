import requests
from bs4 import BeautifulSoup
import pandas as pd
import webbrowser
import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)

urls = ["http://www.espn.com/nba/seasonleaders", "http://www.espn.com/nba/seasonleaders/_/league/nba/page/2", "http://www.espn.com/nba/seasonleaders/_/league/nba/page/3", "http://www.espn.com/nba/seasonleaders/_/league/nba/page/4"]

df_master = pd.DataFrame(columns=["PLAYER", "PTS", "BLKPG", "STPG", "APG", "RPG", "3PM"])

for i in range(0,4):
    page = requests.get(urls[i])   
    soup = BeautifulSoup(page.content, "html.parser")

    data = []
    table = soup.find("table", class_="tablehead")
    for row in table.find_all("tr")[1:]:
        cells = row.find_all("td")
        player = cells[0].find("a")
        if player:
            player = player.text
        else:
            player = cells[1].text
        pts = cells[13].text
        blkpg = cells[11].text
        stpg = cells[10].text
        apg = cells[9].text
        rpg = cells[8].text
        threepm = cells[7].text
        data.append([player, pts, blkpg, stpg, apg, rpg, threepm])

    df1 = pd.DataFrame(data, columns=["PLAYER", "PTS", "BLKPG", "STPG", "APG", "RPG", "3PM"])
    df1 = df1.drop(0)
    df1['PLAYER'] = df1['PLAYER'].str.split(',').str[0]
    df1 = df1[df1['PLAYER'] != 'PLAYER']
    df_master = df_master.append(df1)

for col in df_master.columns:
    if col != 'PLAYER':
        df_master[col] = df_master[col].astype(float)
        
df_master = df_master.assign(BlksANDStls = df_master['BLKPG'] + df_master['STPG'])
df_master = df_master.assign(PtsANDAsts = df_master['PTS'] + df_master['APG'])
df_master = df_master.assign(PtsANDRebs = df_master['PTS'] + df_master['RPG'])
df_master = df_master.assign(PtsANDRebsANDAsts = df_master['PTS'] + df_master['APG'] + df_master['RPG'])
df_master = df_master.assign(RebsAsts = df_master['RPG'] + df_master['APG'])

df_master = df_master.rename(columns={'BlksANDStls':'Blks+Stls', 'PtsANDAsts':'Pts+Asts', 'PtsANDRebs':'Pts+Rebs', 'PtsANDRebsANDAsts':'Pts+Rebs+Asts', 
'RebsAsts':'Rebs+Asts', '3PM':'3-PT Made', 'APG':'Assists', 'RPG':'Rebounds', 'STPG':'Steals', 'BLKPG':'Blocks', 'PLAYER':'Player', 'PTS': 'Points'})


print(df_master)

print("\n\n")
print('-'*100)
print("\n\n")

url = "https://api.prizepicks.com/projections?league_id=7&per_page=250&single_stat=true"
headers = {
    'Connection': 'keep-alive',
    'Accept': 'application/json; charset=UTF-8',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/106.0.0.0 Safari/537.36',
    'Access-Control-Allow-Credentials': 'true',
    'Sec-Fetch-Site': 'same-origin',
    'Sec-Fetch-Mode': 'cors',
    'Referer': 'https://app.prizepicks.com/',
    'Accept-Encoding': 'gzip, deflate, br',
    'Accept-Language': 'en-US,en;q=0.9'
}

response = requests.get(url=url, headers=headers).json()
included = response["included"]

player_data = []
for item in response["data"]:
    name = next(x["attributes"]["name"] for x in included if x["id"] == item["relationships"]["new_player"]["data"]["id"])
    line_score = item["attributes"]["line_score"]
    stat_type = item["attributes"]["stat_type"]
    player_data.append({"name": name, "line_score": line_score, "stat_type": stat_type})

df = pd.DataFrame(player_data)

df_pivot = df.pivot_table(values='line_score', index='name', columns='stat_type')
df_pivot = df_pivot.reset_index()
df_pivot = df_pivot.rename(columns={'name':'Player2'})

for col2 in df_pivot.columns:
    if col2 != 'Player2':
        df_pivot[col2] = df_pivot[col2].astype(float)
print(df_pivot)



#DIFFERENCE IN REGULAR LINE AND BETTING LINE

df_master_filter = df_master[df_master['Player'].isin(df_pivot['Player2'])]
df_pivot_filter = df_pivot[df_pivot['Player2'].isin(df_master['Player'])]
df_master_filter = df_master_filter.set_index('Player')
df_pivot_filter = df_pivot_filter.set_index('Player2')
# Get the columns that are the same in both DataFrames
common_columns = df_master_filter.columns.intersection(df_pivot_filter.columns)
df_diff = df_master_filter[common_columns].subtract(df_pivot_filter[common_columns], axis=0)
df_diff = df_diff.reset_index()
df_diff['Player'] = df_diff['index']
df_diff = df_diff.drop(['index'], axis = 1)

print("\n\n")
print('-'*100)
print(df_diff)

print("\n\n")
print("\n\n")
top_3_cols = {}
for col in df_diff.select_dtypes(include=['float']).columns:
    top_3_cols[col] = df_diff.nlargest(3, col)
    top_3_cols[col] = top_3_cols[col].merge(df_diff[['Player']], left_index=True, right_index=True)
for col in df_diff.columns:
    if col != 'Player':
        df_diff = df_diff.sort_values(by=[col], ascending=False)
        df_diff.index = range(1, len(df_diff) + 1)
        print('\n')
        print(col)
        print(df_diff[['Player', col]].head(3))

bottom_3_cols = {}
for col in df_diff.select_dtypes(include=['float']).columns:
    bottom_3_cols[col] = df_diff.nsmallest(3, col)
    bottom_3_cols[col] = bottom_3_cols[col].merge(df_diff[['Player']], left_index=True, right_index=True)
for col in df_diff.columns:
    if col != 'Player':
        df_diff = df_diff.sort_values(by=[col], ascending=True)
        df_diff.index = range(1, len(df_diff) + 1)
        print('\n')
        print(col)
        print(df_diff[['Player', col]].head(3))



html_code = '<html><head><style> table {display:inline-block; width:300px; height:200px; padding:20px; margin:10px; font-size:20px;} th, td {border:1px solid #ccc;} </style></head>'
html_code += '<body>'

for col in df_diff.select_dtypes(include=['float']).columns:
    top_3_cols = df_diff.nlargest(3, col)
    top_3_cols = top_3_cols.merge(df_diff[['Player']], left_index=True, right_index=True)
    html_code += '<table>'
    html_code += '<tr>'
    html_code += '<th colspan="2">Over ' + col + '</th>'
    html_code += '</tr>'
    for i, row in top_3_cols.iterrows():
        html_code += '<tr>'
        html_code += '<td>' + row.Player_x + '</td>'
        html_code += '<td>' + str(row[col]) + '</td>'
        html_code += '</tr>'
    bottom_3_cols = df_diff.nsmallest(3, col)
    bottom_3_cols = bottom_3_cols.merge(df_diff[['Player']], left_index=True, right_index=True)
    html_code += '<table>'
    html_code += '<tr>'
    html_code += '<th colspan="2">Under ' + col + '</th>'
    html_code += '</tr>'
    for i, row in bottom_3_cols.iterrows():
        html_code += '<tr>'
        html_code += '<td>' + row.Player_x + '</td>'
        html_code += '<td>' + str(row[col]) + '</td>'
        html_code += '</tr>'

html_code += '</table></body></html>'

with open('top_3_bottom_3.html', 'w') as f:
    f.write(html_code)

webbrowser.open('file:///Users/tomkatsaros/Documents/testpython/top_3_bottom_3.html')


