#!/usr/bin/env python
import sys
from datetime import datetime

print("Running reduction for " + sys.argv[1] + " at " + datetime.isoformat(datetime.now()))
