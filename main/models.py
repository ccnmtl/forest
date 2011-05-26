from django.db import models
from django.contrib.auth.models import User, Group
import hashlib

class Stand(models.Model):
    title = models.CharField(max_length=256,default=u"",blank=True,null=True)
    hostname = models.CharField(max_length=256,db_index=True)
    created = models.DateTimeField(auto_now=True)
    css = models.TextField(default=u"",blank=True,null=True)
    description = models.TextField(default=u"",blank=True,null=True)

    access = models.CharField(max_length=256,default="open",
                              choices=(('open','Open Access'),
                                       ('login','Logged-in Users Only'),
                                       ('group','Users in Selected Group(s) Only'),
                                       ('whitelist','Whitelisted Users Only')))

    def __unicode__(self):
        return self.title

    def css_hash(self):
        sha1 = hashlib.sha1()
        sha1.update(self.css)
        return sha1.hexdigest()

    def can_edit(self,user):
        if not user:
            return False
        if user and user.is_anonymous():
            return False
        r = StandUser.objects.filter(stand=self,user=user)
        if r.count() > 0:
            su = r[0]
            if su.access in ["admin","faculty","ta"]:
                return True
        # TODO check groups
        return False

    def can_view(self,user):
        if not user:
            return False
        if self.access == "open":
            return True
        if user and user.is_anonymous():
            return False
        r = StandUser.objects.filter(stand=self,user=user)
        if r.count() > 0:
            return True
        # TODO check groups
        return False

    def can_admin(self,user):
        if not user:
            return False
        if user and user.is_anonymous():
            return False
        r = StandUser.objects.filter(stand=self,user=user)
        if r.count() > 0:
            su = r[0]
            if su.access == "admin":
                return True
        # TODO check groups
        return False


class StandUser(models.Model):
    stand = models.ForeignKey(Stand)
    user = models.ForeignKey(User)
    access = models.CharField(max_length=16,default="student")

class StandGroup(models.Model):
    stand = models.ForeignKey(Stand)
    group = models.ForeignKey(Group)
    access = models.CharField(max_length=16,default="student")

class StandSetting(models.Model):
    stand = models.ForeignKey(Stand)
    name = models.CharField(max_length=256,db_index=True)
    value = models.CharField(max_length=256)

def get_or_create_stand(hostname,user=None):
    r = Stand.objects.filter(hostname=hostname)
    if r.count() > 0:
        return r[0]
    s = Stand.objects.create(hostname=hostname,title=hostname)
    if user:
        su = StandUser.objects.create(stand=s,user=user,access="admin")
    return s
