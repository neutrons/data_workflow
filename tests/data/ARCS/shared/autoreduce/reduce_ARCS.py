#!/usr/bin/env python
import sys
from datetime import datetime

if __name__ == "__main__":
    print("Running reduction for " + sys.argv[1] + " at " + datetime.isoformat(datetime.now()))
