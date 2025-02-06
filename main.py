import json
import os
from dowhy import CausalModel
import base64
import io
import logging
import pandas as pd

import dash
import dash_bootstrap_components as dbc
from dash import dcc, html, Output, Input, State, ALL
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
            [
                dbc.Col(
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
                dbc.Col(
                    dbc.Col(
                        dbc.Card(
                            [
                                dbc.CardHeader(
                                    "Enter Metadata for the CSV File"),
                                dbc.CardBody(
                                    [
                                        dcc.Textarea(
                                            id="metadata-input",
                                            placeholder="Type metadata here...",
                                            value="",
                                            style={"width": "100%",
                                                   "height": "120px"},
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
            ]
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
def generate_output_layout(
    variable_dropdowns, question_elements, graph_output, identified_estimand
):
    return dbc.Row(
        [
            dbc.Col(
                [
                    html.H4("Variable Selection"),
                    html.P("Select variables for causal analysis:"),
                    html.Div(variable_dropdowns),
                ],
                md=4,
            ),
            dbc.Col(
                [
                    html.H4("Causal Graph"),
                    dcc.Loading(children=html.Div(
                        graph_output), type="circle"),
                    html.Pre(
                        str(identified_estimand).replace("###", "\n\n"),
                        className="mt-3",
                    ),
                ],
                md=4,
            ),
            dbc.Col(
                [
                    html.H4("Suggested Questions"),
                    html.Div(question_elements),
                    html.H6("Or Enter Your Own:"),
                    dcc.Input(
                        id="input_question",
                        type="text",
                        placeholder="Type your question...",
                        debounce=True,
                        style={"width": "100%", "marginBottom": "15px"},
                    ),
                ],
                md=4,
            ),
        ],
        className="mt-4",  # Add some top margin for spacing
    )


@app.callback(
    Output("graph_parent", component_property="children"),
    Input({"type": "variable_dropdowns", "index": ALL}, "value"),
)
def show_graph(values):
    outcome = values[0]
    treat = values[1]
    causes = values[2]

    model = CausalModel(data=df, treatment=treat,
                        outcome=outcome, common_causes=causes)
    model.view_model()

    # Ensure the image file is saved before trying to read it
    image_path = "causal_model.png"
    if not os.path.exists(image_path):
        raise FileNotFoundError(
            f"{image_path} not found. Ensure model.view_model() generates the image correctly."
        )

    # Encode the image to base64 for Dash display
    with open(image_path, "rb") as image_file:
        encoded_image = base64.b64encode(image_file.read()).decode("utf-8")

    identified_estimand = model.identify_effect(
        proceed_when_unidentifiable=True)
    print(identified_estimand)
    print(type(identified_estimand))
    print()

    return dbc.Col(
        [
            html.Label("Following is the causal DAG based on your "),
            html.Img(src=f"data:image/png;base64,{encoded_image}"),
            html.Pre(str(identified_estimand).replace("###", "\n\n")),
        ]
    )


if __name__ == "__main__":
    app.run_server(debug=True)
