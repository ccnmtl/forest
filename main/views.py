from django.http import HttpResponseRedirect, HttpResponse, HttpResponseNotFound
from django.shortcuts import render_to_response
from pagetree.helpers import get_hierarchy, get_section_from_path, get_module, needs_submit, submitted
from django.template import RequestContext
from django.contrib.auth.decorators import login_required
from models import *
from forms import StandForm

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

@rendered_with('main/page.html')
def page(request,path):
    stand = get_stand(request.get_host())
    if not stand:
        return HttpResponse("no such site")
    hierarchy = request.get_host()
    section = get_section_from_path(path,hierarchy=hierarchy)

    root = section.hierarchy.get_root()
    module = get_module(section)
    if not stand.can_view(request.user):
        return HttpResponse("you do not have permission")
    can_edit = stand.can_edit(request.user)
    can_admin = stand.can_admin(request.user)
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
                    stand=stand,
                    modules=root.get_children(),
                    root=section.hierarchy.get_root(),
                    can_edit=can_edit,
                    can_admin=can_admin,
                    )

def instructor_page(request,path):
    return HttpResponse("instructor page")

@login_required
@rendered_with('main/edit_page.html')
def edit_page(request,path):
    stand = get_stand(request.get_host())
    if not stand:
        return HttpResponse("no such site")
    hierarchy = request.get_host()
    section = get_section_from_path(path,hierarchy=hierarchy)
    if not stand.can_edit(request.user):
        return HttpResponse("you do not have admin permission")
    can_admin = stand.can_admin(request.user)

    return dict(section=section,
                module=get_module(section),
                stand=stand,
                can_admin=can_admin,
                root=section.hierarchy.get_root())

def css(request):
    stand = get_stand(request.get_host())
    if not stand:
        return HttpResponse("no such site")

    return HttpResponse(stand.css,content_type="text/css")

@login_required
@rendered_with('main/edit_stand.html')
def edit_stand(request):
    stand = get_stand(request.get_host())
    if not stand:
        return HttpResponse("no such site")

    if not stand.can_admin(request.user):
        return HttpResponse("you do not have admin permission")
    if request.method == "POST":
        form = StandForm(request.POST,instance=stand)
        if form.is_valid():
            form.save()
        return HttpResponseRedirect("/_stand/")
    else:
        return dict(stand=stand,
                    form=StandForm(instance=stand))

@login_required
@rendered_with("main/add_stand.html")
def add_stand(request):
    form = StandForm()
    if request.method == "POST":
        form = StandForm(request.POST)
        if form.is_valid():
            stand = form.save()
            su = StandUser.objects.create(stand=stand,user=request.user,access="admin")
            return dict(created=True,stand=stand)
    return dict(form=form)

@login_required
def stand_add_group(request):
    pass

@login_required
def stand_add_user(request):
    pass


@login_required
def stand_groups(request):
    pass

@login_required
def stand_users(request):
    pass
