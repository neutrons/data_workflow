# pylint: disable=bare-except, invalid-name
"""
    View utility functions for user management
"""
import sys
from django.urls import reverse
from django.shortcuts import redirect
from django.contrib.auth.models import Group
from django.http import HttpResponse
from django.conf import settings

# import code for encoding urls and generating md5 hashes
import hashlib
import socket
import logging

from users.models import PageView


def fill_template_values(request, **template_args):
    """
        Fill the template argument items needed to populate
        side bars and other satellite items on the pages.

        Only the arguments common to all pages will be filled.
    """
    template_args['user'] = request.user
    if request.user.is_authenticated:
        if hasattr(settings, 'GRAVATAR_URL'):
            if type(settings.ALLOWED_DOMAIN) is tuple and len(settings.ALLOWED_DOMAIN) > 0:
                domain = settings.ALLOWED_DOMAIN[0]
            else:
                domain = settings.ALLOWED_DOMAIN
            guess_email = "%s@%s" % (request.user.username, domain)
            gravatar_url = settings.GRAVATAR_URL + hashlib.md5(guess_email).hexdigest() + '?d=identicon'
            template_args['gravatar_url'] = gravatar_url
    else:
        request.user.username = 'Guest User'

    template_args['logout_url'] = reverse('users:perform_logout')
    redirect_url = reverse('users:perform_login')
    redirect_url += '?next=%s' % request.path
    template_args['login_url'] = redirect_url

    # Determine whether the user is using a mobile device
    template_args['is_mobile'] = hasattr(request, 'mobile') and request.mobile

    return template_args


def _check_credentials(request):
    """
        Internal utility method to check whether a user has access to a view
    """
    # If we don't allow guests but the user is authenticated, return the function
    if request.user.is_authenticated:
        return True

    # If we allow users on a domain, check the user's IP
    elif len(settings.ALLOWED_DOMAIN) > 0:
        ip_addr = request.META['REMOTE_ADDR']
        try:
            # If the user is on the allowed domain, return the function
            if socket.gethostbyaddr(ip_addr)[0].endswith(settings.ALLOWED_DOMAIN):
                return True
            # If we allow a certain domain and the user is on the server, return the function
            elif socket.gethostbyaddr(ip_addr)[0] == 'localhost':
                return True
        except:
            logging.error("Error processing IP address: %s", str(ip_addr))
    elif len(settings.ALLOWED_HOSTS) > 0:
        try:
            ip_addr = request.META['REMOTE_ADDR']
            host_name = socket.gethostbyaddr(ip_addr)[0]
            for item in settings.ALLOWED_HOSTS:
                if host_name.endswith(item):
                    return True
        except:
            logging.error("Error processing IP address: %s", str(ip_addr))
    return False


def login_or_local_required(fn):
    """
        Function decorator to check whether a user is allowed
        to see a view.
    """
    def request_processor(request, *args, **kws):
        if _check_credentials(request):
            return fn(request, *args, **kws)

        # If we made it here, we need to authenticate the user
        redirect_url = reverse('users:perform_login')
        redirect_url += '?next=%s' % request.path
        return redirect(redirect_url)
    return request_processor


def login_or_local_required_401(fn):
    """
        Function decorator to check whether a user is allowed
        to see a view.

        Usually used for AJAX calls.
    """
    def request_processor(request, *args, **kws):
        try:
            if _check_credentials(request):
                return fn(request, *args, **kws)
            return HttpResponse(status=401)
        except:
            logging.error("[%s]: %s", request.path, sys.exc_info()[1])
            return HttpResponse(status=500)
    return request_processor


def is_instrument_staff(request, instrument_id):
    """
        Determine whether a user is part of an
        instrument team
        @param request: HTTP request object
        @param instrument_id: Instrument object
    """
    # Look for Django group
    try:
        instrument_name = str(instrument_id).upper()
        instr_group = Group.objects.get(name="%s%s" % (instrument_name,
                                                       settings.INSTRUMENT_TEAM_SUFFIX))
        if instr_group in request.user.groups.all():
            return True
    except Group.DoesNotExist:
        # The group doesn't exist, carry on
        pass
    # Look for LDAP group
    try:
        if request.user is not None and hasattr(request.user, "ldap_user"):
            groups = request.user.ldap_user.group_names
            if 'sns_%s_team' % str(instrument_id).lower() in groups \
                    or 'hfir_%s_team' % str(instrument_id).lower() in groups \
                    or 'snsadmin' in groups:
                return True
    except:
        # Couldn't find the user in the instrument LDAP group
        pass
    return request.user.is_staff


def is_experiment_member(request, instrument_id, experiment_id):
    """
        Determine whether a user is part of the given experiment.

        @param request: request object
        @param instrument_id: Instrument object
        @param experiment_id: IPTS object
    """
    if hasattr(settings, 'HIDE_RUN_DETAILS') and settings.HIDE_RUN_DETAILS is False:
        return True

    try:
        if request.user is not None and hasattr(request.user, "ldap_user"):
            groups = request.user.ldap_user.group_names
            return 'sns_%s_team' % str(instrument_id).lower() in groups \
                or 'sns-ihc' in groups \
                or 'snsadmin' in groups \
                or '%s' % experiment_id.expt_name.upper() in groups \
                or is_instrument_staff(request, instrument_id)
    except:
        logging.error("Error determining whether user %s is part of %s", str(request.user), str(experiment_id))
    return request.user.is_staff


def monitor(fn):
    """
        Function decorator to monitor page usage
    """
    def request_processor(request, *args, **kws):
        if settings.MONITOR_ON:
            user = None
            if request.user.is_authenticated:
                user = request.user

            visit = PageView(user=user,
                             view="%s.%s" % (fn.__module__, fn.__name__),
                             ip=request.META['REMOTE_ADDR'],
                             path=request.get_full_path())
            visit.save()
        return fn(request, *args, **kws)

    return request_processor
