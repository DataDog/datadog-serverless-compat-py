from datadog_serverless_compat import main
import pytest
import sys


@pytest.mark.parametrize(
    "test_input, expected",
    [
        (
            [
                ("FUNCTIONS_EXTENSION_VERSION", "~4"),
                ("FUNCTIONS_WORKER_RUNTIME", "python"),
            ],
            main.CloudEnvironment.AZURE_FUNCTION,
        ),
        (
            [
                ("FUNCTION_NAME", "test-function"),
                ("GCP_PROJECT", "test-project"),
            ],
            main.CloudEnvironment.GOOGLE_CLOUD_RUN_FUNCTION_1ST_GEN,
        ),
        (
            [
                ("K_SERVICE", "test-service"),
                ("FUNCTION_TARGET", "test-function"),
            ],
            main.CloudEnvironment.GOOGLE_CLOUD_RUN_FUNCTION_2ND_GEN,
        ),
        (
            [
                ("FUNCTIONS_EXTENSION_VERSION", "~4"),
            ],
            main.CloudEnvironment.UNKNOWN,
        ),
        (
            [],
            main.CloudEnvironment.UNKNOWN,
        ),
    ],
)
def test_get_environment(monkeypatch, test_input, expected):
    for env_var in test_input:
        monkeypatch.setenv(env_var[0], env_var[1])

    environment = main.get_environment()

    assert environment == expected


@pytest.mark.parametrize(
    "test_input, expected",
    [
        ("win32", "bin/windows-amd64/datadog-serverless-compat.exe"),
        ("linux", "bin/linux-amd64/datadog-serverless-compat"),
        ("unknown", "bin/linux-amd64/datadog-serverless-compat"),
    ],
)
def test_get_binary_path_for_platform(monkeypatch, test_input, expected):
    monkeypatch.setattr(sys, "platform", test_input)

    binary_path = main.get_binary_path()

    assert binary_path.endswith(expected)


def test_get_binary_path_from_env_var(monkeypatch):
    user_configured_path = "path/to/datadog-serverless-compat"

    monkeypatch.setattr(sys, "platform", "linux")
    monkeypatch.setenv("DD_SERVERLESS_COMPAT_PATH", user_configured_path)

    binary_path = main.get_binary_path()

    assert binary_path == user_configured_path
