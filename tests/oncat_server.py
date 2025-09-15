import json
import logging
import os
from http.server import BaseHTTPRequestHandler, HTTPServer

logging.basicConfig(filename="oncat_server.log", level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")


class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):
    """Fake ONCat server for testing purposes"""

    def do_POST(self):
        if self.headers.get("Authorization") != "Bearer test-token":
            self.send_response(403)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            response = {"error": "Forbidden"}
            self.wfile.write(json.dumps(response).encode("utf-8"))
            return

        if self.path.startswith("/api/datafiles/"):
            location = self.path.replace("/api/datafiles", "").replace("/ingest", "")
            logging.info("Received datafile ingest request for %s", location)
        elif self.path.startswith("/api/reductions/"):
            location = self.path.replace("/api/reductions", "").replace("/ingest", "")
            logging.info("Received reduction ingest request for %s", location)
        else:
            self.send_response(400)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            logging.error("Unknown endpoint: %s", self.path)
            response = {"error": "Unknown endpoint"}
            self.wfile.write(json.dumps(response).encode("utf-8"))
            return

        if not os.path.isfile(location):
            self.send_response(404)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            logging.error("File not found: %s", location)
            response = {"error": "File not found"}
            self.wfile.write(json.dumps(response).encode("utf-8"))
            return

        try:
            # assume the format /facility/instrument/experiment/nexus/instrument_run_number.nxs.h5
            # the real server would be more complex
            _, facility, instrument, experiment, *_, filename = location.split("/")
            run_number = int(filename.split("_")[-1].split(".")[0])
        except Exception:
            self.send_response(400)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            logging.error("Invalid path format: %s", location)
            response = {"error": "Invalid path format"}
            self.wfile.write(json.dumps(response).encode("utf-8"))
            return

        # Send response
        self.send_response(200)
        self.send_header("Content-type", "application/json")
        self.end_headers()
        response = {
            "location": location,
            "facility": facility,
            "instrument": instrument,
            "experiment": experiment,
            "indexed": {"run_number": run_number},
        }
        self.wfile.write(json.dumps(response).encode("utf-8"))


def run(server_class=HTTPServer, handler_class=SimpleHTTPRequestHandler, port=8000):
    server_address = ("", port)
    httpd = server_class(server_address, handler_class)
    httpd.serve_forever()


if __name__ == "__main__":
    run()
