import json
import base64
import io
import dash
from llm import theorize_about_data, convert_metadata, get_variables_from_metadata
from dash import dcc, html, Output, Input, State
import pandas as pd

import logging

# Configure logging at the start of your script
logging.basicConfig(
    filename="log.log",
    filemode="a",
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)
external_stylesheets = ["https://codepen.io/chriddyp/pen/bWLwgP.css"]

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

app.layout = html.Div(
    [
        # CSV file upload component
        dcc.Upload(
            id="upload-data",
            children=html.Div(
                ["Drag and drop or click to select a CSV file."]),
            style={
                "width": "100%",
                "height": "60px",
                "lineHeight": "60px",
                "borderWidth": "1px",
                "borderStyle": "dashed",
                "borderRadius": "5px",
                "textAlign": "center",
                "margin": "10px",
            },
            multiple=False,  # Only one file at a time
        ),
        # Textarea component for metadata input
        html.Div(
            [
                html.Label("Enter Metadata for the CSV file:"),
                dcc.Textarea(
                    id="metadata-input",
                    placeholder="Type metadata here...",
                    value="",
                    style={"width": "100%", "height": 100},
                ),
                html.Button("Submit Metadata",
                            id="metadata-submit", n_clicks=0),
            ],
            style={"margin": "20px"},
        ),
        # Display output (metadata text and CSV preview)
        html.Div(id="output-data-upload"),
    ]
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

    # Display the file name, metadata (if provided), and a preview of the CSV data.
    return df


# Callback to update the output based on the uploaded CSV and metadata text input.


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
            # Get the questions only if metadata is provided.
            if metadata.strip() != "":
                json_metadata = convert_metadata(metadata)
                metadata_result = theorize_about_data(json_metadata)
                try:
                    # Convert the JSON string to a dictionary and extract the list of questions.
                    result_dict = json.loads(metadata_result)
                    causal_variables_json = get_variables_from_metadata(
                        json_metadata)
                    causal_variables = json.loads(causal_variables_json)
                    questions_list = result_dict.get("questions", [])
                    print(causal_variables)
                except Exception as e:
                    # Fallback: if parsing fails, show the error message.
                    questions_list = [f"Error parsing JSON: {str(e)}"]
                    causal_variables = [f"Error parsing JSON: {str(e)}"]
            else:
                causal_variables = {
                    "Note": "Enter Metadata to automatically identify treat, outcome and confounders"
                }
                questions_list = [
                    "Please enter plaintext metadata to get suggeested questions"
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
            # Create a separate HTML element (e.g., an html.P) for each question.
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
                        "Suggested casual inference questions that can be investigated-"
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
