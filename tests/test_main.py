from datadog_serverless_compat import main
import pytest
import sys
from unittest.mock import Mock


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


@pytest.mark.parametrize("custom_binary", [False, True])
@pytest.mark.parametrize(
    "environment", [main.CloudEnvironment.AZURE_FUNCTION, main.CloudEnvironment.GOOGLE_CLOUD_RUN_FUNCTION_1ST_GEN]
)
def test_start_passes_versions_to_child(monkeypatch, tmp_path, custom_binary, environment):
    executable = tmp_path / "compat"
    executable.write_bytes(b"test fixture")
    monkeypatch.setattr(main, "get_environment", lambda: environment)
    monkeypatch.setattr(sys, "platform", "linux")
    monkeypatch.setattr(main, "get_package_version", lambda: "0.21.0")
    monkeypatch.setattr(main.platform, "python_version", lambda: "3.13.7")
    monkeypatch.setattr(main.tempfile, "gettempdir", lambda: str(tmp_path))
    if custom_binary:
        monkeypatch.setenv("DD_SERVERLESS_COMPAT_PATH", str(executable))
    else:
        monkeypatch.delenv("DD_SERVERLESS_COMPAT_PATH", raising=False)
        monkeypatch.setattr(main, "get_binary_path", lambda: str(executable))
    monkeypatch.setenv("DD_SERVERLESS_COMPAT_VERSION", "stale")
    monkeypatch.setenv("PYTHON_VERSION", "stale")
    monkeypatch.setenv("FUNCTIONS_WORKER_RUNTIME_VERSION", "stale")
    monkeypatch.setenv("DD_SERVICE", "keep-me")
    child = Mock()
    monkeypatch.setattr(main, "Popen", child)
    main.start()
    child.assert_called_once()
    env = child.call_args.kwargs["env"]
    assert env["DD_SERVERLESS_COMPAT_VERSION"] == "0.21.0"
    assert env["PYTHON_VERSION"] == "3.13.7"
    expected_worker = "3.13.7" if environment == main.CloudEnvironment.AZURE_FUNCTION else "stale"
    assert env["FUNCTIONS_WORKER_RUNTIME_VERSION"] == expected_worker
    assert env["DD_SERVICE"] == "keep-me"
    assert main.os.environ["PYTHON_VERSION"] == "stale"


@pytest.mark.parametrize(
    "website_sku, dd_azure_rg, expected",
    [
        ("FlexConsumption", None, True),
        ("FlexConsumption", "test-rg", False),
        ("ElasticPremium", None, False),
        ("ElasticPremium", "test-rg", False),
    ],
)
def test_is_azure_flex_without_dd_azure_rg_env_var(monkeypatch, website_sku, dd_azure_rg, expected):
    monkeypatch.setenv("WEBSITE_SKU", website_sku)
    if dd_azure_rg is not None:
        monkeypatch.setenv("DD_AZURE_RESOURCE_GROUP", dd_azure_rg)

    result = main.is_azure_flex_without_dd_azure_rg_env_var()

    assert result == expected


def test_start_azure_function_flex_no_dd_azure_rg_env_var(caplog, monkeypatch):
    """Test that start() logs an error when DD_AZURE_RESOURCE_GROUP is not set for Azure flex consumption"""

    # Set up Azure Function environment with flex plan
    monkeypatch.setenv("FUNCTIONS_EXTENSION_VERSION", "~4")
    monkeypatch.setenv("FUNCTIONS_WORKER_RUNTIME", "python")
    monkeypatch.setattr(sys, "platform", "linux")
    monkeypatch.setenv("WEBSITE_SKU", "FlexConsumption")

    main.start()

    # Verify error was logged
    expected_message = (
        "Azure function detected on flex consumption plan without DD_AZURE_RESOURCE_GROUP set."
        " Please set the DD_AZURE_RESOURCE_GROUP environment variable to your resource group name"
        " in Azure app settings. Shutting down Datadog Serverless Compatibility Layer."
    )

    assert expected_message in caplog.text
