import pandas as pd
import plotly.graph_objects as go
import plotly.express as px 
import dash
import dash_bootstrap_components as dbc
import dash_ag_grid as dag

from dash import html, dash_table
from dash import dcc
from dash.dependencies import Output, Input 
from dash.exceptions import PreventUpdate
from unicodedata import lookup
from dash.dash_table.Format import Format, Group

master_file = 'https://github.com/Filichkin/Interactive_Dasboard_Plotly_Dash/blob/main/data/dwcc_master_git_model.xlsx'

jan_dcc = pd.read_excel(master_file, sheet_name='jan')
feb_dcc = pd.read_excel(master_file, sheet_name='feb')
mar_dcc = pd.read_excel(master_file, sheet_name='mar')
apr_dcc = pd.read_excel(master_file, sheet_name='apr')
sub_dcc = pd.read_excel(master_file, sheet_name='total')

month_list = [jan_dcc, feb_dcc, mar_dcc, apr_dcc, sub_dcc]
dash_tab = pd.concat(month_list).reset_index(drop=True)
freeze = dash_tab.query('dealer_name.str.contains("Freeze")')
freeze_rs = list(freeze['mobis_code'].unique())

tab_top_dealers =\
dash_tab.query('mobis_code != @freeze_rs').filter(items=['year', 'month', 'dealer_name', 'dealer_code', 'warranty',
                                        'dm2pu_p', 'dcpu_p', 'cpc_p',
                                        'rvs_p', 'campaign_p', 'courtesy_car_p', 'trp_2_p',
                                        'sws_p', 'dowt_p', 'total_points'])

pivot = tab_top_dealers.query('month == "January"').pivot_table(
    index=['warranty'], values='total_points',
    aggfunc='sum'
).reset_index()

tab_top_dealers_data =\
dash_tab.query('mobis_code != @freeze_rs').filter(items=['year', 'month', 'dealer_name', 'dealer_code', 'warranty',
    'uio', 'm2_cost', 'm2_qty', 'parts_cost', 'claim_qty', 'total_cost', 'novs', 'dm2pu', 'dcpu', 'cpc',
    'rvs', 'campaign', 'courtesy_car', 'sws', 'sws_ratio', 'trp_2', 'dowt', 'total_points'])

indicator_columns = ['m2_cost', 'parts_cost', 'total_cost', 'dm2pu', 'dcpu', 'cpc',
                     'rvs', 'campaign']
indicator_columns_other = ['uio', 'm2_qty', 'claim_qty', 'novs', 'courtesy_car', 'sws', 'sws_ratio', 'trp_2']

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP, dbc.icons.FONT_AWESOME, dbc.icons.BOOTSTRAP])

app.layout = html.Div([
    dbc.Col([
        html.Br(),
        html.H1('DWES'),
        html.H2('Dealer Warranty Evaluation System')
    ]
    ),
    
    
    
    html.Br(),
    dbc.Row([
        dbc.Col([
            dbc.Label('Year of report:'),
            dcc.Dropdown(id='year_dropdown', optionHeight=40,
                         value=2024,
                         options=[{'label': year, 'value': year}
                                  for year in dash_tab['year'].unique()])
            ], lg=6),
        
        dbc.Col([
            dbc.Label('Month of report:'),
            dcc.Dropdown(id='month_dropdown',
                         value='January',
                         options=[{'label': month, 'value': str(month)}
                                  for month in dash_tab['month'].unique()]),
    ], lg=6)
    ]
    ),
        
    html.Br(),

    
       html.Div(id='grid-callback-example'),

  

       
        
    dbc.Row([
       dbc.Col([
            dcc.Graph(id='dealer_chart')
        ], lg=6),
       
       dbc.Col([
            dcc.Graph(id='support_chart')
        ], lg=6),
       
   ]),
    
    html.Button('To excel', id='btn_xlsx'),
    dcc.Download(id='download-dataframe-xlsx'),
    
    dbc.Tabs(
    [
        dbc.Tab(label='Penalty points by KPI', tab_id='tab_1',
                className='custom-tabs', active_tab_class_name='custom-tab--selected'),
        dbc.Tab(label='Warranty data', tab_id='tab_2',
                className='custom-tabs', active_tab_class_name='custom-tab--selected'),
        dbc.Tab(label='KPI description', tab_id='tab_3',
                className='custom-tabs', active_tab_class_name='custom-tab--selected'),
    ], id='tabs'),
    
    html.Div(id='content'),
    
    
    
    
    
    html.Br(),
    
    dbc.Row([
        dbc.Col([
            dbc.Label('Dealer code:'),
            dcc.Dropdown(id='code_dropdown',
                         value='DNW001',
                         options=[{'label': dealer, 'value': dealer}
                                  for dealer in dash_tab['dealer_code'].sort_values().unique()])
            ], lg=4),
    
        dbc.Col([
            dbc.Label('KPI indicator:'),
            dcc.Dropdown(id='indicator_dropdown', optionHeight=40,
                         value='total_cost',
                         options=[{'label': indicator, 'value': indicator}
                                  for indicator in indicator_columns])
            ], lg=4),
        
        dbc.Col([
            dbc.Label('Dealer indicator:'),
            dcc.Dropdown(id='dealer_indicator_dropdown', optionHeight=40,
                         value='uio',
                         options=[{'label': indicator, 'value': indicator}
                                  for indicator in indicator_columns_other])
            ], lg=4)
        ]),
    
    html.Br(),
    dbc.Row([
       dbc.Col([
            dcc.Graph(id='dealer_chart_points')
        ], lg=4),
       
       dbc.Col([
            dcc.Graph(id='kpi_chart')
        ], lg=4),
        
        dbc.Col([
            dcc.Graph(id='other_chart')
        ], lg=4),
       
   ]),
     
])

@app.callback(Output('grid-callback-example', 'children'),
              Output('dealer_chart', 'figure'),
              Output('support_chart', 'figure'),              
#              Output('table_dealers_output', 'children'),
#              Output('table_dealers_data_output', 'children'),
              Output('content', 'children'),
              Input('year_dropdown', 'value'),
              Input('month_dropdown', 'value'),
              Input('tabs', 'active_tab')
             )



def plot_dealers_by_points(year, month, active_tab):
    sum_tab = dash_tab.query('year == @year and month == @month and mobis_code != @freeze_rs')
    uio = sum_tab['uio'].sum()
    novs = sum_tab['novs'].sum()
    total = sum_tab['total_cost'].sum()
    qty = sum_tab['claim_qty'].sum()
    m2 = sum_tab['m2_cost'].sum()
    m2_qty = sum_tab['m2_qty'].sum()
    camp = sum_tab['campaign'].mean()/100
    data = {'UIO': [uio], 'NOVS': [novs], 'Total amount': [total],
            'Claims qty': [qty], 'M2 amount': [m2], 'M2 qty': [m2_qty], 'Campaign': [camp]}
    df_tab = pd.DataFrame(data)
    
    
    columnDefs_main = [
        {'field': 'UIO', 'headerName': 'UIO', 
            'valueFormatter': {'function': "d3.format(',.0f')(params.value)"}, 'width': 200,
        "cellStyle": {'textAlign': 'center'}},
        {'field': 'NOVS', 'headerName': 'NOVS',
            'valueFormatter': {'function': "d3.format(',.0f')(params.value)"}, 'width': 200,
        "cellStyle": {'textAlign': 'center'}},
        {'field': 'Total amount', 'headerName': 'TOTAL AMOUNT (RUB)',
            'valueFormatter': {'function': "d3.format(',.0f')(params.value)"}, 'width': 200,
        "cellStyle": {'textAlign': 'center'}},                                       
        {'field': 'Claims qty', 'headerName': 'CLAIM QUANTITY',
            'valueFormatter': {'function': "d3.format(',.0f')(params.value)"}, 'width': 200,
        "cellStyle": {'textAlign': 'center'}},
        {'field': 'M2 amount', 'headerName': 'M2 AMOUNT (RUB)',
            'valueFormatter': {'function': "d3.format(',.0f')(params.value)"}, 'width': 200,
        "cellStyle": {'textAlign': 'center'}},
        {'field': 'M2 qty', 'headerName': 'M2 QUANTITY',
            'valueFormatter': {'function': "d3.format(',.0f')(params.value)"}, 'width': 200,
        "cellStyle": {'textAlign': 'center'}},
        {'field': 'Campaign', 'headerName': 'CAMPAIGN',
            'valueFormatter': {'function': "d3.format('.0%')(params.value)"}, 'width': 200,
        "cellStyle": {'textAlign': 'center'}}
        ]
    

    
    
    table_main = dag.AgGrid(
        rowData=df_tab.to_dict('records'),
        columnDefs=columnDefs_main,
        defaultColDef={
                       'headerClass': 'center-aligned-header',
                       'wrapHeaderText': True,
                       'autoHeaderHeight': False},
        dashGridOptions={'animateRows': False, 'pagination':False,
                         'rowHeight': 55,
                         'headerHeight': 55},
        rowStyle = {'backgroundColor': 'white', 'fontSize': '22px', "color": '#005792',
                   'padding': '15px'},
        columnSize="sizeToFit",
        className='ag-theme-custom-theme',
        style={"height": 110, "width": 1400}

        )

    
    
    
    
    month_df =\
    tab_top_dealers.query('year == @year and month == @month').sort_values(by='total_points', ascending=False)[:10]
    fig1 = px.bar(                 
    x=month_df['total_points'],
    y=month_df['dealer_name'],
    text=month_df['total_points'],
    height=400,
#    width=700,
    title=f'Top 10 dealers by penalty points in {month}',
    orientation='h',
#    color=month_df['total_points'],
    color_discrete_sequence=['lightsteelblue']
    
)
    fig1.update_layout(yaxis={'categoryorder': 'total ascending'})
    fig1.layout.xaxis.title = 'Total points'
    fig1.layout.yaxis.title = None
    fig1.update_coloraxes(showscale=False)
    
    
    month_support =\
    dash_tab.query('year == @year and month == @month and mobis_code != @freeze_rs').pivot_table(
        index=['warranty'], values='total_points', aggfunc='mean').reset_index()
    
    fig2 = px.bar(                 
    x=month_support['total_points'],
    y=month_support['warranty'],
    text=month_support['total_points'],
    height=400,
#    width=700,
    text_auto='.1f',
    title=f'Top penalty points by support in {month}',
    orientation='h',
    color=month_support['warranty'],
    color_discrete_sequence=px.colors.qualitative.Pastel1
    
)
    fig2.update_layout(yaxis={'categoryorder':'total ascending'}, showlegend=False)
    fig2.layout.xaxis.title = 'Total points'
    fig2.layout.yaxis.title = None
    fig2.update_coloraxes(showscale=False)
    
    
# table of points

    table_month = tab_top_dealers.query('year == @year and month == @month').sort_values(by='total_points',
                                                                      ascending=False)[:200]
    table_month = table_month.drop(['year', 'month'], axis=1)
    
    
    columnDefs = [
        {'field': 'dealer_name', 'headerName': 'Dealer name', 'width': 200},
        {'field': 'dealer_code', 'headerName': 'Code', 'width': 100,
                    "cellStyle": {'textAlign': 'center'}},
        {'field': 'warranty', 'headerName': 'Support', 'width': 110,
                    "cellStyle": {'textAlign': 'center'}},
        {'field': 'dm2pu_p', 'headerName': 'DM2PU', 'width': 100, "cellStyle": {'textAlign': 'center'},
        'headerTooltip': 'Dealer M2 cost per unit'},
        {'field': 'dcpu_p', 'headerName': 'DCPU', 'width': 100,
                    "cellStyle": {'textAlign': 'center'}},
        {'field': 'cpc_p', 'headerName': 'CPC', 'width': 100,
                    "cellStyle": {'textAlign': 'center'}},
        {'field': 'rvs_p', 'headerName': 'RVS', 'width': 100,
                    "cellStyle": {'textAlign': 'center'}},
        {'field': 'campaign_p', 'headerName': 'SC', 'width': 100,
                    "cellStyle": {'textAlign': 'center'}},
        {'field': 'courtesy_car_p', 'headerName': 'CC', 'width': 100,
                    "cellStyle": {'textAlign': 'center'}},
        {'field': 'trp_2_p', 'headerName': 'TRP 2', 'width': 100,
                    "cellStyle": {'textAlign': 'center'}},
        {'field': 'sws_p', 'headerName': 'SWS', 'width': 100,
                    "cellStyle": {'textAlign': 'center'}},
        {'field': 'dowt_p', 'headerName': 'DWC', 'width': 100,
                    "cellStyle": {'textAlign': 'center'}},
        {'field': 'total_points', 'headerName': 'Total points', 'width': 100,
                    "cellStyle": {'textAlign': 'center'}}
        ]
    table = dag.AgGrid(
        rowData=table_month.to_dict('records'),
        columnDefs=columnDefs,
        defaultColDef={'filter': True,
                       "headerClass": 'center-aligned-header',
                       'wrapHeaderText': True,
                       'autoHeaderHeight': True,
                       'cellStyle': {'fontSize': '13px'}},
        dashGridOptions={'animateRows': False, 'pagination':True},
        className='ag-theme-alpine'

        )

# table of data

    table_month_data = tab_top_dealers_data.query('year == @year and month == @month').sort_values(by='total_points',
                                                                      ascending=False)[:200]
    table_month_data = table_month_data.drop(['year', 'month', 'total_points'], axis=1)
  
    
    
    columnDefs_ = [
        {'field': 'dealer_name', 'headerName': 'Dealer name', 'width': 200},
        {'field': 'dealer_code', 'headerName': 'Code', 'width': 100,
        "cellStyle": {'textAlign': 'center'}},
        {'field': 'warranty', 'headerName': 'Support', 'width': 110,
        "cellStyle": {'textAlign': 'center'}},
        {'field': 'uio', 'headerName': 'UIO', 
            'valueFormatter': {'function': "d3.format(',.0f')(params.value)"}, 'width': 100,
        "cellStyle": {'textAlign': 'center'}},
        {'field': 'm2_cost', 'headerName': 'M2 cost',
            'valueFormatter': {'function': "d3.format(',.0f')(params.value)"}, 'width': 100,
        "cellStyle": {'textAlign': 'center'}},
        {'field': 'm2_qty', 'headerName': 'M2 qty',
            'valueFormatter': {'function': "d3.format(',.0f')(params.value)"}, 'width': 100,
        "cellStyle": {'textAlign': 'center'}},                                       
        {'field': 'parts_cost', 'headerName': 'Parts cost',
            'valueFormatter': {'function': "d3.format(',.0f')(params.value)"}, 'width': 100,
        "cellStyle": {'textAlign': 'center'}},
        {'field': 'claim_qty', 'headerName': 'Claim qty',
            'valueFormatter': {'function': "d3.format(',.0f')(params.value)"}, 'width': 100,
        "cellStyle": {'textAlign': 'center'}},
        {'field': 'total_cost', 'headerName': 'Total cost',
            'valueFormatter': {'function': "d3.format(',.0f')(params.value)"}, 'width': 100,
        "cellStyle": {'textAlign': 'center'}},
        {'field': 'novs', 'headerName': 'NOVS',
            'valueFormatter': {'function': "d3.format(',.0f')(params.value)"}, 'width': 100,
        "cellStyle": {'textAlign': 'center'}},
        {'field': 'dm2pu', 'headerName': 'DM2PU',
            'valueFormatter': {'function': "d3.format(',.0f')(params.value)"}, 'width': 100,
        "cellStyle": {'textAlign': 'center'}},
        {'field': 'dcpu', 'headerName': 'DCPU',
            'valueFormatter': {'function': "d3.format(',.0f')(params.value)"}, 'width': 100,
        "cellStyle": {'textAlign': 'center'}},
        {'field': 'cpc', 'headerName': 'CPC',
            'valueFormatter': {'function': "d3.format(',.0f')(params.value)"}, 'width': 100,
        "cellStyle": {'textAlign': 'center'}},
        {'field': 'rvs', 'headerName': 'RVS',
            'valueFormatter': {'function': "d3.format(',.2f')(params.value)"}, 'width': 100,
        "cellStyle": {'textAlign': 'center'}},
        {'field': 'campaign', 'headerName': 'SC',
            'valueFormatter': {'function': "d3.format(',.0f')(params.value)"}, 'width': 100,
        "cellStyle": {'textAlign': 'center'}},
        {'field': 'courtesy_car', 'headerName': 'CC',
            'valueFormatter': {'function': "d3.format(',.0f')(params.value)"}, 'width': 100,
        "cellStyle": {'textAlign': 'center'}},
        {'field': 'sws', 'headerName': 'SWS qty',
             'valueFormatter': {'function': "d3.format(',.0f')(params.value)"}, 'width': 100,
        "cellStyle": {'textAlign': 'center'}},
        {'field': 'sws_ratio', 'headerName': 'SWS ratio',
             'valueFormatter': {'function': "d3.format(',.0f')(params.value)"},'width': 100,
        "cellStyle": {'textAlign': 'center'}},
        {'field': 'trp_2', 'headerName': 'TRP 2',
            'valueFormatter': {'function': "d3.format(',.0f')(params.value)"}, 'width': 100,
        "cellStyle": {'textAlign': 'center'}},
        {'field': 'dowt', 'headerName': 'DWC', 'width': 120,
        "cellStyle": {'textAlign': 'center'}}
        ]
    

        
    table_data = dag.AgGrid(
        rowData=table_month_data.to_dict('records'),
        columnDefs=columnDefs_,
        defaultColDef={'filter': True,
                       "headerClass": 'center-aligned-header',
                       'wrapHeaderText': True,
                       'autoHeaderHeight': True,
                       'cellStyle': {'fontSize': '13px'}},
        dashGridOptions={'animateRows': False, 'pagination':True},
        className='ag-theme-alpine')



    if active_tab == 'tab_1':
        return table_main, fig1, fig2, table
    elif active_tab == 'tab_2':
        return table_main, fig1, fig2, table_data
    elif active_tab == 'tab_3':
        return table_main, fig1, fig2, html.Div([
            dcc.Markdown("""
## KPI description: 

#### Numeric KPI's
* **DM2PU** dealer cost M2 per unit: DM2PU = M2(sublet cost)/ dealer UIO
* **DCPU** dealer parts cost per unit: DCPU = claimed parts/ dealer UIO
* **CPC** cost pet unit: CPC = Total warranty cost / claims qty
* **RVS** ratio of vehicle serviced: RVS = claims qty/ NOWS
* **Courtesy car** dealer courtesy car utilization
* **Service campaign** dealer recall and service campaign results
* **SWS** - dealer smart warranty system usage
* **TRP** - dealer technician sertification result

#### Category KPI's
* **DWC** - dealer warranty certification
""")
        ])


@app.callback(Output('dealer_chart_points', 'figure'),
              Output('kpi_chart', 'figure'),
              Output('other_chart', 'figure'),
              Input('code_dropdown', 'value'),
              Input('indicator_dropdown', 'value'),
              Input('dealer_indicator_dropdown', 'value')
             )
def display_bar(dealer, indicator_kpi, indicator_other):
    if (not dealer) or (not indicator_kpi) or (not indicator_other):
        raise PreventUpdate
    df = dash_tab.query('dealer_code == @dealer and mobis_code != @freeze_rs')
    fig1 = px.bar(df,
                x='month',
                y=df['total_points'],
                title=str(dealer) + ' total points',
                text_auto=',.0f',
                height=350,
                color_discrete_sequence=['orange']
                 )
    fig1.layout.xaxis.title = None
    fig1.layout.yaxis.title = 'Total points'
    
    if indicator_kpi == 'rvs':
        fig2 = px.bar(df,
                x='month',
                y=[indicator_kpi, indicator_kpi + '_reg'],
                barmode='group',
                title=str(dealer) + ' ' + indicator_kpi + ' trend',
                text_auto=',.2f',
                height=350,
                color_discrete_sequence=['orange', 'lightsteelblue']
                 )
        fig2.layout.xaxis.title = None
        fig2.layout.yaxis.title = indicator_kpi
        fig2.update_layout(
        legend=dict(
            orientation='h',
            yanchor='bottom',
            y=1.02
        ),
        legend_title_text='KPI'
        )
    else:
        fig2 = px.bar(df,
                x='month',
                y=[indicator_kpi, indicator_kpi + '_reg'],
                barmode='group',
                title=str(dealer) + ' ' + indicator_kpi + ' trend',
                text_auto=',.0f',
                height=350,
                color_discrete_sequence=['orange', 'lightsteelblue']
                 )
        fig2.layout.xaxis.title = None
        fig2.layout.yaxis.title = indicator_kpi
        fig2.update_layout(
        legend=dict(
            orientation='h',
            yanchor='bottom',
            y=1.02
        ),
        legend_title_text='KPI'
        )    
    
    fig3 = px.bar(df,
                x='month',
                y=indicator_other,
                title=str(dealer) + ' ' + indicator_other + ' trend',
                text_auto=',.0f',
                height=350,
                color_discrete_sequence=['lightsteelblue']
                 )
    fig3.layout.xaxis.title = None
    fig3.layout.yaxis.title = indicator_other
                  
                
    return fig1, fig2, fig3

@app.callback(Output('grid-callback-example', 'children'),
              Output('dealer_chart', 'figure'),
              Output('support_chart', 'figure'),              
#              Output('table_dealers_output', 'children'),
#              Output('table_dealers_data_output', 'children'),
              Output('content', 'children'),
              Input('year_dropdown', 'value'),
              Input('month_dropdown', 'value'),
              Input('tabs', 'active_tab')
             )



def plot_dealers_by_points(year, month, active_tab):
    sum_tab = dash_tab.query('year == @year and month == @month and mobis_code != @freeze_rs')
    uio = sum_tab['uio'].sum()
    novs = sum_tab['novs'].sum()
    total = sum_tab['total_cost'].sum()
    qty = sum_tab['claim_qty'].sum()
    m2 = sum_tab['m2_cost'].sum()
    m2_qty = sum_tab['m2_qty'].sum()
    camp = sum_tab['campaign'].mean()/100
    data = {'UIO': [uio], 'NOVS': [novs], 'Total amount': [total],
            'Claims qty': [qty], 'M2 amount': [m2], 'M2 qty': [m2_qty], 'Campaign': [camp]}
    df_tab = pd.DataFrame(data)
    
    
    columnDefs_main = [
        {'field': 'UIO', 'headerName': 'UIO', 
            'valueFormatter': {'function': "d3.format(',.0f')(params.value)"}, 'width': 200,
        "cellStyle": {'textAlign': 'center'}},
        {'field': 'NOVS', 'headerName': 'NOVS',
            'valueFormatter': {'function': "d3.format(',.0f')(params.value)"}, 'width': 200,
        "cellStyle": {'textAlign': 'center'}},
        {'field': 'Total amount', 'headerName': 'TOTAL AMOUNT (RUB)',
            'valueFormatter': {'function': "d3.format(',.0f')(params.value)"}, 'width': 200,
        "cellStyle": {'textAlign': 'center'}},                                       
        {'field': 'Claims qty', 'headerName': 'CLAIM QUANTITY',
            'valueFormatter': {'function': "d3.format(',.0f')(params.value)"}, 'width': 200,
        "cellStyle": {'textAlign': 'center'}},
        {'field': 'M2 amount', 'headerName': 'M2 AMOUNT (RUB)',
            'valueFormatter': {'function': "d3.format(',.0f')(params.value)"}, 'width': 200,
        "cellStyle": {'textAlign': 'center'}},
        {'field': 'M2 qty', 'headerName': 'M2 QUANTITY',
            'valueFormatter': {'function': "d3.format(',.0f')(params.value)"}, 'width': 200,
        "cellStyle": {'textAlign': 'center'}},
        {'field': 'Campaign', 'headerName': 'CAMPAIGN',
            'valueFormatter': {'function': "d3.format('.0%')(params.value)"}, 'width': 200,
        "cellStyle": {'textAlign': 'center'}}
        ]
    

    
    
    table_main = dag.AgGrid(
        rowData=df_tab.to_dict('records'),
        columnDefs=columnDefs_main,
        defaultColDef={
                       'headerClass': 'center-aligned-header',
                       'wrapHeaderText': True,
                       'autoHeaderHeight': False},
        dashGridOptions={'animateRows': False, 'pagination':False,
                         'rowHeight': 55,
                         'headerHeight': 55},
        rowStyle = {'backgroundColor': 'white', 'fontSize': '22px', "color": '#005792',
                   'padding': '15px'},
        columnSize="sizeToFit",
        className='ag-theme-custom-theme',
        style={"height": 110, "width": 1400}

        )

    
    
    
    
    month_df =\
    tab_top_dealers.query('year == @year and month == @month').sort_values(by='total_points', ascending=False)[:10]
    fig1 = px.bar(                 
    x=month_df['total_points'],
    y=month_df['dealer_name'],
    text=month_df['total_points'],
    height=400,
#    width=700,
    title=f'Top 10 dealers by penalty points in {month}',
    orientation='h',
#    color=month_df['total_points'],
    color_discrete_sequence=['lightsteelblue']
    
)
    fig1.update_layout(yaxis={'categoryorder': 'total ascending'})
    fig1.layout.xaxis.title = 'Total points'
    fig1.layout.yaxis.title = None
    fig1.update_coloraxes(showscale=False)
    
    
    month_support =\
    dash_tab.query('year == @year and month == @month and mobis_code != @freeze_rs').pivot_table(
        index=['warranty'], values='total_points', aggfunc='mean').reset_index()
    
    fig2 = px.bar(                 
    x=month_support['total_points'],
    y=month_support['warranty'],
    text=month_support['total_points'],
    height=400,
#    width=700,
    text_auto='.1f',
    title=f'Top penalty points by support in {month}',
    orientation='h',
    color=month_support['warranty'],
    color_discrete_sequence=px.colors.qualitative.Pastel1
    
)
    fig2.update_layout(yaxis={'categoryorder':'total ascending'}, showlegend=False)
    fig2.layout.xaxis.title = 'Total points'
    fig2.layout.yaxis.title = None
    fig2.update_coloraxes(showscale=False)
    
    
# table of points

    table_month = tab_top_dealers.query('year == @year and month == @month').sort_values(by='total_points',
                                                                      ascending=False)[:200]
    table_month = table_month.drop(['year', 'month'], axis=1)
    
    
    columnDefs = [
        {'field': 'dealer_name', 'headerName': 'Dealer name', 'width': 200},
        {'field': 'dealer_code', 'headerName': 'Code', 'width': 100,
                    "cellStyle": {'textAlign': 'center'}},
        {'field': 'warranty', 'headerName': 'Support', 'width': 110,
                    "cellStyle": {'textAlign': 'center'}},
        {'field': 'dm2pu_p', 'headerName': 'DM2PU', 'width': 100, "cellStyle": {'textAlign': 'center'},
        'headerTooltip': 'Dealer M2 cost per unit'},
        {'field': 'dcpu_p', 'headerName': 'DCPU', 'width': 100,
                    "cellStyle": {'textAlign': 'center'}},
        {'field': 'cpc_p', 'headerName': 'CPC', 'width': 100,
                    "cellStyle": {'textAlign': 'center'}},
        {'field': 'rvs_p', 'headerName': 'RVS', 'width': 100,
                    "cellStyle": {'textAlign': 'center'}},
        {'field': 'campaign_p', 'headerName': 'SC', 'width': 100,
                    "cellStyle": {'textAlign': 'center'}},
        {'field': 'courtesy_car_p', 'headerName': 'CC', 'width': 100,
                    "cellStyle": {'textAlign': 'center'}},
        {'field': 'trp_2_p', 'headerName': 'TRP 2', 'width': 100,
                    "cellStyle": {'textAlign': 'center'}},
        {'field': 'sws_p', 'headerName': 'SWS', 'width': 100,
                    "cellStyle": {'textAlign': 'center'}},
        {'field': 'dowt_p', 'headerName': 'DWC', 'width': 100,
                    "cellStyle": {'textAlign': 'center'}},
        {'field': 'total_points', 'headerName': 'Total points', 'width': 100,
                    "cellStyle": {'textAlign': 'center'}}
        ]
    table = dag.AgGrid(
        rowData=table_month.to_dict('records'),
        columnDefs=columnDefs,
        defaultColDef={'filter': True,
                       "headerClass": 'center-aligned-header',
                       'wrapHeaderText': True,
                       'autoHeaderHeight': True,
                       'cellStyle': {'fontSize': '13px'}},
        dashGridOptions={'animateRows': False, 'pagination':True},
        className='ag-theme-alpine'

        )

# table of data

    table_month_data = tab_top_dealers_data.query('year == @year and month == @month').sort_values(by='total_points',
                                                                      ascending=False)[:200]
    table_month_data = table_month_data.drop(['year', 'month', 'total_points'], axis=1)
  
    
    
    columnDefs_ = [
        {'field': 'dealer_name', 'headerName': 'Dealer name', 'width': 200},
        {'field': 'dealer_code', 'headerName': 'Code', 'width': 100,
        "cellStyle": {'textAlign': 'center'}},
        {'field': 'warranty', 'headerName': 'Support', 'width': 110,
        "cellStyle": {'textAlign': 'center'}},
        {'field': 'uio', 'headerName': 'UIO', 
            'valueFormatter': {'function': "d3.format(',.0f')(params.value)"}, 'width': 100,
        "cellStyle": {'textAlign': 'center'}},
        {'field': 'm2_cost', 'headerName': 'M2 cost',
            'valueFormatter': {'function': "d3.format(',.0f')(params.value)"}, 'width': 100,
        "cellStyle": {'textAlign': 'center'}},
        {'field': 'm2_qty', 'headerName': 'M2 qty',
            'valueFormatter': {'function': "d3.format(',.0f')(params.value)"}, 'width': 100,
        "cellStyle": {'textAlign': 'center'}},                                       
        {'field': 'parts_cost', 'headerName': 'Parts cost',
            'valueFormatter': {'function': "d3.format(',.0f')(params.value)"}, 'width': 100,
        "cellStyle": {'textAlign': 'center'}},
        {'field': 'claim_qty', 'headerName': 'Claim qty',
            'valueFormatter': {'function': "d3.format(',.0f')(params.value)"}, 'width': 100,
        "cellStyle": {'textAlign': 'center'}},
        {'field': 'total_cost', 'headerName': 'Total cost',
            'valueFormatter': {'function': "d3.format(',.0f')(params.value)"}, 'width': 100,
        "cellStyle": {'textAlign': 'center'}},
        {'field': 'novs', 'headerName': 'NOVS',
            'valueFormatter': {'function': "d3.format(',.0f')(params.value)"}, 'width': 100,
        "cellStyle": {'textAlign': 'center'}},
        {'field': 'dm2pu', 'headerName': 'DM2PU',
            'valueFormatter': {'function': "d3.format(',.0f')(params.value)"}, 'width': 100,
        "cellStyle": {'textAlign': 'center'}},
        {'field': 'dcpu', 'headerName': 'DCPU',
            'valueFormatter': {'function': "d3.format(',.0f')(params.value)"}, 'width': 100,
        "cellStyle": {'textAlign': 'center'}},
        {'field': 'cpc', 'headerName': 'CPC',
            'valueFormatter': {'function': "d3.format(',.0f')(params.value)"}, 'width': 100,
        "cellStyle": {'textAlign': 'center'}},
        {'field': 'rvs', 'headerName': 'RVS',
            'valueFormatter': {'function': "d3.format(',.2f')(params.value)"}, 'width': 100,
        "cellStyle": {'textAlign': 'center'}},
        {'field': 'campaign', 'headerName': 'SC',
            'valueFormatter': {'function': "d3.format(',.0f')(params.value)"}, 'width': 100,
        "cellStyle": {'textAlign': 'center'}},
        {'field': 'courtesy_car', 'headerName': 'CC',
            'valueFormatter': {'function': "d3.format(',.0f')(params.value)"}, 'width': 100,
        "cellStyle": {'textAlign': 'center'}},
        {'field': 'sws', 'headerName': 'SWS qty',
             'valueFormatter': {'function': "d3.format(',.0f')(params.value)"}, 'width': 100,
        "cellStyle": {'textAlign': 'center'}},
        {'field': 'sws_ratio', 'headerName': 'SWS ratio',
             'valueFormatter': {'function': "d3.format(',.0f')(params.value)"},'width': 100,
        "cellStyle": {'textAlign': 'center'}},
        {'field': 'trp_2', 'headerName': 'TRP 2',
            'valueFormatter': {'function': "d3.format(',.0f')(params.value)"}, 'width': 100,
        "cellStyle": {'textAlign': 'center'}},
        {'field': 'dowt', 'headerName': 'DWC', 'width': 120,
        "cellStyle": {'textAlign': 'center'}}
        ]
    

        
    table_data = dag.AgGrid(
        rowData=table_month_data.to_dict('records'),
        columnDefs=columnDefs_,
        defaultColDef={'filter': True,
                       "headerClass": 'center-aligned-header',
                       'wrapHeaderText': True,
                       'autoHeaderHeight': True,
                       'cellStyle': {'fontSize': '13px'}},
        dashGridOptions={'animateRows': False, 'pagination':True},
        className='ag-theme-alpine')



    if active_tab == 'tab_1':
        return table_main, fig1, fig2, table
    elif active_tab == 'tab_2':
        return table_main, fig1, fig2, table_data
    elif active_tab == 'tab_3':
        return table_main, fig1, fig2, html.Div([
            dcc.Markdown("""
## KPI description: 

#### Numeric KPI's
* **DM2PU** dealer cost M2 per unit: DM2PU = M2(sublet cost)/ dealer UIO
* **DCPU** dealer parts cost per unit: DCPU = claimed parts/ dealer UIO
* **CPC** cost pet unit: CPC = Total warranty cost / claims qty
* **RVS** ratio of vehicle serviced: RVS = claims qty/ NOWS
* **Courtesy car** dealer courtesy car utilization
* **Service campaign** dealer recall and service campaign results
* **SWS** - dealer smart warranty system usage
* **TRP** - dealer technician sertification result

#### Category KPI's
* **DWC** - dealer warranty certification
""")
        ])


@app.callback(Output('dealer_chart_points', 'figure'),
              Output('kpi_chart', 'figure'),
              Output('other_chart', 'figure'),
              Input('code_dropdown', 'value'),
              Input('indicator_dropdown', 'value'),
              Input('dealer_indicator_dropdown', 'value')
             )
def display_bar(dealer, indicator_kpi, indicator_other):
    if (not dealer) or (not indicator_kpi) or (not indicator_other):
        raise PreventUpdate
    df = dash_tab.query('dealer_code == @dealer and mobis_code != @freeze_rs')
    fig1 = px.bar(df,
                x='month',
                y=df['total_points'],
                title=str(dealer) + ' total points',
                text_auto=',.0f',
                height=350,
                color_discrete_sequence=['orange']
                 )
    fig1.layout.xaxis.title = None
    fig1.layout.yaxis.title = 'Total points'
    
    if indicator_kpi == 'rvs':
        fig2 = px.bar(df,
                x='month',
                y=[indicator_kpi, indicator_kpi + '_reg'],
                barmode='group',
                title=str(dealer) + ' ' + indicator_kpi + ' trend',
                text_auto=',.2f',
                height=350,
                color_discrete_sequence=['orange', 'lightsteelblue']
                 )
        fig2.layout.xaxis.title = None
        fig2.layout.yaxis.title = indicator_kpi
        fig2.update_layout(
        legend=dict(
            orientation='h',
            yanchor='bottom',
            y=1.02
        ),
        legend_title_text='KPI'
        )
    else:
        fig2 = px.bar(df,
                x='month',
                y=[indicator_kpi, indicator_kpi + '_reg'],
                barmode='group',
                title=str(dealer) + ' ' + indicator_kpi + ' trend',
                text_auto=',.0f',
                height=350,
                color_discrete_sequence=['orange', 'lightsteelblue']
                 )
        fig2.layout.xaxis.title = None
        fig2.layout.yaxis.title = indicator_kpi
        fig2.update_layout(
        legend=dict(
            orientation='h',
            yanchor='bottom',
            y=1.02
        ),
        legend_title_text='KPI'
        )    
    
    fig3 = px.bar(df,
                x='month',
                y=indicator_other,
                title=str(dealer) + ' ' + indicator_other + ' trend',
                text_auto=',.0f',
                height=350,
                color_discrete_sequence=['lightsteelblue']
                 )
    fig3.layout.xaxis.title = None
    fig3.layout.yaxis.title = indicator_other
                  
                
    return fig1, fig2, fig3

if __name__ == '__main__':
    app.run_server(debug=False)

