"""
    User management
"""
from django.shortcuts import render_to_response, redirect
from django.core.urlresolvers import reverse
from django.contrib.auth import login, logout, authenticate
from django.template import RequestContext

# Application-specific imports
from reporting_app import settings
from users.view_util import fill_template_values

def perform_login(request):
    """
        Perform user authentication
    """
    user = None  
    if request.method == 'POST':
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(username=username, password=password)
        login(request,user)
    
        # If we came from a given page and just needed 
        # authentication, go back to that page.
        if "next" in request.GET:
            redirect_url = request.GET["next"]
            return redirect(redirect_url)
    
    if request.user.is_authenticated():
        return redirect(reverse(settings.LANDING_VIEW))
    else:
        # Breadcrumbs
        breadcrumbs = "<a href='%s'>home</a> &rsaquo; login" % reverse(settings.LANDING_VIEW)
        
        template_values = {'breadcrumbs': breadcrumbs}
        template_values = fill_template_values(request, **template_values)
        return render_to_response('users/authenticate.html', template_values,
                              context_instance=RequestContext(request))

def perform_logout(request):
    """
        Logout user
    """
    logout(request)
    return redirect(reverse(settings.LANDING_VIEW))
        