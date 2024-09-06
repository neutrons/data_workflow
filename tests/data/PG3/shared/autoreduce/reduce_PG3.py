#!/usr/bin/env python
import numpy as np
import sys
import time
from datetime import datetime

print("Running reduction for " + sys.argv[1] + " at " + datetime.isoformat(datetime.now()))

# intentionally take up a lot of memory (used to test job memory monitoring)
_ = np.random.rand(100000, 10000)
time.sleep(5)
