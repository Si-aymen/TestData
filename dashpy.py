import dash
from dash import dcc, html, dash_table
import plotly.express as px
import pandas as pd
import json
import os

json_file = "data/RESULTS/results_20250219.json"

if os.path.exists(json_file):
    with open(json_file, "r", encoding="utf-8") as f:
        data = json.load(f)
else:
    data = {"files_with_errors": {}, "Summary": {}, "Errors": {}}


errors_by_file = data.get("files_with_errors", {})


error_types = ["champs obligatoires", "longueur", "type", "entete"]


df_errors_by_file = pd.DataFrame.from_dict(errors_by_file, orient="index").fillna(0)


df_errors_by_file = df_errors_by_file.reindex(columns=error_types, fill_value=0)

# Convertir en format utilisable par Dash DataTable
df_errors_by_file.reset_index(inplace=True)
df_errors_by_file.rename(columns={"index": "Fichier"}, inplace=True)

# Créer un DataFrame pour le graphique global des erreurs
df_summary_grouped = pd.DataFrame.from_dict(data.get("Errors", {}), orient="index", columns=["Nombre"])
df_summary_grouped.reset_index(inplace=True)
df_summary_grouped.rename(columns={"index": "Type d'erreur"}, inplace=True)


app = dash.Dash(__name__)

app.layout = html.Div([
    html.H1("Dashboard des erreurs de fichiers CSV", style={'textAlign': 'center', 'color': '#333'}),
    
    html.Div([
        dcc.Graph(
            figure=px.pie(df_summary_grouped, names="Type d'erreur", values="Nombre", title="Répartition des erreurs",
                           color_discrete_sequence=px.colors.sequential.RdBu)
        ),
        dcc.Graph(
            figure=px.bar(df_summary_grouped, x="Type d'erreur", y="Nombre", title="Nombre d'erreurs par type",
                          color="Type d'erreur", text_auto=True, color_discrete_sequence=px.colors.sequential.Plasma)
        )
    ], style={'display': 'flex', 'justifyContent': 'space-around'}),
    
    html.H2("Détail des erreurs par fichier", style={'textAlign': 'center', 'marginTop': '20px'}),
    
    dash_table.DataTable(
        id='table-errors',
        columns=[{"name": col, "id": col} for col in df_errors_by_file.columns],
        data=df_errors_by_file.to_dict('records'),
        page_size=10,
        style_table={'overflowX': 'auto', 'border': '1px solid #ddd', 'padding': '10px'},
        style_header={'backgroundColor': '#6d071a', 'color': 'white', 'fontWeight': 'bold', 'textAlign': 'center'},
        style_cell={'textAlign': 'center', 'padding': '8px', 'border': '1px solid #ddd'},
        style_data_conditional=[
            {'if': {'row_index': 'odd'}, 'backgroundColor': '#f2f2f2'},
            {'if': {'column_id': 'Fichier'}, 'textAlign': 'left', 'fontWeight': 'bold'}
        ]
    )
])

if __name__ == "__main__":
    app.run_server(debug=True)
