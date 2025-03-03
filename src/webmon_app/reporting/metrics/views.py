from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.cache import cache_page

import reporting.dasmon.view_util as dasmon_view_util
import reporting.users.view_util as users_view_util

from . import view_util


@users_view_util.login_or_local_required_401
@cache_page(settings.FAST_PAGE_CACHE_TIMEOUT)
def metrics(request):
    data = {}
    data["workflow_diagnostics"] = dasmon_view_util.workflow_diagnostics()
    data["postprocessing_diagnostics"] = view_util.postprocessing_diagnostics()
    data["instrument_status"] = view_util.instrument_status()
    data["run_statuses"] = view_util.run_statuses()
    return JsonResponse(data)


@users_view_util.login_or_local_required_401
@cache_page(settings.FAST_PAGE_CACHE_TIMEOUT)
def workflow_diagnostics(request):
    return JsonResponse(dasmon_view_util.workflow_diagnostics())


@users_view_util.login_or_local_required_401
@cache_page(settings.FAST_PAGE_CACHE_TIMEOUT)
def postprocessing_diagnostics(request):
    return JsonResponse(view_util.postprocessing_diagnostics(), safe=False)


@users_view_util.login_or_local_required_401
@cache_page(settings.FAST_PAGE_CACHE_TIMEOUT)
def instrument_status(request):
    return JsonResponse(view_util.instrument_status())


@users_view_util.login_or_local_required_401
@cache_page(settings.FAST_PAGE_CACHE_TIMEOUT)
def run_statuses(request, minutes=60):
    return JsonResponse(view_util.run_statuses(minutes))
