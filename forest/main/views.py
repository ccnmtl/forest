from cStringIO import StringIO
from django.conf import settings
from django.http import HttpResponseRedirect, HttpResponse, HttpRequest
from pagetree.helpers import get_section_from_path
from pagetree.generic.views import generic_view_page
from pagetree.generic.views import generic_instructor_page
from pagetree.generic.views import generic_edit_page
from django.contrib.auth.decorators import login_required
from epubbuilder import epub
from forest.main.models import get_stand, Stand
from forest.main.models import StandUser, User, Group, StandGroup
from forest.main.models import StandAvailablePageBlock
from forest.main.forms import StandForm
from restclient import GET
import httplib2
import simplejson
from munin.helpers import muninview
from pagetree.models import Section
from pagetree_export.exportimport import export_zip, import_zip
import os
from annoying.decorators import render_to
from django.shortcuts import render
from zipfile import ZipFile


class stand_admin(object):
    def __init__(*args, **kwargs):
        pass

    def __call__(self, func):
        def admin_func(request, *args, **kwargs):
            stand = get_stand(request.get_host())
            if not stand:
                return HttpResponse("no such site '%s'" % request.get_host())
            if not stand.can_admin(request.user):
                return permission_denied(
                    request,
                    "You do not have admin permission.")
            request.stand = stand
            items = func(request, *args, **kwargs)
            if isinstance(items, dict):
                items['stand'] = stand
                items['can_admin'] = True
            return items
        return admin_func


def permission_denied(request, message=""):
    return render(request, "403.html",
                  dictionary=dict(message=message), status=403)


class stand(object):
    def __init__(*args, **kwargs):
        pass

    def __call__(self, func):
        def stand_func(request, *args, **kwargs):
            stand = get_stand(request.get_host())
            if not stand:
                return HttpResponse("no such site '%s'" % request.get_host())
            request.stand = stand
            items = func(request, *args, **kwargs)
            if isinstance(items, dict):
                items['stand'] = stand
            return items
        return stand_func


@stand()
def page(request, path):
    if not request.stand.can_view(request.user):
        if not request.user.is_anonymous():
            return permission_denied(request)
        return HttpResponseRedirect("/accounts/login/?next=/")
    if (request.stand.gated
            and request.user.is_anonymous()):
        return HttpResponseRedirect("/accounts/login/?next=/")
    can_edit = request.stand.can_edit(request.user)
    can_admin = request.stand.can_admin(request.user)

    hierarchy = request.get_host()
    return generic_view_page(
        request, path,
        hierarchy=hierarchy,
        gated=request.stand.gated,
        extra_context=dict(
            stand=request.stand,
            can_edit=can_edit,
            can_admin=can_admin,
        ),
        no_root_fallback_url="/_stand/",
    )


@login_required
@stand()
def instructor_page(request, path):
    if not request.stand.can_view(request.user):
        if not request.user.is_anonymous():
            return permission_denied(request)
        return HttpResponseRedirect("/accounts/login/?next=/")
    # TODO: enforce that they are an instructor
    hierarchy = request.get_host()
    return generic_instructor_page(
        request, path,
        hierarchy=hierarchy,
        extra_context=dict(
            stand=request.stand,
        )
    )


@login_required
@stand()
def edit_page(request, path):
    if not request.stand.can_edit(request.user):
        return permission_denied(request, "You are not an admin for this site")
    can_admin = request.stand.can_admin(request.user)
    hierarchy = request.get_host()

    return generic_edit_page(
        request, path, hierarchy=hierarchy,
        extra_context=dict(
            can_admin=can_admin,
            stand=stand,
            available_pageblocks=request.stand.available_pageblocks(),
        ),
    )


@stand()
def css(request):
    return HttpResponse(request.stand.css, content_type="text/css")


@login_required
@render_to('main/edit_stand.html')
@stand_admin()
def edit_stand(request):
    if request.method == "POST":
        form = StandForm(request.POST, instance=request.stand)
        if form.is_valid():
            form.save()
        return HttpResponseRedirect("/_stand/")
    else:
        is_seed_stand = True
        if not settings.DEBUG:
            # in production
            is_seed_stand = (request.stand.hostname ==
                             "forest.ccnmtl.columbia.edu")
        return dict(stand=request.stand,
                    form=StandForm(instance=request.stand),
                    is_seed_stand=is_seed_stand
                    )

default_css = """
#header { background: #262; }
"""


@login_required
@render_to("main/add_stand.html")
def add_stand(request):
    if not request.user.is_staff:
        return HttpResponse("only staff may access this")
    form = StandForm()
    if request.method == "POST":
        form = StandForm(request.POST)
        hostname = request.POST.get('hostname', '')
        r = Stand.objects.filter(hostname=hostname)
        if r.count() > 0:
            return HttpResponse("a stand with that hostname already exists")
        if form.is_valid():
            stand = form.save()
            su = StandUser.objects.create(stand=stand, user=request.user,
                                          access="admin")
            for pb in settings.PAGEBLOCKS:
                StandAvailablePageBlock.objects.create(stand=stand,
                                                       block=pb)
            stand.make_default_tree()
            if hostname.endswith(".forest.ccnmtl.columbia.edu"):
                # if it's a *.forest site, just send them on their way
                return HttpResponseRedirect("http://%s/_stand/" % hostname)
            else:
                return dict(created=True, stand=stand, su=su)
    return dict(form=form)


@login_required
@stand_admin()
def delete_stand(request):
    if request.method == "POST":
        request.stand.get_root().hierarchy.delete()
        request.stand.get_root().delete()
        request.stand.delete()
        return HttpResponse("""Stand has been deleted. Thank you""")
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
        username = request.POST.get('user', '')
        if username == "":
            username = request.POST.get('uni', '')
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
                if r.get('found', False):
                    u.last_name = r.get('lastname', r.get('sn', ''))
                    u.first_name = r.get('firstname', r.get('givenName', ''))
            except httplib2.ServerNotFoundError:
                # cdap.ccnmtl.columbia.edu
                # (or whatever the CDAP server is set to)
                # is probably not in /etc/hosts on this server
                pass
            u.save()
        r = StandUser.objects.filter(stand=request.stand, user=u)
        if r.count() > 0:
            # if that user already exists, redirect them to the standuser page
            # so they can just edit the access level, which is what they
            # probably want
            return HttpResponseRedirect("/_stand/users/%d/" % r[0].id)
        access = request.POST.get('access')
        StandUser.objects.create(stand=request.stand, user=u,
                                 access=access)
    return HttpResponseRedirect("/_stand/users/")


@login_required
@render_to("main/edit_stand_user.html")
@stand_admin()
def edit_stand_user(request, id):
    standuser = StandUser.objects.get(id=id)
    if request.method == "POST":
        standuser.access = request.POST.get("access", "student")
        standuser.save()
        return HttpResponseRedirect("/_stand/users/")
    return dict(standuser=standuser)


@login_required
@stand_admin()
def delete_stand_user(request, id):
    standuser = StandUser.objects.get(id=id)
    standuser.delete()
    return HttpResponseRedirect("/_stand/users/")


@login_required
@render_to("main/stand_users.html")
@stand_admin()
def stand_users(request):
    return dict(all_users=User.objects.all())


@login_required
@stand_admin()
def stand_add_group(request):
    if request.method == "POST":
        group_id = request.POST.get('group', '')
        if group_id == "":
            return HttpResponse("no group selected")
        group = Group.objects.get(id=group_id)
        access = request.POST.get('access', 'student')
        r = StandGroup.objects.filter(stand=request.stand, group=group)
        if r.count() > 0:
            # if that group already exists, redirect them to
            # the standgroup page
            # so they can just edit the access level, which is what they
            # probably want
            return HttpResponseRedirect("/_stand/groups/%d/" % r[0].id)
        StandGroup.objects.create(stand=request.stand,
                                  group=group, access=access)
    return HttpResponseRedirect("/_stand/groups/")


@login_required
@render_to("main/stand_groups.html")
@stand_admin()
def stand_groups(request):
    return dict(all_groups=Group.objects.all())


@login_required
@render_to("main/edit_stand_group.html")
@stand_admin()
def edit_stand_group(request, id):
    standgroup = StandGroup.objects.get(id=id)
    if request.method == "POST":
        standgroup.access = request.POST.get("access", "student")
        standgroup.save()
        return HttpResponseRedirect("/_stand/groups/")
    return dict(standgroup=standgroup)


@login_required
@stand_admin()
def delete_stand_group(request, id):
    standgroup = StandGroup.objects.get(id=id)
    standgroup.delete()
    return HttpResponseRedirect("/_stand/groups/")


@login_required
@render_to("main/manage_blocks.html")
@stand_admin()
def manage_blocks(request):
    if request.method == "POST":
        for block in settings.PAGEBLOCKS:
            enabled = request.POST.get(block, False)
            r = StandAvailablePageBlock.objects.filter(stand=request.stand,
                                                       block=block)
            if enabled:
                if r.count() == 0:
                    StandAvailablePageBlock.objects.create(stand=request.stand,
                                                           block=block)
                # otherwise, it already exists
            else:
                if r.count() > 0:
                    r.delete()
        return HttpResponseRedirect("/_stand/blocks/")

    all_blocks = []
    for block in settings.PAGEBLOCKS:
        r = StandAvailablePageBlock.objects.filter(stand=request.stand,
                                                   block=block)
        all_blocks.append(dict(name=block, enabled=r.count()))
    return dict(all_blocks=all_blocks)


@muninview(config="""graph_title Total Stands
graph_vlabel stands""")
def total_stands(request):
    return [("stands", Stand.objects.all().count())]


@muninview(config="""graph_title Total Sections
graph_vlabel sections""")
def total_sections(request):
    return [("sections", Section.objects.all().count())]


@muninview(config="""graph_title Total StandUsers
graph_vlabel standusers""")
def total_standusers(request):
    return [("standusers", StandUser.objects.all().count())]


@login_required
@stand_admin()
def exporter(request):
    hierarchy = request.get_host()
    section = get_section_from_path('/', hierarchy=hierarchy)
    zip_filename = export_zip(section.hierarchy)

    with open(zip_filename) as zipfile:
        resp = HttpResponse(zipfile.read())
    resp['Content-Disposition'] = ("attachment; filename=%s.zip" %
                                   section.hierarchy.name)

    os.unlink(zip_filename)
    return resp


def section_html(section):
    """ return a quick and dirty HTML version of the
    section suitable for epub """
    parts = [
        """<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.1//EN" """,
        """"http://www.w3.org/TR/xhtml11/DTD/xhtml11.dtd">""",
        """<html xmlns="http://www.w3.org/1999/xhtml">""",
        """<head><title>%s</title></head>""" % section.label,
        "<body>",
    ]

    if section.pageblock_set.all().count() == 0:
        parts.append("<p>[EMPTY SECTION]</p>")

    for block in section.pageblock_set.all():
        if block.label:
            parts.append("<h2>" + block.label + "</h2>")
        if block.content_object.display_name != "Text Block":
            parts.append(
                "<p>Unrenderable Block: %s</p>" %
                block.content_object.display_name)
            continue
        parts.append(block.render())
    parts.append("</body></html>")
    return "\n".join(parts)


@login_required
@stand_admin()
def epub_exporter(request):
    hierarchy = request.get_host()
    section = get_section_from_path('/', hierarchy=hierarchy)

    im_book = epub.EpubBook(template_dir=settings.EPUB_TEMPLATE_DIR)
    im_book.setTitle(request.stand.title)
    im_book.addCreator('CCNMTL')
    im_book.addMeta('date', '2013', event='publication')

    im_book.addTitlePage()
    im_book.addTocPage()

    depth_first_traversal = section.get_annotated_list()
    for (i, (s, ai)) in enumerate(depth_first_traversal):
        # skip the root
        if s.is_root():
            continue
        title = s.label
        if s.label == '':
            title = "chapter %d" % i
        n = im_book.addHtml('', '%d.html' % i,
                            section_html(s))
        im_book.addSpineItem(n)
        depth = ai['level']
        if depth == 1:
            depth = None
        im_book.addTocMapNode(n.destPath, title, depth=depth)

    out = im_book.make_epub()
    resp = HttpResponse(out.getvalue(),
                        mimetype="application/x-zip-compressed")
    resp['Content-Disposition'] = ("attachment; filename=%s.epub" %
                                   section.hierarchy.name)
    return resp


@render_to("main/import.html")
@login_required
@stand_admin()
def importer(request):
    if request.method == "GET":
        return {}
    f = request.FILES['file']
    zipfile = ZipFile(f)

    # If we exported the morx.com site, and we are now
    # visiting http://fleem.com/import/, we don't want
    # to touch the morx.com hierarchy -- instead we want
    # to import the bundle to the fleem.com hierarchy.
    hierarchy_name = request.get_host()
    hierarchy = import_zip(zipfile, hierarchy_name)

    url = hierarchy.get_absolute_url()
    url = '/' + url.lstrip('/')  # sigh
    return HttpResponseRedirect(url)


@render_to("main/add_stand.html")
def cloner_created(request, ctx):
    return ctx


@render_to("main/clone.html")
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

    StandUser.objects.create(stand=stand, user=request.user,
                             access="admin")
    if request.POST.get('copy_userperms'):
        q = StandUser.objects.filter(stand=old_stand)
        for standuser in q.exclude(user=request.user):
            StandUser.objects.create(stand=stand, user=standuser.user,
                                     access=standuser.access).save()

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
        return cloner_created(request, dict(created=True, stand=stand))
