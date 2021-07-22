#!/usr/bin/env python
from __future__ import absolute_import, division, print_function, unicode_literals

import os
import sys

if __name__ == "__main__":
    print('os.path.isfile("/usr/share/zoneinfo/America/New_York") = {}'.format(os.path.isfile('/usr/share/zoneinfo/America/New_York')))
    sys.exit(1)
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "reporting_app.settings")

    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)
