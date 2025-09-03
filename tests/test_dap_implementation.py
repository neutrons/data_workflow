"""
Test for Digital Analytics Program (DAP) implementation
"""

import re

import pytest
import requests


class TestDAPImplementation:
    """Test cases for Digital Analytics Program integration"""

    def test_dap_script_in_base_template(self):
        """Test that the DAP script is present in the base template"""
        # Read the base template file
        base_template_path = "/home/dzj/data_workflow/src/webmon_app/reporting/templates/base.html"
        with open(base_template_path, "r") as f:
            template_content = f.read()

        # Check that DAP script is present
        assert "Digital Analytics Program (DAP)" in template_content
        assert "_fed_an_ua_tag" in template_content
        assert "dap.digitalgov.gov/Universal-Federated-Analytics-Min.js" in template_content
        assert "agency=DOE" in template_content
        assert "subagency=BES" in template_content

    def test_dap_script_has_error_handling(self):
        """Test that the DAP script includes proper error handling"""
        base_template_path = "/home/dzj/data_workflow/src/webmon_app/reporting/templates/base.html"
        with open(base_template_path, "r") as f:
            template_content = f.read()

        # Check for error handling
        assert "onerror" in template_content
        assert "console.log" in template_content
        assert "failed to load" in template_content

    def test_dap_script_structure(self):
        """Test that the DAP script has proper structure"""
        base_template_path = "/home/dzj/data_workflow/src/webmon_app/reporting/templates/base.html"
        with open(base_template_path, "r") as f:
            template_content = f.read()

        # Check script structure
        assert "createElement('script')" in template_content
        assert "async = true" in template_content
        assert "appendChild(dapScript)" in template_content

        # Verify the script URL contains required parameters
        dap_pattern = r"dap\.digitalgov\.gov/Universal-Federated-Analytics-Min\.js\?agency=DOE&subagency=BES&sitetopic=science&siteplatform=drupal"  # noqa: E501
        assert re.search(dap_pattern, template_content)


class TestDAPIntegrationLive:
    """Integration tests for DAP functionality (requires running server)"""

    @pytest.fixture
    def webmon_url(self):
        """Base URL for webmon testing"""
        return "http://localhost"

    def test_dap_script_accessibility(self):
        """Test that the DAP script URL is accessible"""
        dap_url = "https://dap.digitalgov.gov/Universal-Federated-Analytics-Min.js?agency=DOE&subagency=BES&sitetopic=science&siteplatform=drupal"

        try:
            response = requests.get(dap_url, timeout=10)
            if response.status_code == 200:
                # Check that it's actually JavaScript
                assert "function" in response.text.lower()
            else:
                pytest.skip(f"DAP script URL returned status: {response.status_code}")
        except requests.exceptions.RequestException as e:
            pytest.skip(
                f"DAP script URL not accessible: {e} - Expected on beamline computers without external network access"
            )

    def test_dap_parameters_configuration(self):
        """Test that DAP parameters are correctly configured for DOE/BES"""
        base_template_path = "/home/dzj/data_workflow/src/webmon_app/reporting/templates/base.html"
        with open(base_template_path, "r") as f:
            template_content = f.read()

        # Verify all required DAP parameters are present
        required_params = ["agency=DOE", "subagency=BES", "sitetopic=science", "siteplatform=drupal"]

        for param in required_params:
            assert param in template_content, f"Missing required DAP parameter: {param}"
