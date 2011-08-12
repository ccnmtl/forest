from django.http import HttpResponseRedirect, HttpResponse, HttpResponseNotFound, HttpRequest
from django.shortcuts import render_to_response
from pagetree.helpers import get_hierarchy, get_section_from_path, get_module, needs_submit, submitted
from django.template import RequestContext
from django.contrib.auth.decorators import login_required
from models import *
from forms import StandForm
from restclient import GET
import httplib2
import simplejson
from django.conf import settings
from munin.helpers import muninview
from pagetree.models import Section
from pagetree_export.exportimport import export_zip, import_zip
from pageblocks.exportimport import *
from quizblock.exportimport import *
import os

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

def has_responses(section):
    quizzes = [p.block() for p in section.pageblock_set.all() if hasattr(p.block(),'needs_submit') and p.block().needs_submit()]
    return quizzes != []

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
            section.reset(request.user)
            return HttpResponseRedirect(section.get_absolute_url())
        proceed = section.submit(request.POST,request.user)
        if proceed:
            return HttpResponseRedirect(section.get_next().get_absolute_url())
        else:
            # giving them feedback before they proceed
            return HttpResponseRedirect(section.get_absolute_url())
    else:
        instructor_link = has_responses(section)
        return dict(section=section,
                    module=module,
                    needs_submit=needs_submit(section),
                    is_submitted=submitted(section,request.user),
                    stand=request.stand,
                    modules=root.get_children(),
                    root=section.hierarchy.get_root(),
                    can_edit=can_edit,
                    can_admin=can_admin,
                    instructor_link=instructor_link,
                    )
@login_required
@rendered_with("main/instructor_page.html")
@stand()
def instructor_page(request,path):
    h = get_hierarchy(request.get_host())
    section = get_section_from_path(path,hierarchy=h)
    root = section.hierarchy.get_root()
    module = get_module(section)

    quizzes = [p.block() for p in section.pageblock_set.all() if hasattr(p.block(),'needs_submit') and p.block().needs_submit()]
    return dict(section=section,
                quizzes=quizzes,
                module=get_module(section),
                modules=root.get_children(),
                root=h.get_root())

@login_required
@rendered_with('main/edit_page.html')
@stand()
def edit_page(request,path):
    hierarchy = request.get_host()
    section = get_section_from_path(path,hierarchy=hierarchy)
    if not request.stand.can_edit(request.user):
        return HttpResponse("you do not have admin permission")
    can_admin = request.stand.can_admin(request.user)
    root = section.hierarchy.get_root()
    module = get_module(section)

    return dict(section=section,
                module=get_module(section),
                modules=root.get_children(),
                stand=request.stand,
                can_admin=can_admin,
                available_pageblocks=request.stand.available_pageblocks(),
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
        is_seed_stand = True
        if settings.DEBUG == False:
            # in production
            is_seed_stand = request.stand.hostname == "forest.ccnmtl.columbia.edu"
        return dict(stand=request.stand,
                    form=StandForm(instance=request.stand),
                    is_seed_stand=is_seed_stand
                    )

default_css = """
#header { background: #262; }
"""

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
            for pb in settings.PAGEBLOCKS:
                sapb = StandAvailablePageBlock.objects.create(stand=stand,block=pb)
            if hostname.endswith(".forest.ccnmtl.columbia.edu"):
                # if it's a *.forest site, just send them on their way
                return HttpResponseRedirect("http://%s/_stand/" % hostname)
            else:
                return dict(created=True,stand=stand)
    return dict(form=form)

@login_required
@stand_admin()
def delete_stand(request):
    if request.method == "POST":
        request.stand.delete()
        return HttpResponseRedirect("/")
    else:
        return HttpResponse("""
<form action="." method="post">
Are you sure? <input type="submit" value="YES!" />
</form>
""")

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
    if request.method == "POST":
        group_id = request.POST.get('group','')
        if group_id == "":
            return HttpResponse("no group selected")
        group = Group.objects.get(id=group_id)
        access = request.POST.get('access','student')
        r = StandGroup.objects.filter(stand=request.stand,group=group)
        if r.count() > 0:
            # if that group already exists, redirect them to the standgroup page
            # so they can just edit the access level, which is what they 
            # probably want
            return HttpResponseRedirect("/_stand/groups/%d/" % r[0].id)
        sg = StandGroup.objects.create(stand=request.stand,group=group,access=access)
    return HttpResponseRedirect("/_stand/groups/")

@login_required
@rendered_with("main/stand_groups.html")
@stand_admin()
def stand_groups(request):
    return dict(all_groups=Group.objects.all())    


@login_required
@rendered_with("main/edit_stand_group.html")
@stand_admin()
def edit_stand_group(request,id):
    standgroup = StandGroup.objects.get(id=id)
    if request.method == "POST":
        standgroup.access = request.POST.get("access","student")
        standgroup.save()
        return HttpResponseRedirect("/_stand/groups/")
    return dict(standgroup=standgroup)

@login_required
@stand_admin()
def delete_stand_group(request,id):
    standgroup = StandGroup.objects.get(id=id)
    standgroup.delete()
    return HttpResponseRedirect("/_stand/groups/")

@login_required
@rendered_with("main/manage_blocks.html")
@stand_admin()
def manage_blocks(request):
    if request.method == "POST":
        for block in settings.PAGEBLOCKS:
            enabled = request.POST.get(block,False)
            r = StandAvailablePageBlock.objects.filter(stand=request.stand,block=block)
            if enabled:
                if r.count() == 0:
                    sapb = StandAvailablePageBlock.objects.create(stand=request.stand,block=block)
                # otherwise, it already exists
            else:
                if r.count() > 0:
                    r.delete()
        return HttpResponseRedirect("/_stand/blocks/")
    
    all_blocks = []
    for block in settings.PAGEBLOCKS:
        r = StandAvailablePageBlock.objects.filter(stand=request.stand,block=block)
        all_blocks.append(dict(name=block,enabled=r.count()))
    return dict(all_blocks=all_blocks)

@muninview(config="""graph_title Total Stands
graph_vlabel stands""")
def total_stands(request):
    return [("stands",Stand.objects.all().count())]

@muninview(config="""graph_title Total Sections
graph_vlabel sections""")
def total_sections(request):
    return [("sections",Section.objects.all().count())]

@muninview(config="""graph_title Total StandUsers
graph_vlabel standusers""")
def total_standusers(request):
    return [("standusers",StandUser.objects.all().count())]

@login_required
@stand_admin()
def exporter(request):
    hierarchy = request.get_host()
    section = get_section_from_path('/', hierarchy=hierarchy)
    zip_filename = export_zip(section.hierarchy)

    with open(zip_filename) as zipfile:
        resp = HttpResponse(zipfile.read())
    resp['Content-Disposition'] = "attachment; filename=%s.zip" % section.hierarchy.name

    os.unlink(zip_filename)
    return resp

from zipfile import ZipFile

@rendered_with("main/import.html")
@login_required
@stand_admin()
def importer(request):
    if request.method == "GET":
        return {}
    file = request.FILES['file']
    zipfile = ZipFile(file)

    # If we exported the morx.com site, and we are now
    # visiting http://fleem.com/import/, we don't want
    # to touch the morx.com hierarchy -- instead we want
    # to import the bundle to the fleem.com hierarchy.
    hierarchy_name = request.get_host()
    hierarchy = import_zip(zipfile, hierarchy_name)

    url = hierarchy.get_absolute_url()
    url = '/' + url.lstrip('/') # sigh
    return HttpResponseRedirect(url)

@rendered_with("main/add_stand.html")
def cloner_created(request, ctx):
    return ctx

@rendered_with("main/clone.html")
@login_required
@stand_admin()
def cloner(request):
    if request.method == "GET":
        return {}

    new_hierarchy = request.POST['new_hierarchy']

    old_stand = get_stand(request.get_host())

    fake_request = HttpRequest()
    fake_request.method = "POST"
    fake_request.POST['hostname'] = new_hierarchy    
    fake_request.POST['title'] = old_stand.title
    fake_request.POST['css'] = old_stand.css
    fake_request.POST['description'] = old_stand.description
    fake_request.POST['access'] = old_stand.access
    form = StandForm(fake_request.POST)
    stand = form.save()

    su = StandUser.objects.create(stand=stand, user=request.user, access="admin")
    if request.POST.get('copy_userperms'):
        for standuser in StandUser.objects.filter(stand=old_stand).exclude(user=request.user):
            StandUser.objects.create(stand=stand, user=standuser.user, access=standuser.access
                                     ).save()

    for old_sapb in old_stand.standavailablepageblock_set.all():
        StandAvailablePageBlock.objects.create(
            stand=stand, block=old_sapb.block).save()

    hierarchy = request.get_host()
    section = get_section_from_path('/', hierarchy=hierarchy)
    zip_filename = export_zip(section.hierarchy)

    zipfile = ZipFile(zip_filename)
    
    hierarchy_name = new_hierarchy
    hierarchy = import_zip(zipfile, hierarchy_name)

    os.unlink(zip_filename)

    if new_hierarchy.endswith(".forest.ccnmtl.columbia.edu"):
        # if it's a *.forest site, just send them on their way
        return HttpResponseRedirect("http://%s/_stand/" % new_hierarchy)
    else:
        return cloner_created(request, dict(created=True,stand=stand))
