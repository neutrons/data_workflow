import os
import sys

apache_path = os.path.dirname(__file__)
app_path = os.path.join(apache_path, '..')
app_path = os.path.abspath(app_path)

if app_path not in sys.path:
    sys.path.append(app_path)

os.environ['DJANGO_SETTINGS_MODULE'] = 'reporting_app.settings'

import django.core.handlers.wsgi
application = django.core.handlers.wsgi.WSGIHandler()