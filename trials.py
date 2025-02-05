from IPython.display import Image, display
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
model = CausalModel(
    data=df,
    treatment="treat",
    outcome="re78",
    common_causes="nodegr+black+hisp+age+educ+married".split("+"),
)

model.view_model()

display(Image(filename="causal_model.png"))
