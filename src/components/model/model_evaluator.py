"""Module to evaluate models"""
from urllib.parse import urlparse
import numpy as np
from sklearn.metrics import r2_score, mean_absolute_error, mean_squared_error
import mlflow
from src.entities.config_entity import DataConfig, ModelConfig, EvalConfig
from src.utils.common import get_file_paths_in_folder, \
    save_object, load_object, save_json
from src.utils.helper import load_split_data, perform_data_transformation
from src import logger


class ModelEvaluator:
    """Class to evaluate models"""

    def __init__(self,
                 data_config=DataConfig,
                 model_config=ModelConfig,
                 eval_config=EvalConfig):
        self.data_config = data_config
        self.model_config = model_config
        self.eval_config = eval_config

    @staticmethod
    def r2_score(actual, predicted):
        """Method to calculate r2_score"""
        try:
            score = r2_score(actual, predicted)
            return score
        except Exception as ex:
            raise ex

    @staticmethod
    def mean_squared_error(actual, predicted):
        """Method to calculate r2_score"""
        try:
            score = np.sqrt(mean_squared_error(actual, predicted))
            return score
        except Exception as ex:
            raise ex

    @staticmethod
    def mean_absolute_error(actual, predicted):
        """Method to calculate r2_score"""
        try:
            score = mean_absolute_error(actual, predicted)
            return score
        except Exception as ex:
            raise ex

    def evaluate_metric(self, eval_metric: str, actual, predicted):
        """Method to invoke model evaluation"""
        try:
            return getattr(self, eval_metric)(actual, predicted)
        except AttributeError as ex:
            logger.exception("Error getting metric function: %s", ex)
            raise ex
        except Exception as ex:
            raise ex

    def evaluate_models(self, file_paths: list, x_test, y_test):
        """Method to evaluate models"""
        try:
            trained_models = {}
            result = {}

            for file_path in file_paths:
                # Predict
                model = load_object(file_path=file_path)
                model_name = type(model).__name__
                logger.info("loaded %s successfully.", model_name)
                y_test_pred = model.predict(x_test)

                # Evaluate
                eval_metrics: list = self.eval_config.eval_metrics.split(
                    ',')
                test_model_scores = {}
                for metric in eval_metrics:
                    metric = metric.strip()
                    test_model_score = self.evaluate_metric(
                        eval_metric=metric,
                        actual=y_test, predicted=y_test_pred)
                    test_model_scores[metric] = test_model_score
                    logger.info("Evaluated %s with %s: %s", model_name,
                                metric, test_model_score)

                # Prepare return values
                trained_models[model_name] = model
                result[model_name] = test_model_scores
            return trained_models, result
        except AttributeError as ex:
            raise ex
        except Exception as ex:
            raise ex

    def log_mlflow(self, model, model_score: dict):
        """Method to log to MLflow"""
        try:
            # Below URL can be used to save experiments on remote server (dagshub can be used)
            # dagshub uri, username and password will need to be
            # exported as env variabls using gitbash terminal
            # commented as of now - experiments saved to local and model registry not done
            # mlflow.set_registry_uri(self.eval_config.mlflow_uri)
            tracking_url_type_store = urlparse(
                mlflow.get_tracking_uri()).scheme

            with mlflow.start_run():
                mlflow.log_params(model.get_params())
                mlflow.log_metric("r2_score", model_score["r2_score"])
                mlflow.log_metric("mean_squared_error",
                                  model_score["mean_squared_error"])
                mlflow.log_metric("mean_absolute_error",
                                  model_score["mean_absolute_error"])

                # Model registry does not work with file store
                if tracking_url_type_store != "file":
                    # Register the model
                    # There are other ways to use the Model Registry, which depends on the use case,
                    # please refer to the doc for more information:
                    # https://mlflow.org/docs/latest/model-registry.html#api-workflow
                    mlflow.sklearn.log_model(
                        model, "model", registered_model_name="abc")
                else:
                    mlflow.sklearn.log_model(model, "model")
        except AttributeError as ex:
            raise ex
        except Exception as ex:
            raise ex

    @staticmethod
    def get_best_score(scores: dict, metric_name: str):
        """Method to get the best score"""
        try:
            if metric_name == "r2_score":
                return max(sorted(scores.values()))
            return min(sorted(scores.values()))
        except Exception as ex:
            raise ex

    def save_best_model(self, trained_models, result):
        """Method to save best model and result"""
        try:
            # Save all results to json
            logger.info("Saving Results to json file")
            save_json(
                file_path=self.eval_config.eval_scores_path, data=result)

            # Build a new dictionary with only desired metric to get best model
            result_dict = {}
            best_metric = self.eval_config.eval_metric_selection
            for key, value in result.items():
                for key_2, value_2 in value.items():
                    if key_2 == best_metric:
                        result_dict[key] = value_2

            # Save best model
            best_model_score = self.get_best_score(scores=result_dict,
                                                   metric_name=best_metric)
            best_model_name = list(result_dict.keys())[list(
                result_dict.values()).index(best_model_score)]
            best_model = trained_models[best_model_name]
            save_object(
                file_path=self.model_config.final_model_path, obj=best_model)
            logger.info("%s is the best model with %s as %s",
                        best_model_name,
                        best_metric,
                        best_model_score)

            # Log ml flow
            self.log_mlflow(best_model, result[best_model_name])
        except AttributeError as ex:
            raise ex
        except Exception as ex:
            raise ex

    def evaluate(self):
        """Method to evaluate models"""
        try:
            # Load test data
            x_test, y_test = load_split_data(data_path=self.data_config.test_split_path,
                                             target_column=self.data_config.target_column)

            # Transform test data
            x_test_transformed = perform_data_transformation(
                transformer_path=self.data_config.transformer_path,
                input_data=x_test)

            # Evaluate models
            file_paths = get_file_paths_in_folder(
                self.model_config.trained_models_path)
            trained_models, result = self.evaluate_models(file_paths=file_paths,
                                                          x_test=x_test_transformed, y_test=y_test)
            # Save the best model
            self.save_best_model(trained_models=trained_models, result=result)
        except AttributeError as ex:
            logger.exception("Error finding attribute: %s", ex)
            raise ex
        except Exception as ex:
            logger.exception("Exception occured: %s", ex)
            raise ex