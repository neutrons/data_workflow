#!/usr/bin/env python
import os
import sys
import socket
from datetime import datetime
from postprocessing.publish_plot import publish_plot

if __name__ == "__main__":
    time = datetime.isoformat(datetime.now())
    filename = sys.argv[1]
    print("Running reduction for " + filename + " at " + time)

    publish_plot(
        "ARCS",
        os.path.basename(filename).split(".")[0].split("_")[-1],
        files={
            "file": f"<div><h>Example Plot Data</h><p>Filename: {filename}</p>"
            f"<p>Time: {time}</p><p>Hostname: {socket.gethostname()}</p></div>"
        },
    )
