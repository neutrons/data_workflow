#!/usr/bin/env python
import json
import os
import string
import sys
from datetime import datetime

import requests


minimal_html_plot = """
<div>
    <div id="3b2f5f9e-1c44-4e7b-8bfa-3a5c91b1e9d3"
         class="plotly-graph-div"
         style="height:100%; width:100%;"></div>

    <script type="text/javascript">
        window.PLOTLYENV = window.PLOTLYENV || {};

        Plotly.newPlot(
            "3b2f5f9e-1c44-4e7b-8bfa-3a5c91b1e9d3",
            [
                {
                    "type": "scatter",
                    "mode": "lines",
                    "x": [1, 2, 3],
                    "y": [4, 1, 2]
                }
            ],
            {
                "title": {"text": "Minimal Plotly Example"}
            },
            {"responsive": true}
        );
    </script>
</div>
"""


if __name__ == "__main__":
    time = datetime.isoformat(datetime.now())
    filename = sys.argv[1] if len(sys.argv) > 1 else "test_file.nxs"
    print("Running reduction for " + filename + " at " + time)

    # Extract run number
    run_number = os.path.basename(filename).split(".")[0].split("_")[-1]

    # Create plot without plotly version injection
    plot_html = minimal_html_plot

    json_path = "/etc/autoreduce/post_processing.conf"
    with open(json_path, "r") as f:
        config = json.load(f)
        url_template = config["publish_url_template"]
        publisher_username = config["publisher_username"]
        publisher_password = config["publisher_password"]

    url_template = string.Template(url_template)
    url = url_template.substitute(instrument="VULCAN", run_number=str(run_number))

    response = requests.post(
        url,
        data={"username": publisher_username, "password": publisher_password},
        files={"file": plot_html},
        # verify=config.verify_ssl,
    )
