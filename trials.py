from IPython.core.display import display
import statsmodels.formula.api as smf
from IPython.display import Image, display
import dowhy.datasets
import dowhy.plotter
import logging.config
import logging
import numpy as np
import pandas as pd

from dowhy import CausalModel
import dowhy.datasets

# Avoid printing dataconversion warnings from sklearn and numpy
import warnings
from sklearn.exceptions import DataConversionWarning

warnings.filterwarnings(action="ignore", category=DataConversionWarning)
warnings.filterwarnings(action="ignore", category=FutureWarning)

# Config dict to set the logging level
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
logging.info("Getting started with DoWhy. Running notebook...")
df = pd.read_csv("lalonde_data.csv")
print(type(df))

# With graph
global model
model = CausalModel(
    data=df,
    treatment="treat",
    outcome="re78",
    common_causes="nodegree,black,hispan,age,educ,married,re74,re75".split(
        ","),
)
identified_estimand = model.identify_effect(proceed_when_unidentifiable=True)
estimate = model.estimate_effect(
    identified_estimand,
    method_name="backdoor.propensity_score_weighting",
    target_units="ate",
    method_params={"weighting_scheme": "ips_weight"},
)
estimate.interpret(
    method_name="confounder_distribution_interpreter",
    var_type="discrete",
    var_name="married",
    fig_size=(10, 7),
    font_size=12,
)
