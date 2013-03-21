from django.core.urlresolvers import reverse
from django.shortcuts import redirect

# import code for encoding urls and generating md5 hashes
import hashlib
import socket
import logging
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
        # Login URL
        redirect_url = reverse('users.views.perform_login')
        redirect_url  += '?next=%s' % request.path
        
        # If we allow guests in, just return the function
        #if settings.ALLOW_GUESTS:
        #    return fn(request, *args, **kws)
        
        # If we don't allow guests but the user is authenticated, return the function
        if request.user.is_authenticated():
            return fn(request, *args, **kws)
        
        # If we allow users on a domain, check the user's IP
        elif len(settings.ALLOWED_DOMAIN)>0:
            ip_addr =  request.META['REMOTE_ADDR']

            # If the user is on the allowed domain, return the function
            if socket.gethostbyaddr(ip_addr)[0].endswith(settings.ALLOWED_DOMAIN):
                logging.warning("Allowing user on %s" % socket.gethostbyaddr(ip_addr)[0])
                return fn(request, *args, **kws)
            
            # If we allow a certain domain and the user is on the server, return the function
            elif socket.gethostbyaddr(ip_addr)[0] =='localhost':
                logging.warning("Allowing localhost user")
                return fn(request, *args, **kws)

        # If we made it here, we need to authenticate the user
        return redirect(redirect_url)   
    return request_processor

