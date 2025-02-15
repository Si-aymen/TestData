import dash
from dash import dcc, html, dash_table
import pandas as pd
import plotly.express as px
import json

# Load the JSON file containing test results
json_path = "data/Mandatory_columns_failure/test_results.json"  # Update this path if needed
with open(json_path, "r", encoding="utf-8") as file:
    test_results = json.load(file)

# Convert the JSON data into a Pandas DataFrame
df = pd.DataFrame(test_results)

# Calculate summary statistics for the dashboard
total_files = len(df)
passed_files = len(df[df["status"] == "Passed"])
failed_files = len(df[df["status"] == "Failed"])

# Create a pie chart to visualize passed vs. failed files
pie_chart = px.pie(
    df,
    names="status",
    title="Proportion of Passed vs. Failed Files",
    hole=0.3,
    color_discrete_sequence=["green", "red"],
)

# Initialize the Dash application
app = dash.Dash(__name__)

# Define the layout of the dashboard
app.layout = html.Div(
    style={
        "padding": "20px",
        "fontFamily": "Arial, sans-serif",
        "backgroundColor": "#f4f4f4",
        "textAlign": "center",
    },
    children=[
        # Logo
        html.Img(src="Logo-tessi-2019-bleu-1000x557.jpg", style={"width": "200px", "marginBottom": "20px"}),

        # Title section
        html.H1("Test Results CSV Files", style={"color": "#003366"}),
        html.Hr(style={"borderTop": "2px solid #003366"}),

        # Summary statistics section
        html.Div(
            style={
                "display": "flex",
                "justifyContent": "center",
                "gap": "50px",
                "marginBottom": "20px",
            },
            children=[
                html.Div([
                    html.H3("Total Files Processed", style={"color": "#003366"}),
                    html.P(f"{total_files}", style={"fontSize": "20px", "fontWeight": "bold"}),
                ], style={"background": "white", "padding": "20px", "borderRadius": "10px", "boxShadow": "0 0 10px rgba(0,0,0,0.1)"}),
                html.Div([
                    html.H3("Passed Files", style={"color": "green"}),
                    html.P(f"{passed_files}", style={"fontSize": "20px", "fontWeight": "bold"}),
                ], style={"background": "white", "padding": "20px", "borderRadius": "10px", "boxShadow": "0 0 10px rgba(0,0,0,0.1)"}),
                html.Div([
                    html.H3("Failed Files", style={"color": "red"}),
                    html.P(f"{failed_files}", style={"fontSize": "20px", "fontWeight": "bold"}),
                ], style={"background": "white", "padding": "20px", "borderRadius": "10px", "boxShadow": "0 0 10px rgba(0,0,0,0.1)"}),
            ],
        ),
        html.Hr(style={"borderTop": "2px solid #003366"}),

        # Pie chart section
        html.H3("Passed vs. Failed Files", style={"color": "#003366"}),
        dcc.Graph(figure=pie_chart),
        html.Hr(style={"borderTop": "2px solid #003366"}),

        # Failed files table section with pagination
        html.H3("Failed Files", style={"color": "red"}),
        dash_table.DataTable(
            columns=[{"name": col, "id": col} for col in df.columns],
            data=df[df["status"] == "Failed"].to_dict("records"),
            style_table={"overflowX": "auto"},
            style_cell={"textAlign": "left", "padding": "10px"},
            style_header={
                "backgroundColor": "#ffcccc",
                "fontWeight": "bold",
                "padding": "10px",
            },
            page_size=10,  # Pagination
        ),
        html.Hr(style={"borderTop": "2px solid #003366"}),

        # Passed files table section with pagination
        html.H3("Passed Files", style={"color": "green"}),
        dash_table.DataTable(
            columns=[{"name": col, "id": col} for col in df.columns],
            data=df[df["status"] == "Passed"].to_dict("records"),
            style_table={"overflowX": "auto"},
            style_cell={"textAlign": "left", "padding": "10px"},
            style_header={
                "backgroundColor": "#ccffcc",
                "fontWeight": "bold",
                "padding": "10px",
            },
            page_size=10,  # Pagination
        ),
    ],
)

# Run the Dash application
if __name__ == "__main__":
    app.run_server(debug=True)
