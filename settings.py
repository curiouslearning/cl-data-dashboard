import google.cloud.logging
import logging
import os
from google.cloud import secretmanager


def get_secrets():
    client = secretmanager.SecretManagerServiceClient()
    attributes = {
        "table_id": get_secret(client, "table_id"),
        "dataset_id": get_secret(client, "dataset_name"),
        "fb_access_token": get_secret(client, "fb_access_token"),
        "fb_account_id": get_secret(client, "fb_account_id"),
        "fb_app_id": get_secret(client, "fb_app_id"),
        "fb_app_secret": get_secret(client, "fb_app_secret"),
        "gcp_project_id": get_secret(client, "gcp_project_id"),
    }
    return attributes


def get_secret(client, secret):
    name = "projects/405806232197/secrets/" + secret + "/versions/latest"
    response = client.access_secret_version(name=name)
    return response.payload.data.decode("UTF-8")


def init_logging():
    logging_client = google.cloud.logging.Client()
    logging_client.setup_logging(log_level=logging.DEBUG)
    logging_client.setup_logging()
    logger = logging.getLogger()

    if os.getenv("LOCAL_LOGGING", "False") == "True":
        # output logs to console - otherwise logs are only visible when running in GCP
        logger.addHandler(logging.StreamHandler())
    return logger
