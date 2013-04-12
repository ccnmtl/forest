from django.db import models
from django.contrib.auth.models import User, Group
import hashlib
from django.db.models import get_model
from django.conf import settings
from pagetree.helpers import get_section_from_path

from south.modelsinspector import add_introspection_rules

add_introspection_rules(
    [],
    ["^django_extensions\.db\.fields\.CreationDateTimeField",
     "django_extensions.db.fields.ModificationDateTimeField",
     "sorl.thumbnail.fields.ImageWithThumbnailsField",
     "django_extensions.db.fields.UUIDField"])


class RequireUser(object):
    def check(self, checker):
        if not checker.user:
            return False


class DenyAnonymous(object):
    def check(self, checker):
        if checker.user.is_anonymous():
            return False


class AllowSuperUser(object):
    def check(self, checker):
        if checker.user.is_superuser:
            return True


class AllowOpen(object):
    def check(self, checker):
        if checker.stand.access == "open":
            return True


class AllowEditUser(object):
    def check(self, checker):
        if checker._access_in(["admin", "faculty", "ta"]):
            return True


class AllowInEditGroup(object):
    def check(self, checker):
        if checker.in_edit_group():
            return True


class AllowStandUser(object):
    def check(self, checker):
        r = checker.standuser()
        if r.count() > 0:
            return True


class AllowUserGroupCanView(object):
    def check(self, checker):
        if checker.user_group_can_x("view"):
            return True


class AllowAdminUser(object):
    def check(self, checker):
        if checker._access_in(["admin"]):
            return True


class AllowInAdminGroup(object):
    def check(self, checker):
        if checker.user_group_can_x("admin"):
            return True


class AccessChecker(object):
    """ centralize access control policy checks """
    def __init__(self, stand, user):
        self.stand = stand
        self.user = user

    def standuser(self):
        return StandUser.objects.filter(stand=self.stand, user=self.user)

    def _access_in(self, access_list):
        r = self.standuser()
        if r.count() > 0:
            su = r[0]
            if su.access in access_list:
                return True
        return False

    def check(self, policies):
        """ call each policy implementation in order
        short-circuiting out as soon as any of them
        give us an explicity ALLOW/DENY """
        for p in policies:
            status = p.check(self)
            if status is not None:
                return status
        return False

    def can_edit(self):
        policies = [
            RequireUser(),
            DenyAnonymous(),
            AllowSuperUser(),
            AllowEditUser(),
            AllowInEditGroup(),
        ]
        return self.check(policies)

    def can_view(self):
        policies = [
            AllowOpen(),
            RequireUser(),
            DenyAnonymous(),
            AllowSuperUser(),
            AllowStandUser(),
            AllowUserGroupCanView(),
        ]
        return self.check(policies)

    def can_admin(self):
        policies = [
            RequireUser(),
            DenyAnonymous(),
            AllowSuperUser(),
            AllowAdminUser(),
            AllowInAdminGroup(),
        ]
        return self.check(policies)

    def standgroups(self):
        return StandGroup.objects.filter(stand=self.stand)

    def in_edit_group(self):
        allowed_groups = {g.group.name for g in self.standgroups()
                          if g.access in ["admin", "faculty", "ta"]}
        user_groups = {g.name for g in self.user.groups.all()}
        return len(allowed_groups & user_groups) > 0

    def user_group_can_x(self, permission):
        """check if the user is in a group that has access"""
        allowed_groups = {g.group.name for g in self.standgroups()
                          if permission == "view" or g.access == permission}
        user_groups = {g.name for g in self.user.groups.all()}
        return len(allowed_groups & user_groups) > 0


class Stand(models.Model):
    title = models.CharField(max_length=256, default=u"", blank=True,
                             null=True)
    hostname = models.CharField(max_length=256, db_index=True)
    created = models.DateTimeField(auto_now=True)
    css = models.TextField(default=u"", blank=True, null=True)
    description = models.TextField(default=u"", blank=True, null=True)

    ACCESS_CHOICES = (('open', 'Open Access'),
                      ('login', 'Logged-in Users Only'),
                      ('group', 'Users in Selected Group(s) Only'),
                      ('whitelist', 'Whitelisted Users Only'))
    access = models.CharField(max_length=256, default="open",
                              choices=ACCESS_CHOICES)
    gated = models.BooleanField(default=False)

    def __unicode__(self):
        return self.title

    def css_hash(self):
        sha1 = hashlib.sha1()
        sha1.update(self.css)
        return sha1.hexdigest()

    def can_edit(self, user):
        return AccessChecker(self, user).can_edit()

    def can_view(self, user):
        return AccessChecker(self, user).can_view()

    def can_admin(self, user):
        return AccessChecker(self, user).can_admin()

    def available_pageblocks(self):
        enabled = [pb.block for pb in self.standavailablepageblock_set.all()]
        return [get_model(*pb.split('.')) for pb in settings.PAGEBLOCKS
                if pb in enabled]

    def get_root(self):
        """ return the Root pagetree.Section for this Stand """
        section = get_section_from_path("/", hierarchy=self.hostname)
        return section.hierarchy.get_root()

    def make_default_tree(self):
        """ when a new stand is created, we want to populate it
        with at least one Section and a bit of content to get things
        started so the user isn't just presented with a blank page"""
        self.get_root().add_child_section_from_dict(
            {
                'label': 'Welcome',
                'slug': 'welcome',
                'pageblocks': [
                    {'label': 'Welcome to your new Forest Site',
                     'css_extra': '',
                     'block_type': 'Text Block',
                     'body': 'You should now use the edit link to add content',
                     },
                ],
                'children': [],
            })


class StandUser(models.Model):
    stand = models.ForeignKey(Stand)
    user = models.ForeignKey(User)
    access = models.CharField(max_length=16, default="student")

    class Meta:
        ordering = ('user__last_name', 'user__first_name')


class StandGroup(models.Model):
    stand = models.ForeignKey(Stand)
    group = models.ForeignKey(Group)
    access = models.CharField(max_length=16, default="student")


class StandSetting(models.Model):
    stand = models.ForeignKey(Stand)
    name = models.CharField(max_length=256, db_index=True)
    value = models.CharField(max_length=256)


class StandAvailablePageBlock(models.Model):
    stand = models.ForeignKey(Stand)
    block = models.CharField(max_length=256, db_index=True)


def get_stand(hostname, user=None):
    r = Stand.objects.filter(hostname=hostname)
    if r.count() > 0:
        return r[0]
    return None
