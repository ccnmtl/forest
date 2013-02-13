from django.db import models
from django.contrib.auth.models import User, Group
import hashlib
from django.db.models import get_model
from django.conf import settings

from south.modelsinspector import add_introspection_rules

add_introspection_rules(
    [],
    ["^django_extensions\.db\.fields\.CreationDateTimeField",
     "django_extensions.db.fields.ModificationDateTimeField",
     "sorl.thumbnail.fields.ImageWithThumbnailsField",
     "django_extensions.db.fields.UUIDField"])


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

    def __unicode__(self):
        return self.title

    def css_hash(self):
        sha1 = hashlib.sha1()
        sha1.update(self.css)
        return sha1.hexdigest()

    def can_edit(self, user):
        if not user:
            return False
        if user.is_anonymous():
            return False
        if user.is_superuser:
            return True
        r = StandUser.objects.filter(stand=self, user=user)
        if r.count() > 0:
            su = r[0]
            if su.access in ["admin", "faculty", "ta"]:
                return True
        if self.in_edit_group(user):
            return True
        return False

    def in_edit_group(self, user):
        allowed_groups = []
        for g in StandGroup.objects.filter(stand=self):
            if g.access in ["admin", "faculty", "ta"]:
                allowed_groups.append(g.group.name)
        for g in user.groups.all():
            if g.name in allowed_groups:
                # bail as soon as we find a group affil that's allowed
                return True
        return False

    def can_view(self, user):
        if self.access == "open":
            return True
        if not user:
            return False
        if user.is_anonymous():
            return False
        if user.is_superuser:
            return True
        r = StandUser.objects.filter(stand=self, user=user)
        if r.count() > 0:
            return True
        if self.user_group_can_x(user, "view"):
            return True

        return False

    def user_group_can_x(self, user, permission):
        """check if the user is in a group that has access"""

        allowed_groups = []
        for g in StandGroup.objects.filter(stand=self):
            if permission == "view" or g.access == permission:
                allowed_groups.append(g.group.name)
        for g in user.groups.all():
            if g.name in allowed_groups:
                # bail as soon as we find a group affil that's allowed
                return True
        return False

    def can_admin(self, user):
        if not user:
            return False
        if user.is_anonymous():
            return False
        if user.is_superuser:
            return True
        r = StandUser.objects.filter(stand=self, user=user)
        if r.count() > 0:
            su = r[0]
            if su.access == "admin":
                return True
        if self.user_group_can_x(user, "admin"):
            return True
        return False

    def available_pageblocks(self):
        enabled = [pb.block for pb in self.standavailablepageblock_set.all()]
        return [get_model(*pb.split('.')) for pb in settings.PAGEBLOCKS
                if pb in enabled]


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
