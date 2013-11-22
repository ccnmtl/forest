from django.conf import settings
from django.http import HttpResponseRedirect, HttpResponse, HttpRequest
from django.template.loader import render_to_string
from django.views.generic.base import View
from django.views.generic.edit import DeleteView
from django.views.generic.list import ListView
from django.utils.decorators import method_decorator
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
from pagetree.models import Section, PageBlock
import os
from annoying.decorators import render_to
from django.shortcuts import render


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


class StandMixin(object):
    def dispatch(self, *args, **kwargs):
        stand = get_stand(self.request.get_host())
        if not stand:
            return HttpResponse("no such site '%s'" % self.request.get_host())
        self.request.stand = stand
        items = super(StandMixin, self).dispatch(*args, **kwargs)
        if isinstance(items, dict):
            items['stand'] = stand
        return items


class StandAdminMixin(object):
    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        stand = get_stand(self.request.get_host())
        if not stand:
            return HttpResponse("no such site '%s'" % self.request.get_host())
        if not stand.can_admin(self.request.user):
            return permission_denied(
                self.request,
                "You do not have admin permission.")
        self.request.stand = stand
        items = super(StandAdminMixin, self).dispatch(*args, **kwargs)
        if isinstance(items, dict):
            items['stand'] = stand
            items['can_admin'] = True
        return items


class LoggedInMixin(object):
    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(LoggedInMixin, self).dispatch(*args, **kwargs)


class GetPostView(View):
    def get(self, request, path):
        return self.handler(request, path)

    def post(self, request, path):
        return self.handler(request, path)


class PageView(StandMixin, GetPostView):
    def handler(self, request, path):
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


class InstructorView(LoggedInMixin, StandMixin, GetPostView):
    def handler(self, request, path):
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


class EditView(LoggedInMixin, StandMixin, GetPostView):
    def handler(self, request, path):
        if not request.stand.can_edit(request.user):
            return permission_denied(request,
                                     "You are not an admin for this site")
        can_admin = request.stand.can_admin(request.user)
        hierarchy = request.get_host()

        return generic_edit_page(
            request, path, hierarchy=hierarchy,
            extra_context=dict(
                can_admin=can_admin,
                stand=request.stand,
                available_pageblocks=request.stand.available_pageblocks(),
            ),
        )


class CSSView(StandMixin, View):
    def get(self, request):
        return HttpResponse(request.stand.css, content_type="text/css")


class EditStandView(StandAdminMixin, View):
    template_name = 'main/edit_stand.html'

    def post(self, request):
        form = StandForm(request.POST, instance=request.stand)
        if form.is_valid():
            form.save()
        return HttpResponseRedirect("/_stand/")

    def get(self, request):
        is_seed_stand = True
        if not settings.DEBUG:
            # in production
            is_seed_stand = (request.stand.hostname ==
                             "forest.ccnmtl.columbia.edu")
        return render(
            request, self.template_name,
            dict(stand=request.stand,
                 form=StandForm(instance=request.stand),
                 is_seed_stand=is_seed_stand))

default_css = """
#header { background: #262; }
"""


class AddStandView(LoggedInMixin, View):
    template_name = "main/add_stand.html"

    def post(self, request):
        if not request.user.is_staff:
            return HttpResponse("only staff may access this")
        form = StandForm()
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
                return render(request, self.template_name,
                              dict(created=True, stand=stand, su=su))
        return render(request, self.template_name, dict(form=form))

    def get(self, request):
        if not request.user.is_staff:
            return HttpResponse("only staff may access this")
        form = StandForm()
        form = StandForm(request.POST)
        return render(request, self.template_name, dict(form=form))


class DeleteStandView(StandAdminMixin, View):
    def post(self, request):
        request.stand.get_root().hierarchy.delete()
        request.stand.get_root().delete()
        request.stand.delete()
        return HttpResponse("""Stand has been deleted. Thank you""")

    def get(self, request):
        return HttpResponse("""
<form action="." method="post">
Are you sure? <input type="submit" value="YES!" />
</form>
""")


class StandAddUserView(StandAdminMixin, View):
    def post(self, request):
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


class EditStandUserView(StandAdminMixin, View):
    template_name = "main/edit_stand_user.html"

    def post(self, request, id):
        standuser = StandUser.objects.get(id=id)
        standuser.access = request.POST.get("access", "student")
        standuser.save()
        return HttpResponseRedirect("/_stand/users/")

    def get(self, request, id):
        standuser = StandUser.objects.get(id=id)
        return render(request, self.template_name,
                      dict(standuser=standuser))


class DeleteStandUserView(StandAdminMixin, DeleteView):
    model = StandUser
    success_url = "/_stand/users/"


class StandUsersView(StandAdminMixin, ListView):
    template_name = "main/stand_users.html"
    model = User
    context_object_name = "all_users"


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


class StandGroupsView(StandAdminMixin, ListView):
    template_name = "main/stand_groups.html"
    model = Group
    context_object_name = "all_groups"


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


def is_block_allowed(block):
    return block.content_object.display_name in settings.EPUB_ALLOWED_BLOCKS


def is_image_block(block):
    return block.content_object.display_name == "Image Block"


def image_epub_filename(block):
    assert is_image_block(block)
    return "images/%d-%s" % (
        block.pk, os.path.basename(block.block().image.name))


def section_html(section):
    """ return a quick and dirty HTML version of the
    section suitable for epub """
    blocks = []
    for block in section.pageblock_set.all():
        if is_block_allowed(block):
            blocks.append(block)
        elif is_image_block(block):
            block.is_image_block = True
            block.epub_image_filename = image_epub_filename(block)
            blocks.append(block)
        else:
            block.unrenderable = True
            blocks.append(block)

    return render_to_string('epub/section.html',
                            dict(section=section, blocks=blocks))


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

    # gather images from all the blocks in the site
    for pb in PageBlock.objects.filter(section__hierarchy__name=hierarchy):
        if is_image_block(pb):
            fullpath = os.path.join(settings.MEDIA_ROOT, pb.block().image.name)
            im_book.addImage(fullpath, image_epub_filename(pb))

    depth_first_traversal = section.get_annotated_list()
    for (i, (s, ai)) in enumerate(depth_first_traversal):
        # skip the root
        if s.is_root():
            continue
        if s.hierarchy.name != hierarchy:
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

    old_hierarchy = old_stand.get_hierarchy()
    d = old_hierarchy.as_dict()

    # eventually, pagetree.hierarchy needs a .from_dict() method
    # that will overwrite the root
    for c in d['sections'][0]['children']:
        stand.get_root().add_child_section_from_dict(c)

    if new_hierarchy.endswith(".forest.ccnmtl.columbia.edu"):
        # if it's a *.forest site, just send them on their way
        return HttpResponseRedirect("http://%s/_stand/" % new_hierarchy)
    else:
        return cloner_created(request, dict(created=True, stand=stand))
