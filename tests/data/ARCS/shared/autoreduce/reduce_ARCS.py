#!/usr/bin/env python
import os
import sys
import socket
from datetime import datetime
from plot_publisher import publish_plot, plot1d


def create_plotly_plot(filename):
    """Create a plot using the plot_publisher package"""
    try:
        # Import numpy for sample data generation
        import numpy as np

        # Create sample data based on run number for variety
        run_number = os.path.basename(filename).split(".")[0].split("_")[-1]
        seed = hash(run_number) % 1000  # Create deterministic but varied data based on run number  # noqa: E501
        np.random.seed(seed)

        # Create simple sample data without error bars
        x = list(range(1, 21))  # Simple integer range
        y = [10 + i + np.random.normal(0, 1) for i in range(20)]  # Simple list comprehension  # noqa: E501

        # Use plot_publisher's plot1d function which automatically handles version injection
        plot_html = plot1d(
            run_number=run_number,
            data_list=[[x, y]],  # Wrap in additional list to indicate it's one trace
            instrument="ARCS",
            title=f"ARCS Test Plot - Run {run_number}",
            x_title="Energy Transfer (meV)",
            y_title="Intensity (counts)",
            publish=False  # Just return the HTML, don't publish yet
        )

        print(f"Successfully created plot using plot_publisher.plot1d for run {run_number}")
        return plot_html

    except ImportError as e:
        print(f"Warning: Could not import required libraries: {e}")
        # Fallback to simple HTML content
        time = datetime.isoformat(datetime.now())
        hostname = socket.gethostname()

        return f"""<div id="arcs-plot" class="plotly-graph-div" style="height:400px; width:100%;" data-plotlyjs-version="fallback">
            <div style="text-align: center; padding: 50px;">
                <h3>ARCS Fallback Plot</h3>
                <p><strong>Filename:</strong> {filename}</p>
                <p><strong>Time:</strong> {time}</p>
                <p><strong>Hostname:</strong> {hostname}</p>
                <p>This is a fallback plot when plot_publisher is not available.</p>
            </div>
        </div>"""

    except Exception as e:
        print(f"Failed to create plotly plot: {e}")
        # Return simple fallback
        time = datetime.isoformat(datetime.now())
        hostname = socket.gethostname()

        return f"""<div><h>Example Plot Data</h><p>Filename: {filename}</p>
        <p>Time: {time}</p><p>Hostname: {hostname}</p></div>"""


if __name__ == "__main__":
    time = datetime.isoformat(datetime.now())
    filename = sys.argv[1] if len(sys.argv) > 1 else "test_file.nxs"
    print("Running reduction for " + filename + " at " + time)

    # Create plot using plot_publisher
    plot_html = create_plotly_plot(filename)

    # Extract run number
    run_number = os.path.basename(filename).split(".")[0].split("_")[-1]

    # Publish the plot
    publish_plot(
        "ARCS",
        run_number,
        files={"file": plot_html},
    )
