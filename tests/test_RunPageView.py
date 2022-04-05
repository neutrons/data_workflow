import pytest
import unittest
import requests


class TestRunPageView:
    instrument_scientist_usern4me = "InstrumentScientist"
    instrument_scientist_p4ssword = "InstrumentScientist"
    general_user_usern4me = "GeneralUser"
    general_user_p4ssword = "GeneralUser"

    @pytest.fixture
    def instrument_scientist(self):
        r = self.login("/report/arcs/214583/", self.instrument_scientist_usern4me, self.instrument_scientist_usern4me)
        yield r

    @pytest.fixture
    def dashboard_instrument_scientist(self):
        r = self.login("/dasmon/", self.instrument_scientist_usern4me, self.instrument_scientist_usern4me)
        yield r

    @pytest.fixture
    def extended_dashboard_instrument_scientist(self):
        r = self.login("/dasmon/dashboard/", self.instrument_scientist_usern4me, self.instrument_scientist_usern4me)
        yield r

    @pytest.fixture
    def latest_runs_instrument_scientist(self):
        r = self.login("/dasmon/summary/", self.instrument_scientist_usern4me, self.instrument_scientist_usern4me)
        yield r

    @pytest.fixture
    def latest_runs_general_user(self):
        r = self.login("/dasmon/summary/", self.general_user_usern4me, self.general_user_p4ssword)
        yield r

    @pytest.fixture
    def general_user(self):
        r = self.login("/report/arcs/214583/", self.general_user_usern4me, self.general_user_p4ssword)
        yield r

    @pytest.fixture
    def dashboard_general_user(self):
        r = self.login("/dasmon/", self.general_user_usern4me, self.general_user_p4ssword)
        yield r

    @pytest.fixture
    def extended_dashboard_general_user(self):
        r = self.login("/dasmon/dashboard/", self.general_user_usern4me, self.general_user_p4ssword)
        yield r

    @pytest.fixture
    def reduction_setup_page(self):
        r = self.login("/reduction/arcs/", self.instrument_scientist_usern4me, self.instrument_scientist_usern4me)
        yield r

    @pytest.fixture
    def reduction_setup_page_general_user(self):
        r = self.login("/reduction/arcs/", self.general_user_usern4me, self.general_user_p4ssword)
        yield r

    @pytest.fixture
    def post_processing_page(self):
        r = self.login("/report/processing", self.instrument_scientist_usern4me, self.instrument_scientist_usern4me)
        yield r

    def removeWhitespace(self, text):
        return "".join(text.split())

    def assertHtml(self, expected, actual):
        assert self.removeWhitespace(expected) in self.removeWhitespace(actual), actual

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
        self.assertHtml("<title>ARCS Run 214581</title>", r.text)

        # Check that OnCat could be reached
        assert "Could not communicate with the online catalog" not in r.text
        assert "There is no catalog information for this run yet" not in r.text

        self.assertHtml("<td>Run title</td><td><b>HfO2:12Y omega=90.5,Ei=60 Flux,T=300.944 K</b></td>", r.text)
        self.assertHtml("<td>Run start</td><td>Oct. 20, 2021, 6:50 a.m.</td>", r.text)
        self.assertHtml("<td>Run end</td><td>Oct. 20, 2021, 6:53 a.m.</td>", r.text)
        self.assertHtml("<td>Duration</td><td>179.45538330078125</td>", r.text)
        self.assertHtml("<td>Total counts</td><td>1158832</td>", r.text)
        self.assertHtml("<td>Proton charge</td><td>251337556440.0</td>", r.text)

        # Check that live_data was retrived
        self.assertHtml("https://livedata.sns.gov:443/plots/arcs/214581/update/html/", r.text)

        # Check workflow has been completed
        self.assertHtml("reduction.complete", r.text)
        self.assertHtml("catalog.complete", r.text)
        self.assertHtml("reduction_catalog.complete", r.text)

    def verifyDashboard(self, r):
        html = self.removeWhitespace(r.text)

        self.assertHtml("""<p>List of instruments:<br>""", html)
        self.assertHtml(
            """<a href="/dasmon/dashboard/">extended dashboard</a> |
         <a href="/dasmon/summary/">latest runs</a>""",
            html,
        )

    def testGeneralUserVerifyDashboard(self, dashboard_general_user):
        assert dashboard_general_user.status_code == 200
        self.verifyDashboard(dashboard_general_user)

    def testInstrumentScientistVerifyDashboard(self, dashboard_instrument_scientist):
        assert dashboard_instrument_scientist.status_code == 200
        self.verifyDashboard(dashboard_instrument_scientist)

    def verifyExtendedDashboard(self, r):
        html = self.removeWhitespace(r.text)

        self.assertHtml("""<div id="runs_per_hour_""", html)
        self.assertHtml("""" class="dashboard_plots"></div>""", html)

    def testGeneralUserVerifyExtendedDashboard(self, extended_dashboard_general_user):
        assert extended_dashboard_general_user.status_code == 200
        self.verifyExtendedDashboard(extended_dashboard_general_user)

    def testInstrumentScientistVerifyExtendedDashboard(self, extended_dashboard_instrument_scientist):
        assert extended_dashboard_instrument_scientist.status_code == 200
        self.verifyExtendedDashboard(extended_dashboard_instrument_scientist)

    # 1 test to confirm catalog data is received
    @unittest.skip("JavaScript not processed, this data will be missing")
    def testInstrumentScientistCatalogDataExist(self, instrument_scientist):
        assert instrument_scientist.status_code == 200
        self.confirmCatalogDataExist(instrument_scientist)

    @unittest.skip("JavaScript not processed, this data will be missing")
    def testGeneralUserCatalogDataExist(self, general_user):
        assert general_user.status_code == 200
        self.confirmCatalogDataExist(general_user)

    def confirmPlotDataExist(self, response):
        r = response
        # checks that the xaxis title of all the expected graphs
        self.assertHtml(
            '<text class="xtitle" style="font-family: &quot;Open Sans&quot;'
            ", verdana, arial, sans-serif; font-size: 14px; fill: rgb(42, 63, 95);"
            ' opacity: 1; font-weight: normal; white-space: pre;" x="293.5" y="488.1995361328125"'
            ' text-anchor="middle" data-unformatted="|Q| (1/A)" data-math="N">|Q| (1/A)</text>',
            r.text,
        )
        self.assertHtml(
            '<text class="xtitle" style="font-family: &quot;Open Sans&quot;,'
            " verdana, arial, sans-serif; font-size: 14px; fill: rgb(42, 63, 95);"
            ' opacity: 1; font-weight: normal; white-space: pre;" x="320" y="388.1995361328125"'
            ' text-anchor="middle" data-unformatted="Energy transfer (meV)" data-math="N">Energy transfer (meV)</text>',
            r.text,
        )
        self.assertHtml(
            '<text class="xtitle" style="font-family: &quot;Open Sans&quot;, verdana, arial, sans-serif;'
            ' font-size: 14px; fill: rgb(42, 63, 95); opacity: 1; font-weight: normal; white-space: pre;"'
            ' x="297" y="488.1995361328125" text-anchor="middle" data-unformatted="[0,0,L] (r.l.u.)" data'
            '-math="N">[0,0,L] (r.l.u.)</text>',
            r.text,
        )
        self.assertHtml(
            '<text class="xtitle" style="font-family: &quot;Open Sans&quot;, verdana, arial, sans-serif;'
            ' font-size: 14px; fill: rgb(42, 63, 95); opacity: 1; font-weight: normal; white-space: pre;"'
            ' x="297" y="488.1995361328125" text-anchor="middle" data-unformatted="[0,0,L] (r.l.u.)" data-math="N">'
            "[0,0,L] (r.l.u.)</text>",
            r.text,
        )
        self.assertHtml(
            '<text class="xtitle" style="font-family: &quot;Open Sans&quot;, verdana, arial, sans-serif;'
            ' font-size: 14px; fill: rgb(42, 63, 95); opacity: 1; font-weight: normal; white-space: pre;"'
            ' x="293.5" y="488.1995361328125" text-anchor="middle" data-unformatted="[0,K,0] (r.l.u.)"'
            ' data-math="N">[0,K,0] (r.l.u.)</text>',
            r.text,
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

    def testGeneralUserAccessDenied(self, general_user):
        assert general_user.status_code == 200
        self.assertHtml(
            "You do not have access to data for this experiment. If you need access, please contact the",
            general_user.text,
        )

    def confirmPVDataExist(self, response):
        r = response
        html = self.removeWhitespace(r.text)

        self.assertHtml(
            """<div class="box">

  <table class="message_table fixed_table">
    <thead>
      <tr>
        <th style="width: 170px;">Message</th>
        <th>Information</th>
        <th style="width: 90px;">Time</th>
      </tr>
    </thead>
    <tbody>

      <tr>
        <td>""",
            html,
        )

    # 3 test to confirm pv data is received
    def testInstrumentScientistPVDataExist(self, instrument_scientist):
        assert instrument_scientist.status_code == 200
        self.confirmPVDataExist(instrument_scientist)

    @unittest.skip("General User needs a self generated dataset to be able to view")
    def testGeneralUserPVDataExist(self, general_user):
        assert general_user.status_code == 200
        self.confirmPVDataExist(general_user)

    def testInstrumentScientistReductionButtonsExist(self, instrument_scientist):
        assert instrument_scientist.status_code == 200
        r = instrument_scientist
        self.assertHtml("""<a href='javascript:void(0);' onClick="confirm('catalog');">catalog</a>""", r.text)
        self.assertHtml("""<a href='javascript:void(0);' onClick="confirm('reduce');">reduction</a>""", r.text)
        self.assertHtml(
            """<a href='javascript:void(0);' onClick="confirm('postprocess');">all post-processing</a>""", r.text
        )
        self.assertHtml("""<a href='/reduction/arcs/'>setup</a>""", r.text)

    def testInstrumentScientistReductionSetupExists(self, reduction_setup_page):
        assert reduction_setup_page.status_code == 200
        r = reduction_setup_page

        html = self.removeWhitespace(r.text)

        assert (
            self.removeWhitespace("""Only instrument team members can use this form: contact adara_support@ornl.gov""")
            not in html
        )
        self.assertHtml(
            """<tr><th>Raw vanadium</th> <td ><input type="text" name="raw_vanadium" class="font_resize"
             id="id_raw_vanadium"> </td></tr>""",
            html,
        )
        self.assertHtml(
            """<tr><th>Processed vanadium</th> <td ><input type="text" name="processed_vanadium"
             class="font_resize" id="id_processed_vanadium"> </td></tr>""",
            html,
        )
        self.assertHtml("""<tr><th>Grouping file</th> <td ><select name="grouping" id="id_grouping">""", html)
        self.assertHtml(
            """<tr class='tiny_input'><th>Energy binning <span style='font-weight: normal;'>[% of E""", html
        )
        self.assertHtml("""<span >E<sub>min</sub> <input type="number" name="e_min" value="-0.2" """, html)
        self.assertHtml("""<sub>step</sub> <input type="number" name="e_step" value="0.015" step="any" """, html)
        self.assertHtml("""<sub>max</sub> <input type="number" name="e_max" value="0.95" step="any" """, html)

    def testGeneralUserReductionSetupDenied(self, reduction_setup_page_general_user):
        assert reduction_setup_page_general_user.status_code == 200

        self.assertHtml(
            """Only instrument team members can use this form: contact adara_support@ornl.gov""",
            reduction_setup_page_general_user.text,
        )

    # NOTE: Nothing is currently stopping general users from going directly to this page,
    # there is no messages saying they cant uses this like there is on the reduction setup page
    def testInstrumentScientistPostProcessingExists(self, post_processing_page):
        assert post_processing_page.status_code == 200
        r = post_processing_page

        self.assertHtml("""<th><label for="id_experiment">Experiment:</label></th>""", r.text)
        self.assertHtml("""<th><label for="id_run_list">Run list:</label></th>""", r.text)
        self.assertHtml("""<th><label for="id_create_as_needed">Create as needed:</label></th>""", r.text)
        self.assertHtml("""<th><label for="id_task">Task:</label></th>""", r.text)
        self.assertHtml("""<th><label for="id_instrument">Instrument:</label></th>""", r.text)
        self.assertHtml(
            """<input id="submit_button" title="Click to submit tasks" type="submit" name="button_choice"
            value="submit"/>""",
            self.removeWhitespace(r.text),
        )

    def verifyLatestRun(self, r):
        self.assertHtml("""<div class="summary">List of latest runs:<br><br>""", r.text)
        self.assertHtml(
            """<table class="message_table dynatable-loaded" id="run_table"><thead><tr>
        <th data-dynatable-column="instrument_id" style="min-width: 50px;" class="dynatable-head">
        <a class="dynatable-sort-header" href="#">Instr.<span class="dynatable-arrow"> ▲</span></a></th>
        <th data-dynatable-column="run" data-dynatable-no-sort="true" style="min-width: 50px;" class=
        "dynatable-head">Run</th>""",
            r.text,
        )

    def testGeneralUserVerifyLatestRuns(self, latest_runs_general_user):
        assert latest_runs_general_user.status_code == 200

    def testInstrumentScientistVerifyLatestRuns(self, latest_runs_instrument_scientist):
        assert latest_runs_instrument_scientist.status_code == 200
