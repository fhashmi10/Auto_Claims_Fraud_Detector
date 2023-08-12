"""Module to define data preprocessing steps"""
import pandas as pd
import numpy as np
from src import logger

@staticmethod
def preprocess_data(data_frame) -> pd.DataFrame:
    """Method to perform data preprocessing"""
    try:
        # Drop unneccessary columns
        data_frame.drop('_c39', axis=1, inplace=True)
        data_frame.drop('incident_location', axis=1, inplace=True)

        # Datetime Handling
        data_frame[["policy_bind_date", "incident_date"]] = data_frame[[
            "policy_bind_date", "incident_date"]].apply(pd.to_datetime)
        data_frame["incident_days_since_inception"] = (
            data_frame["incident_date"] - data_frame["policy_bind_date"])/pd.Timedelta(days=1)
        data_frame["incident_days_since_inception"].apply(pd.to_numeric)
        data_frame.drop('incident_date', axis=1, inplace=True)
        data_frame.drop('policy_bind_date', axis=1, inplace=True)

        # Derived Metrics
        data_frame[['policy_csl_low', 'policy_csl_high']
                    ] = data_frame['policy_csl'].str.split('/', expand=True)
        data_frame[["policy_csl_low", "policy_csl_high"]] = data_frame[[
            "policy_csl_low", "policy_csl_high"]].apply(pd.to_numeric)
        data_frame.drop('policy_csl', axis=1, inplace=True)

        # Replace bad characters with nan
        data_frame.replace('?', np.nan, inplace=True)
        return data_frame
    except Exception as ex:
        logger.exception("Exception occured while pre-processing data %s", ex)
        raise ex
