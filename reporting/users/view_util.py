from django.core.urlresolvers import reverse
from django.shortcuts import redirect

# import code for encoding urls and generating md5 hashes
import hashlib
import socket
from reporting_app import settings

def fill_template_values(request, **template_args):
    """
        Fill the template argument items needed to populate
        side bars and other satellite items on the pages.
        
        Only the arguments common to all pages will be filled.
    """
    template_args['user'] = request.user
    if request.user.is_authenticated():
        if hasattr(settings, 'GRAVATAR_URL'):
            guess_email = "%s@%s" % (request.user.username, settings.ALLOWED_DOMAIN)
            gravatar_url = settings.GRAVATAR_URL+hashlib.md5(guess_email).hexdigest()+'?d=identicon'
            template_args['gravatar_url'] = gravatar_url
    else:
        request.user.username = 'Guest User'

    template_args['logout_url'] = reverse('users.views.perform_logout')
    redirect_url = reverse('users.views.perform_login')
    redirect_url  += '?next=%s' % request.path
    template_args['login_url'] = redirect_url
    return template_args

def login_or_local_required(fn):
    """
        Function decorator to check whether a user is allowed
        to see a view.
    """
    def request_processor(request, *args, **kws):
        if not request.user.is_authenticated():
            ip_addr =  request.META['REMOTE_ADDR']
            if not settings.ALLOW_GUESTS or \
                not (socket.gethostbyaddr(ip_addr)[0].endswith(settings.ALLOWED_DOMAIN) \
                     or socket.gethostbyaddr(ip_addr)[0] =='localhost'):
                redirect_url = reverse('users.views.perform_login')
                redirect_url  += '?next=%s' % request.path
                return redirect(redirect_url)
        return fn(request, *args, **kws)        
    return request_processor

