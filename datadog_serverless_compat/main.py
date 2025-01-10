from enum import Enum
import logging
import os
from subprocess import Popen
import sys


logger = logging.getLogger(__name__)


class CloudEnvironment(Enum):
    AZURE_FUNCTION = "Azure Function"
    GOOGLE_CLOUD_RUN_FUNCTION_1ST_GEN = "Google Cloud Run Function 1st gen"
    GOOGLE_CLOUD_RUN_FUNCTION_2ND_GEN = "Google Cloud Run Function 2nd gen"
    UNKNOWN = "Unknown"


def get_environment():
    if (
        os.environ.get("FUNCTIONS_EXTENSION_VERSION") is not None
        and os.environ.get("FUNCTIONS_WORKER_RUNTIME") is not None
    ):
        return CloudEnvironment.AZURE_FUNCTION

    if (
        os.environ.get("FUNCTION_NAME") is not None
        and os.environ.get("GCP_PROJECT") is not None
    ):
        return CloudEnvironment.GOOGLE_CLOUD_RUN_FUNCTION_1ST_GEN

    if (
        os.environ.get("K_SERVICE") is not None
        and os.environ.get("FUNCTION_TARGET") is not None
    ):
        return CloudEnvironment.GOOGLE_CLOUD_RUN_FUNCTION_2ND_GEN

    return CloudEnvironment.UNKNOWN


def get_binary_path():
    # Use user defined path if provided
    binary_path = os.getenv("DD_SERVERLESS_COMPAT_PATH")

    if binary_path is not None:
        return binary_path

    binary_path_os_folder = os.path.join(
        os.path.dirname(__file__),
        "bin/windows-amd64" if sys.platform == "win32" else "bin/linux-amd64",
    )
    binary_extension = ".exe" if sys.platform == "win32" else ""
    binary_path = os.path.join(
        binary_path_os_folder, f"datadog-serverless-compat{binary_extension}"
    )

    return binary_path


def start():
    environment = get_environment()
    logger.debug(f"Environment detected: {environment}")

    if environment == CloudEnvironment.UNKNOWN:
        logger.error(
            f"{environment} environment detected, will not start the Datadog Serverless Compatibility Layer"
        )
        return

    logger.debug(f"Platform detected: {sys.platform}")

    if sys.platform not in {"win32", "linux"}:
        logger.error(
            (
                f"Platform {sys.platform} detected, the Datadog Serverless Compatibility Layer is only supported",
                " on Windows and Linux",
            )
        )
        return

    binary_path = get_binary_path()
    logger.debug(f"Spawning process from binary at path {binary_path}")

    if not os.path.exists(binary_path):
        logger.error(
            f"Serverless Compatibility Layer did not start, could not find binary at path {binary_path}"
        )
        return

    try:
        logger.debug(
            f"Trying to spawn the Serverless Compatibility Layer at path: {binary_path}"
        )
        Popen(binary_path)
    except Exception as e:
        logger.error(
            f"An unexpected error occurred while spawning Serverless Compatibility Layer process: {repr(e)}"
        )
