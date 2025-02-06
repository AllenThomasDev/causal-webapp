from sklearn.exceptions import DataConversionWarning
import warnings
from llm import (
    theorize_about_data,
    convert_metadata,
    get_variables_from_metadata,
    explain_identification,
)
import dash_dangerously_set_inner_html
from dash import dcc, html, Output, Input, State, ALL
import dash_bootstrap_components as dbc
import dash
import pandas as pd
import logging
import io
import base64
from dowhy import CausalModel
import os
import matplotlib.pyplot as plt
import json
import matplotlib
import logging.config

DEFAULT_LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "loggers": {
        "": {
            "level": "WARN",
        },
    },
}
logging.config.dictConfig(DEFAULT_LOGGING)
# Disabling warnings output

warnings.filterwarnings(action="ignore", category=DataConversionWarning)
matplotlib.use("Agg")


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
                    "Causal Inference - Model, Identify, Estimate",
                    className="text-center my-3",
                ),
                width=12,
            )
        ),
        # File Upload Section
        dbc.Row(
            [
                dbc.Col(
                    [
                        dbc.Card(
                            [
                                dbc.CardHeader("Upload CSV File"),
                                dbc.CardBody(
                                    dcc.Upload(
                                        id="upload-data",
                                        children=html.Div(
                                            "Drag and drop or click to select a CSV file."
                                        ),
                                        multiple=False,
                                    )
                                ),
                            ],
                            className="mb-3",
                        ),
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
                                            style={
                                                "width": "100%",
                                                "height": "120px",
                                            },
                                        ),
                                        dbc.Button(
                                            "Submit Metadata",
                                            id="metadata-submit",
                                            n_clicks=0,
                                            color="primary",
                                        ),
                                    ]
                                ),
                            ],
                        ),
                    ],
                    width=6,
                ),
                # Metadata Input Section
                dbc.Col(html.Div(id="question-container")),
            ]
        ),
        dbc.Row(
            [
                dbc.Col(html.Div(id="variable-dropdown-container")),
                dbc.Col(html.Div(id="graph_parent"), width=6),
            ]
        ),
        dbc.Row(
            [
                dbc.Col(
                    [
                        dbc.Card(
                            [
                                dbc.CardHeader("Phase 2. Identification"),
                                dbc.CardBody(
                                    [
                                        html.Div(id="identification-parent"),
                                    ]
                                ),
                            ]
                        ),
                        html.Div(id="estimation-parent"),
                        html.Div(id="refute-parent"),
                    ],
                    width=6,
                ),
                dbc.Col(
                    html.Div(id="identification-explanation"),
                ),
            ]
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


def update_question_elements(questions_list):
    return dbc.Card(
        [
            dbc.CardHeader("Suggested Causal Questions You Can ask - "),
            dbc.CardBody(
                [
                    html.Div(
                        question,
                        id=f"question-{i}",
                        style={
                            "cursor": "pointer",
                            "color": "blue",
                            "margin": "10px 0",
                        },
                        n_clicks=0,
                    )
                    for i, question in enumerate(questions_list)
                ]
            ),
        ]
    )


def update_variable_dropdowns(causal_variables, n_clicks):
    return dbc.Card(
        [
            dbc.CardHeader("Variables"),
            dbc.CardBody(
                [
                    html.Div(
                        [
                            html.Label(i.split("_")[0], style={
                                       "margin-right": "10px"}),
                            dcc.Dropdown(
                                options=list(df.columns.values),
                                value=all_vals
                                if isinstance(all_vals, list)
                                else [all_vals],
                                id={"type": "variable_dropdowns",
                                    "index": n_clicks},
                                multi=True,
                                clearable=False,
                            ),
                        ],
                        style={
                            "align-items": "center",
                            "margin-bottom": "10px",
                        },
                    )
                    for i, all_vals in causal_variables.items()
                ]
            ),
        ]
    )


@app.callback(
    Output("question-container", "children"),
    Input("metadata-submit", "n_clicks"),
    State("metadata-input", "value"),
    prevent_initial_call=True,
)
def update_question_elements_callback(n_clicks, metadata):
    global json_metadata
    if metadata.strip() != "":
        try:
            json_metadata = convert_metadata(metadata)
            metadata_result = theorize_about_data(json_metadata)
            result_dict = json.loads(metadata_result)
            questions_list = result_dict.get("questions", [])
        except Exception as e:
            questions_list = [f"Error parsing JSON: {str(e)}"]
    else:
        questions_list = [
            "Please enter plaintext metadata to get suggested questions"]
    return update_question_elements(questions_list)


@app.callback(
    Output("variable-dropdown-container", "children"),
    Input("upload-data", "contents"),
    Input("upload-data", "filename"),
    Input("metadata-submit", "n_clicks"),
    State("metadata-input", "value"),
    prevent_initial_call=True,
)
def update_variable_dropdown_callback(contents, filename, n_clicks, metadata):
    if contents is not None:
        global df
        df = parse_contents(contents, filename)
        if isinstance(df, pd.DataFrame) and metadata.strip() != "":
            try:
                json_metadata = convert_metadata(metadata)
                causal_variables_json = get_variables_from_metadata(
                    json_metadata)
                causal_variables = json.loads(causal_variables_json)
            except Exception as e:
                causal_variables = {"Error": f"Error parsing JSON: {str(e)}"}
        else:
            causal_variables = {
                "Note": "Enter Metadata to automatically identify treat, outcome and confounders"
            }
        return update_variable_dropdowns(causal_variables, n_clicks)
    return html.Div("No file uploaded yet.")


@app.callback(
    [
        Output("estimation-parent", "children"),
        Output("refute-parent", "children"),
    ],
    Input({"type": "variable_dropdowns", "index": ALL}, "value"),
)
def show_estimation_selector(values):
    if len(values) < 3:
        return dbc.Card()
    return (
        dbc.Col(
            [
                dbc.Card(
                    [
                        dbc.CardHeader("Phase 3. Estimate"),
                        dbc.CardBody(
                            [
                                dcc.Dropdown(
                                    values[2],
                                    values[2][0],
                                    placeholder="Select which confounder you want to make an estimation for...",
                                    id="estimation-selector",
                                ),
                                dcc.Dropdown(
                                    ["continuous", "discrete"],
                                    "discrete",
                                    placeholder="Select the type of the confounder variable...",
                                    id="estimation-type-selector",
                                ),
                                html.Div(id="estimation-graph"),
                            ]
                        ),
                    ]
                )
            ],
        ),
        dbc.Card(
            [
                dbc.CardHeader("Phase 4. Refutation"),
                dbc.CardBody(
                    [
                        dcc.Dropdown(
                            [
                                "data_subset_refuter",
                                "placebo_treatment_refuter",
                                "random_common_cause",
                            ],
                            placeholder="Select which refutation method you want to use...",
                            id="refutation-selector",
                        ),
                        html.Div(id="refutation-results"),
                    ]
                ),
            ]
        ),
    )


@app.callback(
    Output("refutation-results", "value"),
    Input("refutation-selector", "value"),
    prevent_initial_call=True,
)
def show_refutation(value):
    placebo_type = "permute"
    subset_fraction = 0.9
    lalonde_identified_estimand = model.identify_effect(
        proceed_when_unidentifiable=True
    )
    lalonde_estimate = model.estimate_effect(
        lalonde_identified_estimand, method_name="backdoor.propensity_score_weighting"
    )
    return html.Div(
        str(
            model.refute_estimate(
                lalonde_identified_estimand,
                lalonde_estimate,
                method_name="random_common_cause",
            )
        )
    )
    if value == "random_common_cause":
        return model.refute_estimate(
            lalonde_identified_estimand,
            lalonde_estimate,
            method_name="random_common_cause",
        )
    if value == "placebo_treatment_refuter":
        return model.refute_estimate(
            lalonde_identified_estimand,
            lalonde_estimate,
            method_name="placebo_treatment_refuter",
            placebo_type="permute",
        )
    if value == "data_subset_refuter":
        return model.refute_estimate(
            lalonde_identified_estimand,
            lalonde_estimate,
            method_name="data_subset_refuter",
            subset_fraction=0.9,
        )


def custom_show(*args, **kwargs):
    # "This is becuase estimate.interpret, does not save the image"
    plt.savefig("estimate_chart.png")


plt.show = custom_show


@app.callback(
    Output("estimation-graph", "children"),
    Input("estimation-selector", "value"),
    Input("estimation-type-selector", "value"),
    prevent_initial_call=True,
)
def show_estimation_plot(value, confounder_type):
    print(value)
    identified_estimand = model.identify_effect(
        proceed_when_unidentifiable=True)
    estimate = model.estimate_effect(
        identified_estimand,
        method_name="backdoor.propensity_score_weighting",
        target_units="ate",
        method_params={"weighting_scheme": "ips_weight"},
    )
    try:
        estimate.interpret(
            method_name="confounder_distribution_interpreter",
            var_type=confounder_type,
            var_name=value,
            fig_size=(10, 7),
            font_size=12,
        )
        image_path = "estimate_chart.png"
        if not os.path.exists(image_path):
            raise FileNotFoundError(
                f"{image_path} not found. Ensure model.view_model() generates the image correctly."
            )
        with open(image_path, "rb") as image_file:
            encoded_image = base64.b64encode(image_file.read()).decode("utf-8")
            return html.Img(
                src=f"data:image/png;base64,{encoded_image}",
                style={"width": "85%"},
            )
    except:
        return html.Div(
            "Possible mismatch between confounder and type (discrete/continuous)"
        )


@app.callback(
    Output("graph_parent", "children"),
    Input({"type": "variable_dropdowns", "index": ALL}, "value"),
    prevent_initial_call=True,
)
def show_graph(values):
    if len(values) < 3:
        return dbc.Card()
    outcome = values[0]
    treat = values[1]
    causes = values[2]
    global model
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

    # identified_estimand = model.identify_effect(
    #     proceed_when_unidentifiable=True)
    return dbc.Card(
        [
            dbc.CardHeader("Phase 1. Model"),
            dbc.CardBody(
                [
                    html.Img(
                        src=f"data:image/png;base64,{encoded_image}",
                        style={"width": "85%"},
                    ),
                ]
            ),
        ]
    )


@app.callback(
    [
        Output("identification-parent", "children"),
        Output("identification-explanation", "children"),
    ],
    [Input({"type": "variable_dropdowns", "index": ALL}, "value")],
    prevent_initial_call=True,
)
def show_identification_plot(values):
    if len(values) < 3:
        return dbc.Card()
    outcome = values[0]
    treat = values[1]
    causes = values[2]
    global model
    model = CausalModel(data=df, treatment=treat,
                        outcome=outcome, common_causes=causes)
    identified_estimand = model.identify_effect(
        proceed_when_unidentifiable=True)
    estimate = model.estimate_effect(
        identified_estimand,
        method_name="backdoor.propensity_score_weighting",
        target_units="ate",
        method_params={"weighting_scheme": "ips_weight"},
    )
    # print(estimate)
    print("Causal Estimate is " + str(estimate.value))

    import statsmodels.formula.api as smf

    reg = smf.wls("re78~1+treat", data=df, weights=df.ips_stabilized_weight)
    res = reg.fit()
    identificationToBeExplained = res.summary().as_text()
    explanationmd = explain_identification(
        identificationToBeExplained, json_metadata)
    return html.Div(
        [
            dash_dangerously_set_inner_html.DangerouslySetInnerHTML(
                res.summary().as_html()
            )
        ]
    ), dbc.Card(
        [
            dbc.CardHeader("Simplified explanation of results - "),
            dbc.CardBody([html.Div([dcc.Markdown(explanationmd)])]),
        ]
    )


if __name__ == "__main__":
    app.run_server(debug=False)
