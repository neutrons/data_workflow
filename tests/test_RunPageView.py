import pytest
import unittest
import requests


class TestRunPageView:
    @pytest.fixture
    def instrument_scientist(self):
        r = self.login("/report/arcs/214583/", "InstrumentScientist", "InstrumentScientist")
        yield r

    @pytest.fixture
    def general_user(self):
        r = self.login("/report/arcs/214583/", "GeneralUser", "GeneralUser")
        yield r

    @pytest.fixture
    def reduction_setup_page(self):
        r = self.login("/reduction/arcs/", "InstrumentScientist", "InstrumentScientist")
        yield r

    @pytest.fixture
    def reduction_setup_page_general_user(self):
        r = self.login("/reduction/arcs/", "GeneralUser", "GeneralUser")
        yield r

    @pytest.fixture
    def post_processing_page(self):
        r = self.login("/report/processing", "InstrumentScientist", "InstrumentScientist")
        yield r

    def removeWhitespace(self, text):
        return "".join(text.split())

    def login(self, next, username, password):
        URL = "http://localhost/users/login?next="
        client = requests.session()

        # Retrieve the CSRF token first
        client.get(URL)  # sets the cookie
        csrftoken = client.cookies["csrftoken"]

        login_data = dict(username=username, password=password, csrfmiddlewaretoken=csrftoken)
        return client.post(URL + next, data=login_data, timeout=None)

    def confirmCatalogDataExist(self, response):
        r = response
        assert "<title>ARCS Run 214581</title>" in r.text

        # Check that OnCat could be reached
        assert "Could not communicate with the online catalog" not in r.text
        assert "There is no catalog information for this run yet" not in r.text

        assert "<td>Run title</td><td><b>HfO2:12Y omega=90.5,Ei=60 Flux,T=300.944 K</b></td>" in r.text
        assert "<td>Run start</td><td>Oct. 20, 2021, 6:50 a.m.</td>" in r.text
        assert "<td>Run end</td><td>Oct. 20, 2021, 6:53 a.m.</td>" in r.text
        assert "<td>Duration</td><td>179.45538330078125</td>" in r.text
        assert "<td>Total counts</td><td>1158832</td>" in r.text
        assert "<td>Proton charge</td><td>251337556440.0</td>" in r.text

        # Check that live_data was retrived
        assert "https://livedata.sns.gov:443/plots/arcs/214581/update/html/" in r.text

        # Check workflow has been completed
        assert "reduction.complete" in r.text
        assert "catalog.complete" in r.text
        assert "reduction_catalog.complete" in r.text

    # 1 test to confirm catalog data is received
    @unittest.skip("JavaScript not processed, this data will be missing")
    def testCatalogDataExistInstrumentScientist(self, instrument_scientist):
        assert instrument_scientist.status_code == 200
        self.confirmCatalogDataExist(instrument_scientist)

    @unittest.skip("JavaScript not processed, this data will be missing")
    def testCatalogDataExistGeneralUser(self, general_user):
        assert general_user.status_code == 200
        self.confirmCatalogDataExist(general_user)

    def confirmPlotDataExist(self, response):
        r = response
        # checks that the xaxis title of all the expected graphs
        assert (
            '<text class="xtitle" style="font-family: &quot;Open Sans&quot;'
            ", verdana, arial, sans-serif; font-size: 14px; fill: rgb(42, 63, 95);"
            ' opacity: 1; font-weight: normal; white-space: pre;" x="293.5" y="488.1995361328125"'
            ' text-anchor="middle" data-unformatted="|Q| (1/A)" data-math="N">|Q| (1/A)</text>' in r.text
        )
        assert (
            '<text class="xtitle" style="font-family: &quot;Open Sans&quot;,'
            " verdana, arial, sans-serif; font-size: 14px; fill: rgb(42, 63, 95);"
            ' opacity: 1; font-weight: normal; white-space: pre;" x="320" y="388.1995361328125"'
            ' text-anchor="middle" data-unformatted="Energy transfer (meV)" data-math="N">Energy transfer (meV)</text>'
            in r.text
        )
        assert (
            '<text class="xtitle" style="font-family: &quot;Open Sans&quot;, verdana, arial, sans-serif;'
            ' font-size: 14px; fill: rgb(42, 63, 95); opacity: 1; font-weight: normal; white-space: pre;"'
            ' x="297" y="488.1995361328125" text-anchor="middle" data-unformatted="[0,0,L] (r.l.u.)" data'
            '-math="N">[0,0,L] (r.l.u.)</text>' in r.text
        )
        assert (
            '<text class="xtitle" style="font-family: &quot;Open Sans&quot;, verdana, arial, sans-serif;'
            ' font-size: 14px; fill: rgb(42, 63, 95); opacity: 1; font-weight: normal; white-space: pre;"'
            ' x="297" y="488.1995361328125" text-anchor="middle" data-unformatted="[0,0,L] (r.l.u.)" data-math="N">'
            "[0,0,L] (r.l.u.)</text>" in r.text
        )
        assert (
            '<text class="xtitle" style="font-family: &quot;Open Sans&quot;, verdana, arial, sans-serif;'
            ' font-size: 14px; fill: rgb(42, 63, 95); opacity: 1; font-weight: normal; white-space: pre;"'
            ' x="293.5" y="488.1995361328125" text-anchor="middle" data-unformatted="[0,K,0] (r.l.u.)"'
            ' data-math="N">[0,K,0] (r.l.u.)</text>' in r.text
        )

    # 2 test to confirm plot data is received
    @unittest.skip("JavaScript not processed, this data will be missing")
    def testInstrumentScientistPlotDataExist(self, instrument_scientist):
        assert instrument_scientist.status_code == 200
        self.confirmPlotDataExist(instrument_scientist)

    @unittest.skip("JavaScript not processed, this data will be missing")
    def testGeneralUserPlotDataExist(self, general_user):
        assert general_user.status_code == 200
        self.confirmPlotDataExist(general_user)

    def confirmPVDataExist(self, response):
        r = response
        html = self.removeWhitespace(r.text)

        assert (
            self.removeWhitespace(
                """<tr>
        <td>reduction_catalog.complete</td>
        <td></td>"""
            )
            in html
        )
        assert (
            self.removeWhitespace(
                """<tr>
        <td>reduction_catalog.started</td>
        <td></td>"""
            )
            in html
        )
        assert (
            self.removeWhitespace(
                """<tr>
        <td>reduction_catalog.data_ready</td>
        <td></td>"""
            )
            in html
        )
        assert (
            self.removeWhitespace(
                """<tr>
        <td>reduction.complete</td>
        <td>autoreducer</td>"""
            )
            in html
        )
        assert (
            self.removeWhitespace(
                """<tr>
        <td>catalog.complete</td>
        <td></td>"""
            )
            in html
        )
        assert (
            self.removeWhitespace(
                """<tr>
        <td>reduction.started</td>
        <td>autoreducer</td>"""
            )
            in html
        )
        assert (
            self.removeWhitespace(
                """<tr>
        <td>catalog.started</td>
        <td></td>"""
            )
            in html
        )
        assert (
            self.removeWhitespace(
                """<tr>
        <td>reduction.data_ready</td>
        <td></td>"""
            )
            in html
        )
        assert (
            self.removeWhitespace(
                """<tr>
        <td>catalog.data_ready</td>
        <td></td>"""
            )
            in html
        )
        assert (
            self.removeWhitespace(
                """<tr>
        <td>postprocess.data_ready</td>
        <td></td>"""
            )
            in html
        )

    # 3 test to confirm pv data is received
    def testInstrumentScientistPVDataExist(self, instrument_scientist):
        assert instrument_scientist.status_code == 200
        self.confirmPVDataExist(instrument_scientist)

    def testGeneralUserPVDataExist(self, general_user):
        assert general_user.status_code == 200
        self.confirmPVDataExist(general_user)

    def testInstrumentScientistReductionButtonsExist(self, instrument_scientist):
        assert instrument_scientist.status_code == 200
        r = instrument_scientist
        assert """<a href='javascript:void(0);' onClick="confirm('catalog');">catalog</a>""" in r.text
        assert """<a href='javascript:void(0);' onClick="confirm('reduce');">reduction</a>""" in r.text
        assert """<a href='javascript:void(0);' onClick="confirm('postprocess');">all post-processing</a>""" in r.text
        assert """<a href='/reduction/arcs/'>setup</a>""" in r.text

    def testInstrumentScientistReductionSetupExists(self, reduction_setup_page):
        assert reduction_setup_page.status_code == 200
        r = reduction_setup_page

        assert """Only instrument team members can use this form: contact adara_support@ornl.gov""" not in r.text
        assert (
            """<tr><th>Raw vanadium</th> <td ><input type="text" name="raw_vanadium" class="font_resize"'
            ' id="id_raw_vanadium"> </td></tr>"""
            in r.text
        )
        assert (
            """<tr><th>Processed vanadium</th> <td ><input type="text" name="processed_vanadium"'
            ' class="font_resize" id="id_processed_vanadium"> </td></tr>"""
            in r.text
        )
        assert """<tr><th>Grouping file</th> <td ><select name="grouping" id="id_grouping">""" in r.text
        assert (
            """<tr class='tiny_input'><th>Energy binning <span style='font-weight: normal;'>[% of E<sub>guess</sub>]<'
            '</span></th> <td>"""
            in r.text
        )
        assert (
            """<span >E<sub>min</sub> <input type="number" name="e_min" value="-0.2" step="any"'
            ' required id="id_e_min"> </span>"""
            in r.text
        )
        assert (
            """<sub>step</sub> <input type="number" name="e_step" value="0.015" step="any" required'
            ' id="id_e_step">"""
            in r.text
        )
        assert (
            """<sub>max</sub> <input type="number" name="e_max" value="0.95" step="any" required'
            ' id="id_e_max"> </td></tr>"""
            in r.text
        )

    def testGeneralUserReductionSetupDenied(self, reduction_setup_page_general_user):
        assert reduction_setup_page_general_user.status_code == 200

        assert (
            """Only instrument team members can use this form: contact adara_support@ornl.gov"""
            in reduction_setup_page_general_user.text
        )

    # NOTE: Nothing is currently stopping general users from going directly to this page,
    # there is no messages saying they cant uses this like there is on the reduction setup page
    def testInstrumentScientistPostProcessingExists(self, post_processing_page):
        assert post_processing_page.status_code == 200
        r = post_processing_page

        assert (
            """<tr><th><label for="id_experiment">Experiment:</label></th><td><input type="text"'
            ' name="experiment" required id="id_experiment"></td></tr>"""
            in r.text
        )
        assert (
            """<tr><th><label for="id_run_list">Run list:</label></th><td><input type="text"'
            ' name="run_list" required id="id_run_list"></td></tr>"""
            in r.text
        )
        assert (
            """<tr><th><label for="id_create_as_needed">Create as needed:</label></th><td><input'
            ' type="checkbox" name="create_as_needed" id="id_create_as_needed"></td></tr>"""
            in r.text
        )
        assert """<tr><th><label for="id_task">Task:</label></th><td><select name="task" id="id_task">""" in r.text
        assert (
            """<tr><th><label for="id_instrument">Instrument:</label></th><td><select name="instrument"'
            ' id="id_instrument">"""
            in r.text
        )
        assert (
            """<input id="submit_button" title="Click to submit tasks" type="submit" name="button_choice"'
            ' value="submit"/>"""
            in r.text
        )
