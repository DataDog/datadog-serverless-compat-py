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
    "test_input, expected",
    [
        ("00000000-0000-0000-0000-000000000000+test-rg-EastUSwebspace-Linux", "test-rg"),
        ("00000000-0000-0000-0000-000000000000+test-rg-EastUSwebspace", "test-rg"),
        ("foo", None),
    ],
)
def test_extract_resource_group(test_input, expected):
    result = main.extract_resource_group(test_input)
    assert result == expected

@pytest.mark.parametrize(
    "dd_azure_rg, website_rg, website_owner_name, expected",
    [
        ("dd-azure-rg", None, None, "dd-azure-rg"),
        (None, "website-rg", None, "website-rg"),
        (None, None, "00000000-0000-0000-0000-000000000000+website-owner-name-rg-EastUSwebspace-Linux", "website-owner-name-rg"),
        (None, "website-rg", "00000000-0000-0000-0000-000000000000+website-owner-name-rg-EastUSwebspace-Linux", "website-rg"),
        ("dd-azure-rg", "website-rg", "00000000-0000-0000-0000-000000000000+website-owner-name-rg-EastUSwebspace-Linux", "dd-azure-rg"),
    ],
)
def test_get_azure_resource_group(monkeypatch, dd_azure_rg, website_rg, website_owner_name, expected):
    monkeypatch.delenv("DD_AZURE_RESOURCE_GROUP", raising=False)
    monkeypatch.delenv("WEBSITE_RESOURCE_GROUP", raising=False)
    monkeypatch.delenv("WEBSITE_OWNER_NAME", raising=False)
    
    # Set test environment variables only if they're not None
    if dd_azure_rg is not None:
        monkeypatch.setenv("DD_AZURE_RESOURCE_GROUP", dd_azure_rg)
    if website_rg is not None:
        monkeypatch.setenv("WEBSITE_RESOURCE_GROUP", website_rg)
    if website_owner_name is not None:
        monkeypatch.setenv("WEBSITE_OWNER_NAME", website_owner_name)

    result = main.get_azure_resource_group()
    assert result == expected

def test_start_azure_function_flex_no_dd_azure_rg_env_var(caplog, monkeypatch):
    """Test that the start function logs an error when DD_AZURE_RESOURCE_GROUP is not set for Azure functions on flex consumption plans"""
    
    # Set up Azure Function environment with flex plan
    monkeypatch.setenv("FUNCTIONS_EXTENSION_VERSION", "~4")
    monkeypatch.setenv("FUNCTIONS_WORKER_RUNTIME", "python")
    monkeypatch.setattr(sys, "platform", "linux")

    monkeypatch.delenv("DD_AZURE_RESOURCE_GROUP", raising=False)
    monkeypatch.delenv("WEBSITE_RESOURCE_GROUP", raising=False)
    monkeypatch.setenv("WEBSITE_OWNER_NAME", "00000000-0000-0000-0000-000000000000+flex-EastUSwebspace-Linux")

    main.start()

    # Verify error was logged
    expected_message = "Unable to determine Azure resource group. This may indicate a flex consumption plan without the DD_AZURE_RESOURCE_GROUP environment variable set. Shutting down Datadog Serverless Compatibility Layer."
    assert expected_message in caplog.text