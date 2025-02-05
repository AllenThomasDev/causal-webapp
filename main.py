import json
import base64
import io
import logging
import pandas as pd

import dash
import dash_bootstrap_components as dbc
from dash import dcc, html, Output, Input, State
from llm import theorize_about_data, convert_metadata, get_variables_from_metadata

# Configure logging at the start of your script
logging.basicConfig(
    filename="log.log",
    filemode="a",
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Use a Bootstrap theme for styling – here we select the LUX theme as an example.
external_stylesheets = [dbc.themes.LUX]
app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

app.layout = dbc.Container(
    [
        # Header
        dbc.Row(
            dbc.Col(
                html.H2(
                    "CSV and Metadata Upload Dashboard", className="text-center my-3"
                ),
                width=12,
            )
        ),
        # File Upload Section
        dbc.Row(
            dbc.Col(
                dbc.Card(
                    [
                        dbc.CardHeader("Upload CSV File"),
                        dbc.CardBody(
                            dcc.Upload(
                                id="upload-data",
                                children=html.Div(
                                    "Drag and drop or click to select a CSV file."
                                ),
                                style={
                                    "width": "100%",
                                    "height": "40px",
                                    "lineHeight": "40px",
                                    "borderWidth": "1px",
                                    "borderStyle": "dashed",
                                    "borderRadius": "5px",
                                    "textAlign": "center",
                                    "margin": "10px",
                                },
                                multiple=False,
                            )
                        ),
                    ],
                    className="mb-3",
                ),
                width=12,
            )
        ),
        # Metadata Input Section
        dbc.Row(
            dbc.Col(
                dbc.Card(
                    [
                        dbc.CardHeader("Enter Metadata for the CSV File"),
                        dbc.CardBody(
                            [
                                dcc.Textarea(
                                    id="metadata-input",
                                    placeholder="Type metadata here...",
                                    value="",
                                    style={"width": "100%", "height": "120px"},
                                ),
                                dbc.Button(
                                    "Submit Metadata",
                                    id="metadata-submit",
                                    n_clicks=0,
                                    color="primary",
                                    className="mt-2",
                                ),
                            ]
                        ),
                    ],
                    className="mb-3",
                ),
                width=12,
            )
        ),
        # Output Section for CSV Preview and Suggested Questions
        dbc.Row(
            dbc.Col(
                html.Div(id="output-data-upload"),
                width=12,
            )
        ),
    ],
    fluid=True,
)


def parse_contents(contents, filename):
    content_type, content_string = contents.split(",")
    decoded = base64.b64decode(content_string)
    try:
        if "csv" in filename:
            df = pd.read_csv(io.StringIO(decoded.decode("utf-8")))
        else:
            return html.Div(["Invalid file format. Please upload a CSV file."])
    except Exception as e:
        return html.Div([f"There was an error processing this file: {e}"])
    return df


@app.callback(
    Output("output-data-upload", "children"),
    Input("upload-data", "contents"),
    Input("upload-data", "filename"),
    Input("metadata-submit", "n_clicks"),
    State("metadata-input", "value"),
    prevent_initial_call=True,
)
def update_output(contents, filename, n_clicks, metadata):
    if contents is not None:
        df = parse_contents(contents, filename)
        if isinstance(df, pd.DataFrame):
            if metadata.strip() != "":
                json_metadata = convert_metadata(metadata)
                metadata_result = theorize_about_data(json_metadata)
                try:
                    result_dict = json.loads(metadata_result)
                    causal_variables_json = get_variables_from_metadata(
                        json_metadata)
                    causal_variables = json.loads(causal_variables_json)
                    questions_list = result_dict.get("questions", [])
                    print(causal_variables)
                except Exception as e:
                    questions_list = [f"Error parsing JSON: {str(e)}"]
                    causal_variables = [f"Error parsing JSON: {str(e)}"]
            else:
                causal_variables = {
                    "Note": "Enter Metadata to automatically identify treat, outcome and confounders"
                }
                questions_list = [
                    "Please enter plaintext metadata to get suggested questions"
                ]

            variable_dropdowns = [
                dcc.Dropdown(
                    options=all_vals if isinstance(
                        all_vals, list) else [all_vals],
                    value=all_vals if isinstance(
                        all_vals, list) else [all_vals],
                    id=f"dropdown-{i}",
                    multi=True,
                    clearable=False,
                )
                for i, all_vals in causal_variables.items()
            ]
            question_elements = [
                html.Div(
                    question,
                    id=f"question-{i}",
                    style={
                        "cursor": "pointer",
                        "color": "blue",
                        "text-decoration": "underline",
                        "margin": "10px 0",
                    },
                    n_clicks=0,
                )
                for i, question in enumerate(questions_list)
            ]
            return html.Div(
                [
                    html.H5(
                        "Suggested causal inference questions that can be investigated:"
                    ),
                    html.Div(variable_dropdowns),
                    html.Div(question_elements),
                    html.H6("Or"),
                    dcc.Input(
                        id="input_question",
                        type="text",
                        placeholder="Enter your own question - ",
                        debounce=True,
                        style={"width": "600px", "height": "48px"},
                    ),
                ]
            )
        else:
            return df
    return html.Div(["No file uploaded yet."])


if __name__ == "__main__":
    app.run_server(debug=True)
