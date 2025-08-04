#!/usr/bin/env python
import os
import sys
from datetime import datetime
from plot_publisher import publish_plot


def create_plotly_plot():
    """Create a plot using the plot_publisher package"""
    try:
        # Import numpy for sample data generation
        import numpy as np

        # Create sample data
        x = list(range(1, 21))  # Simple integer range
        y = [10 + i * 0.5 + np.random.normal(0, 0.5) for i in range(20)]  # Simple list  # noqa: E501

        # Import plot1d from plot_publisher
        from plot_publisher import plot1d

        # Use plot_publisher's plot1d function which automatically handles version injection
        plot_html = plot1d(
            run_number="test",  # Will be overridden in main
            data_list=[[x, y]],  # Wrap in additional list to indicate it's one trace
            instrument="REF_L",
            title="REF_L Test Plot with Dynamic Plotly Loading",
            x_title="X Axis Label",
            y_title="Y Axis Label",
            publish=False  # Just return the HTML, don't publish yet
        )

        print("Successfully created plot using plot_publisher.plot1d")
        return plot_html

    except ImportError as e:
        print(f"Warning: Could not import required libraries: {e}")
        # Fallback to simple HTML if plot_publisher is not available
        return """
        <div id="fallback-plot" class="plotly-graph-div" style="height:400px; width:100%;" data-plotlyjs-version="fallback">
            <div style="text-align: center; padding: 100px;">
                <h3>REF_L Fallback Plot</h3>
                <p>This is a fallback plot when plot_publisher is not available.</p>
                <p>Sample data: [1, 2, 3, 4, 5] vs [10, 15, 13, 17, 20]</p>
            </div>
        </div>
        """

    except Exception as e:
        print(f"Failed to create plotly plot: {e}")
        return None


if __name__ == "__main__":
    time = datetime.isoformat(datetime.now())
    filename = sys.argv[1] if len(sys.argv) > 1 else "test_file.nxs"
    print("Running reduction for " + filename + " at " + time)

    # Extract run number from filename
    run_number = os.path.basename(filename).split(".")[0].split("_")[-1]

    plot_html = create_plotly_plot()

    if plot_html:
        publish_plot(
            "REF_L",
            run_number,
            files={"file": plot_html},
        )
    else:
        print("Failed to create plot, skipping publication")
