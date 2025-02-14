#!/usr/bin/env python
import sys
import time
from datetime import datetime

print("Running reduction for " + sys.argv[1] + " at " + datetime.isoformat(datetime.now()))

time.sleep(10)
