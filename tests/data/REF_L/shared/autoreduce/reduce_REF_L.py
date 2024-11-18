#!/usr/bin/env python
import os
import sys
from datetime import datetime
from postprocessing.publish_plot import publish_plot

plot_div = """
<div>
    <div id="plot"></div>

    <script>
        // Layout configuration
        // Render the plot
        Plotly.newPlot('plot',
            [
                {
                    "x": [1, 2, 3, 4, 5],
                    "y": [10, 15, 13, 17, 20],
                    "type": 'scatter',
                    "mode": 'lines+markers',
                    "marker": { "color": 'red' }
                }
            ],
            {
                "title": 'My First Plot',
                "xaxis": { "title": 'X Axis Label' },
                "yaxis": { "title": 'Y Axis Label' }
            }
        );
    </script>
</div>
"""

if __name__ == "__main__":
    time = datetime.isoformat(datetime.now())
    filename = sys.argv[1]
    print("Running reduction for " + filename + " at " + time)

    publish_plot(
        "REF_L",
        os.path.basename(filename).split(".")[0].split("_")[-1],
        files={"file": f"<div>{plot_div}</div>"},
    )
