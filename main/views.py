from django.http import HttpResponseRedirect, HttpResponse, HttpResponseNotFound
from django.shortcuts import render_to_response
from pagetree.helpers import get_hierarchy, get_section_from_path, get_module, needs_submit, submitted
from django.template import RequestContext
from django.contrib.auth.decorators import login_required
from models import *
from forms import StandForm
from restclient import GET
import httplib2
import simplejson

class rendered_with(object):
    def __init__(self, template_name):
        self.template_name = template_name

    def __call__(self, func):
        def rendered_func(request, *args, **kwargs):
            items = func(request, *args, **kwargs)
            if type(items) == type({}):
                return render_to_response(self.template_name, items, context_instance=RequestContext(request))
            else:
                return items

        return rendered_func

class stand_admin(object):
    def __init__(*args,**kwargs):
        pass

    def __call__(self, func):
        def admin_func(request,*args,**kwargs):
            stand = get_stand(request.get_host())
            if not stand:
                return HttpResponse("no such site")
            if not stand.can_admin(request.user):
                return HttpResponse("you do not have admin permission")
            request.stand = stand
            items = func(request, *args, **kwargs)
            if type(items) == type({}):
                items['stand'] = stand
                items['can_admin'] = True
            return items
        return admin_func

class stand(object):
    def __init__(*args,**kwargs):
        pass
    def __call__(self,func):
        def stand_func(request,*args,**kwargs):
            stand = get_stand(request.get_host())
            if not stand:
                return HttpResponse("no such site")
            request.stand = stand
            items = func(request, *args, **kwargs)
            if type(items) == type({}):
                items['stand'] = stand
            return items
        return stand_func

@rendered_with('main/page.html')
@stand()
def page(request,path):
    hierarchy = request.get_host()
    section = get_section_from_path(path,hierarchy=hierarchy)

    root = section.hierarchy.get_root()
    module = get_module(section)
    if not request.stand.can_view(request.user):
        return HttpResponse("you do not have permission")
    can_edit = request.stand.can_edit(request.user)
    can_admin = request.stand.can_admin(request.user)
    if section.id == root.id:
        # trying to visit the root page
        if section.get_next():
            # just send them to the first child
            return HttpResponseRedirect(section.get_next().get_absolute_url())
        else:
            # send them to the stand admin interface
            return HttpResponseRedirect("/_stand/")

    if request.method == "POST":
        # user has submitted a form. deal with it
        if request.POST.get('action','') == 'reset':
            # it's a reset request
            for p in section.pageblock_set.all():
                if hasattr(p.block(),'needs_submit'):
                    if p.block().needs_submit():
                        p.block().clear_user_submissions(request.user)
            return HttpResponseRedirect(section.get_absolute_url())
        proceed = True
        for p in section.pageblock_set.all():
            if hasattr(p.block(),'needs_submit'):
                if p.block().needs_submit():
                    prefix = "pageblock-%d-" % p.id
                    data = dict()
                    for k in request.POST.keys():
                        if k.startswith(prefix):
                            # handle lists for multi-selects
                            v = request.POST.getlist(k)
                            if len(v) == 1:
                                data[k[len(prefix):]] = request.POST[k]
                            else:
                                data[k[len(prefix):]] = v
                    p.block().submit(request.user,data)
                    if hasattr(p.block(),'redirect_to_self_on_submit'):
                        # semi bug here?
                        # proceed will only be set by the last submittable
                        # block on the page. previous ones get ignored.
                        proceed = not p.block().redirect_to_self_on_submit()
        if proceed:
            return HttpResponseRedirect(section.get_next().get_absolute_url())
        else:
            # giving them feedback before they proceed
            return HttpResponseRedirect(section.get_absolute_url())
    else:
        return dict(section=section,
                    module=module,
                    needs_submit=needs_submit(section),
                    is_submitted=submitted(section,request.user),
                    stand=request.stand,
                    modules=root.get_children(),
                    root=section.hierarchy.get_root(),
                    can_edit=can_edit,
                    can_admin=can_admin,
                    )

def instructor_page(request,path):
    return HttpResponse("instructor page")

@login_required
@rendered_with('main/edit_page.html')
@stand()
def edit_page(request,path):
    hierarchy = request.get_host()
    section = get_section_from_path(path,hierarchy=hierarchy)
    if not request.stand.can_edit(request.user):
        return HttpResponse("you do not have admin permission")
    can_admin = request.stand.can_admin(request.user)

    return dict(section=section,
                module=get_module(section),
                stand=request.stand,
                can_admin=can_admin,
                root=section.hierarchy.get_root())

@stand()
def css(request):
    return HttpResponse(request.stand.css,content_type="text/css")

@login_required
@rendered_with('main/edit_stand.html')
@stand_admin()
def edit_stand(request):
    if request.method == "POST":
        form = StandForm(request.POST,instance=request.stand)
        if form.is_valid():
            form.save()
        return HttpResponseRedirect("/_stand/")
    else:
        return dict(stand=request.stand,
                    form=StandForm(instance=request.stand))

@login_required
@rendered_with("main/add_stand.html")
def add_stand(request):
    if not request.user.is_staff:
        return HttpResponse("only staff may access this")
    form = StandForm()
    if request.method == "POST":
        form = StandForm(request.POST)
        hostname = request.POST.get('hostname','')
        r = Stand.objects.filter(hostname=hostname)
        if r.count() > 0:
            return HttpResponse("a stand with that hostname already exists")
        if form.is_valid():
            stand = form.save()
            su = StandUser.objects.create(stand=stand,user=request.user,access="admin")
            return dict(created=True,stand=stand)
    return dict(form=form)

@login_required
@stand_admin()
def stand_add_user(request):
    if request.method == "POST":
        username = request.POST.get('user','')
        if username == "":
            username = request.POST.get('uni','')
        try:
            u = User.objects.get(username=username)
        except User.DoesNotExist:
            if username == "":
                return HttpResponse("no username or uni specified")
            u = User(username=username, password='forest user')
            u.set_unusable_password()
            u.email = u.username + "@columbia.edu"
            cdap_base = "http://cdap.ccnmtl.columbia.edu/"
            try:
                r = simplejson.loads(GET(cdap_base + "?uni=%s" % u.username))
                if r.get('found',False):
                    u.last_name = r.get('lastname',r.get('sn',''))
                    u.first_name = r.get('firstname',r.get('givenName',''))
            except httplib2.ServerNotFoundError:
                # cdap.ccnmtl.columbia.edu (or whatever the CDAP server is set to)
                # is probably not in /etc/hosts on this server
                pass
            u.save()
        r = StandUser.objects.filter(stand=request.stand,user=u)
        if r.count() > 0:
            # if that user already exists, redirect them to the standuser page
            # so they can just edit the access level, which is what they 
            # probably want
            return HttpResponseRedirect("/_stand/users/%d/" % r[0].id)
        access = request.POST.get('access')
        su = StandUser.objects.create(stand=request.stand,user=u,access=access)
    return HttpResponseRedirect("/_stand/users/")

@login_required
@rendered_with("main/edit_stand_user.html")
@stand_admin()
def edit_stand_user(request,id):
    standuser = StandUser.objects.get(id=id)
    if request.method == "POST":
        standuser.access = request.POST.get("access","student")
        standuser.save()
        return HttpResponseRedirect("/_stand/users/")
    return dict(standuser=standuser)

@login_required
@stand_admin()
def delete_stand_user(request,id):
    standuser = StandUser.objects.get(id=id)
    standuser.delete()
    return HttpResponseRedirect("/_stand/users/")

@login_required
@rendered_with("main/stand_users.html")
@stand_admin()
def stand_users(request):
    return dict(all_users=User.objects.all())

@login_required
@stand_admin()
def stand_add_group(request):
    pass

@login_required
@stand_admin()
def stand_groups(request):
    pass
