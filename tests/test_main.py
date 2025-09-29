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
    # Set test environment variables only if they're not None
    if website_sku is not None:
        monkeypatch.setenv("WEBSITE_SKU", website_sku)
    if dd_azure_rg is not None:
        monkeypatch.setenv("DD_AZURE_RESOURCE_GROUP", dd_azure_rg)

    result = main.is_azure_flex_without_dd_azure_rg_env_var()

    assert result == expected

def test_start_azure_function_flex_no_dd_azure_rg_env_var(caplog, monkeypatch):
    """Test that the start function logs an error when DD_AZURE_RESOURCE_GROUP is not set for Azure functions on flex consumption plans"""
    
    # Set up Azure Function environment with flex plan
    monkeypatch.setenv("FUNCTIONS_EXTENSION_VERSION", "~4")
    monkeypatch.setenv("FUNCTIONS_WORKER_RUNTIME", "python")
    monkeypatch.setattr(sys, "platform", "linux")
    monkeypatch.setenv("WEBSITE_SKU", "FlexConsumption")

    main.start()

    # Verify error was logged
    expected_message = "Azure function detected on flex consumption plan without DD_AZURE_RESOURCE_GROUP set. Please set the DD_AZURE_RESOURCE_GROUP environment variable to your resource group name in Azure app settings. Shutting down Datadog Serverless Compatibility Layer."
    assert expected_message in caplog.text