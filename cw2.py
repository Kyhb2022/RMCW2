import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np

# Load and prepare data
data = pd.read_csv('Results_21MAR2022_nokcaladjust.csv')
columns_to_use = [
    'diet_group', 'mean_ghgs', 'mean_land', 'mean_watscar', 'mean_eut',
    'mean_ghgs_ch4', 'mean_ghgs_n2o', 'mean_bio', 'mean_watuse', 'mean_acid',
    'sex', 'age_group'
]
data = data[columns_to_use]
data[columns_to_use[1:10]] = data[columns_to_use[1:10]].apply(pd.to_numeric, errors='coerce')

# Define diet group labels
diet_labels = {
    'meat100': 'meat 100+',
    'meat': 'meat50-99',
    'meat50': 'meat <50',
    'fish': 'Fish',
    'veggie': 'Vegetarian',
    'vegan': 'Vegan'
}
data['diet_group'] = data['diet_group'].map(diet_labels)

# Define environmental impact labels
impact_labels = {
    'mean_ghgs': 'Greenhouse Gases',
    'mean_land': 'Land Use',
    'mean_watscar': 'Water Scarcity',
    'mean_eut': 'Eutrophication',
    'mean_ghgs_ch4': 'GHG CH4',
    'mean_ghgs_n2o': 'GHG N2O',
    'mean_bio': 'Biodiversity',
    'mean_acid': 'Acidification',
    'mean_watuse': 'Water Usage'
}

color_dict = {
    'meat50-99': 'rgba(255, 99, 132, 1)',
    'meat 100+': 'rgba(54, 162, 235, 1)',
    'meat <50': 'rgba(255, 206, 86, 1)',
    'Fish': 'rgba(75, 192, 192, 1)',
    'Vegetarian': 'rgba(153, 102, 255, 1)',
    'Vegan': 'rgba(255, 159, 64, 1)'
}
# Setup the Dash app
app = dash.Dash(__name__)

# Define the layout of the app
app.layout = html.Div([
    html.Label("Select Diet Groups:"),
    dcc.Checklist(
        id='diet-group-checklist',
        options=[{'label': i, 'value': i} for i in diet_labels.values()],
        value=list(diet_labels.values()),
        inline=True
    ),
    html.Label("Select Gender:"),
    dcc.Dropdown(
        id='gender-dropdown',
        options=[{'label': i, 'value': i} for i in data['sex'].unique()],
        value=data['sex'].unique(),
        multi=True
    ),
    html.Label("Select Age Group:"),
    dcc.Dropdown(
        id='age-group-dropdown',
        options=[{'label': i, 'value': i} for i in data['age_group'].unique()],
        value=data['age_group'].unique(),
        multi=True
    ),
    dcc.RadioItems(
        id='graph-type',
        options=[
            {'label': 'Radar Graph', 'value': 'radar'},
            {'label': 'Treemap', 'value': 'treemap'}
        ],
        value='radar',
        labelStyle={'display': 'inline-block'}
    ),
    dcc.Graph(id='main-graph')
])

# Define the callback to update the graph based on the selected graph type
@app.callback(
    Output('main-graph', 'figure'),
    [Input('diet-group-checklist', 'value'),
     Input('gender-dropdown', 'value'),
     Input('age-group-dropdown', 'value'),
     Input('graph-type', 'value')]
)
def update_graph(selected_diets, selected_genders, selected_ages, graph_type):
    filtered_data = data[
        (data['diet_group'].isin(selected_diets)) &
        (data['sex'].isin(selected_genders)) &
        (data['age_group'].isin(selected_ages))
    ]

    if graph_type == 'radar':
        env_impact_totals = filtered_data.groupby('diet_group')[columns_to_use[1:10]].mean().reset_index()
        
        # Normalize data
        for col in columns_to_use[1:10]:
            max_value = env_impact_totals[col].max()
            if max_value > 0:
                env_impact_totals[col] = env_impact_totals[col] / max_value

        # Map technical names to readable labels
        readable_labels = [impact_labels[col] for col in columns_to_use[1:10]] + [impact_labels[columns_to_use[1]]]

        # Create radar chart
        fig = go.Figure()
        
        for diet in selected_diets:
            diet_data = env_impact_totals[env_impact_totals['diet_group'] == diet]
            r_values = diet_data.iloc[0, 1:10].tolist() + [diet_data.iloc[0, 1]]  
            theta_values = readable_labels
            fig.add_trace(go.Scatterpolar(
                r=r_values,
                theta=theta_values,
                fill='toself',
                fillcolor= 'rgba(68, 206, 246, 0.2)',
                line=dict(
                    color=color_dict[diet],
                    width=1
                ),
                name=diet,
                marker=dict(
                    size=0,
                    color='rgba(0,0,0,0)'  # Set marker color to transparent
                )
            )
            )
        
        fig.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, 1.3],
                    color='grey',
                    gridcolor='silver'
                ),
                angularaxis=dict(
                    color='grey',
                    gridcolor='lightgrey'
                ),
                bgcolor="white"
            ),
            title={
                'text': 'Environmental Impact by Diet Group',
                'y':0.9,
                'x':0.5,
                'xanchor': 'center',
                'yanchor': 'top'
            },
            font=dict(
                family="Arial, sans-serif",
                size=12,
                color="#333"
            ),
            legend=dict(
                title=dict(
                    text="Diet Groups"
                ),
                orientation="h",
                x=0.5,
                xanchor="center",
                y=-0.1
            )
        )
        

    elif graph_type == 'treemap':
            # Aggregate the environmental impact totals for filtered data
        env_impact_totals = filtered_data.groupby('diet_group')[columns_to_use[1:10]].sum().reset_index()
        
        # Normalize the environmental impact data
        for col in columns_to_use[1:10]:  
            total_sum = env_impact_totals[col].sum()
            if total_sum > 0:
                env_impact_totals[col] = env_impact_totals[col] / total_sum
            else:
                env_impact_totals[col] = 0  

        # Melt the data for the treemap visualization
        data_totals = env_impact_totals.melt(id_vars='diet_group', value_vars=columns_to_use[1:10], var_name='Impact', value_name='Contribution')
        # Map the technical column names to readable labels
        data_totals['Impact'] = data_totals['Impact'].map(impact_labels)

        # Create the treemap
        fig = px.treemap(
            data_totals,
            path=['Impact', 'diet_group'],
            values='Contribution',
            color='Contribution',
            color_continuous_scale='Blues',
            title='Normalized Treemap of Dietary Habits Contribution to Environmental Impact by Age and Gender'
        )
        # Set the layout dimensions
        fig.update_layout(
            width=1000,  
            height=600,  
        )
        

    fig.update_layout(transition_duration=500)
    return fig

# Run the app
if __name__ == '__main__':
    app.run_server(debug=True)
