import dash
from dash import dcc, html, dash_table
import pandas as pd
import json
import plotly.express as px
from collections import Counter

# Load JSON files
no_match_path = "data/NO_MATCH/file_test_results.json"
mandatory_failure_path = "data/Mandatory_columns_failure/test_results.json"

def load_json(path):
    try:
        with open(path, "r", encoding="utf-8") as file:
            return json.load(file)
    except FileNotFoundError:
        return []

# Load JSON data into DataFrames
no_match_results = load_json(no_match_path)
mandatory_failure_results = load_json(mandatory_failure_path)

df_no_match = pd.DataFrame(no_match_results) if no_match_results else pd.DataFrame(columns=["filename", "status", "reason"])
df_mandatory_failure = pd.DataFrame(mandatory_failure_results) if mandatory_failure_results else pd.DataFrame(columns=["filename", "status", "reason"])

# Filter failed results
df_no_match_failed = df_no_match[df_no_match["status"] == "Failed"]
df_mandatory_failure_failed = df_mandatory_failure[df_mandatory_failure["status"] == "Failed"]

# Combine all results
df_combined = pd.concat([df_no_match, df_mandatory_failure])

# Calculate statistics
total_tests = len(df_combined)
passed_tests = len(df_combined[df_combined["status"] == "Passed"])
failed_tests = len(df_combined[df_combined["status"] == "Failed"])
pass_rate = (passed_tests / total_tests * 100) if total_tests else 0
failure_rate = (failed_tests / total_tests * 100) if total_tests else 0

# Determine most common failure reason
failure_reasons = df_combined[df_combined["status"] == "Failed"]["reason"].dropna().tolist()
most_common_failure, most_common_failure_count = Counter(failure_reasons).most_common(1)[0] if failure_reasons else ("N/A", 0)
most_common_failure_percent = (most_common_failure_count / failed_tests * 100) if failed_tests else 0

# Calculate statistics for each dataset
def calculate_stats(df, name):
    total_files = len(df)
    passed_files = len(df[df["status"] == "Passed"])
    failed_files = len(df[df["status"] == "Failed"])
    pass_rate = (passed_files / total_files * 100) if total_files else 0
    failure_rate = (failed_files / total_files * 100) if total_files else 0
    return {
        "name": name,
        "total_files": total_files,
        "passed_files": passed_files,
        "failed_files": failed_files,
        "pass_rate": pass_rate,
        "failure_rate": failure_rate,
    }

no_match_stats = calculate_stats(df_no_match, "NO_MATCH")
mandatory_failure_stats = calculate_stats(df_mandatory_failure, "Mandatory Columns Failure")

# Failure reasons distribution
failure_reasons_distribution = Counter(failure_reasons)
failure_reasons_df = pd.DataFrame(failure_reasons_distribution.items(), columns=["Reason", "Count"])
failure_reasons_df["Percentage"] = (failure_reasons_df["Count"] / failed_tests * 100) if failed_tests else 0

# Create pie chart for Passed vs. Failed
pie_chart = px.pie(
    df_combined,
    names="status",
    title="Proportion of Passed vs. Failed Files",
    hole=0.3,
    color_discrete_sequence=["darkblue", "grey"],
)



# Initialize Dash app
app = dash.Dash(__name__)

# Define layout
app.layout = html.Div(style={"padding": "20px", "fontFamily": "Arial, sans-serif", "backgroundColor": "#f4f4f4", "textAlign": "center"}, 
children=[
    html.Img(src="assets/Logo.jpg", style={"width": "200px", "marginBottom": "20px"}),
    html.H1("Test Results CSV Files", style={"color": "#003366"}),
    html.Hr(style={"borderTop": "2px solid #003366"}),

    # Pie chart for Proportion of Passed vs. Failed Files
    dcc.Graph(
        id="pie-chart",
        figure=pie_chart,
        style={"marginBottom": "30px"}
    ),

    # NO_MATCH Section
    html.H2(f"{no_match_stats['name']} - Failed Test Results", style={"color": "#003366"}),
    html.P(f"Total Failed Test Results: {len(df_no_match_failed)}", style={"color": "#003366", "fontSize": "16px", "fontWeight": "bold"}),  # Added line
    dash_table.DataTable(
        columns=[{"name": col, "id": col} for col in df_no_match_failed.columns],
        data=df_no_match_failed.to_dict("records"),
        page_size=10,
        style_table={"overflowX": "auto"},
        style_cell={"textAlign": "left", "padding": "10px"},
        style_header={"backgroundColor": "#003366", "color": "white", "fontWeight": "bold"},
    ),
    html.Hr(),

    # Mandatory Columns Failure Section
    html.H2(f"{mandatory_failure_stats['name']} - Failed Test Results", style={"color": "#003366"}),
    html.P(f"Total Failed Test Results: {len(df_mandatory_failure_failed)}", style={"color": "#003366", "fontSize": "16px", "fontWeight": "bold"}),  # Added line
    dash_table.DataTable(
        columns=[{"name": col, "id": col} for col in df_mandatory_failure_failed.columns],
        data=df_mandatory_failure_failed.to_dict("records"),
        page_size=10,
        style_table={"overflowX": "auto"},
        style_cell={"textAlign": "left", "padding": "10px"},
        style_header={"backgroundColor": "#003366", "color": "white", "fontWeight": "bold"},
    ),
    html.Hr(),

    # Summary statistics table
    html.H2(f"Summary Statistics", style={"color": "#003366"}),
    dash_table.DataTable(
        columns=[
            {"name": "Metric", "id": "metric"},
            {"name": "Value", "id": "value"}
        ],
        data=[
            {"metric": "Total Tests Processed", "value": total_tests},
            {"metric": "Passed Tests", "value": passed_tests},
            {"metric": "Failed Tests", "value": failed_tests},
            {"metric": "Pass Rate", "value": f"{pass_rate:.2f}%"},
            {"metric": "Failure Rate", "value": f"{failure_rate:.2f}%"},
            {"metric": "Most Common Failure", "value": most_common_failure},
            {"metric": "Failure Percentage", "value": f"{most_common_failure_percent:.2f}%"}
        ],
        style_table={"marginBottom": "30px", "width": "60%", "margin": "auto"},
        style_header={"backgroundColor": "#003366", "color": "white", "fontWeight": "bold"},
        style_cell={"textAlign": "center", "padding": "10px"},
    ),

    # Dataset-Specific Statistics
    html.H2(f"Dataset-Specific Statistics", style={"color": "#003366"}),
    dash_table.DataTable(
        columns=[
            {"name": "Dataset", "id": "dataset"},
            {"name": "Total Files", "id": "total_files"},
            {"name": "Passed Files", "id": "passed_files"},
            {"name": "Failed Files", "id": "failed_files"},
            {"name": "Pass Rate", "id": "pass_rate"},
            {"name": "Failure Rate", "id": "failure_rate"},
        ],
        data=[
            {
                "dataset": no_match_stats["name"],
                "total_files": no_match_stats["total_files"],
                "passed_files": no_match_stats["passed_files"],
                "failed_files": no_match_stats["failed_files"],
                "pass_rate": f"{no_match_stats['pass_rate']:.2f}%",
                "failure_rate": f"{no_match_stats['failure_rate']:.2f}%",
            },
            {
                "dataset": mandatory_failure_stats["name"],
                "total_files": mandatory_failure_stats["total_files"],
                "passed_files": mandatory_failure_stats["passed_files"],
                "failed_files": mandatory_failure_stats["failed_files"],
                "pass_rate": f"{mandatory_failure_stats['pass_rate']:.2f}%",
                "failure_rate": f"{mandatory_failure_stats['failure_rate']:.2f}%",
            }
        ],
        style_table={"marginBottom": "30px", "width": "80%", "margin": "auto"},
        style_header={"backgroundColor": "#003366", "color": "white", "fontWeight": "bold"},
        style_cell={"textAlign": "center", "padding": "10px"},
    ),
])

# Run the app
if __name__ == "__main__":
    app.run_server(debug=True)