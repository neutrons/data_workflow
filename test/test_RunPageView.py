import requests


class TestRunPageView:
    def test(self):
        URL = 'http://localhost/users/login?next=/report/arcs/214581/'
        UN = 'postgres'
        PWD = 'postgres'
        client = requests.session()

        # Retrieve the CSRF token first
        client.get(URL)  # sets the cookie
        csrftoken = client.cookies['csrftoken']

        login_data = dict(username=UN, password=PWD, csrfmiddlewaretoken=csrftoken)
        r = client.post(URL, data=login_data)

        assert r.status_code == 200
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
