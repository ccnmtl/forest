from django.db import models
from django.contrib.auth.models import User

class Stand(models.Model):
    title = models.CharField(max_length=256,default=u"",blank=True,null=True)
    hostname = models.CharField(max_length=256,db_index=True)
    created = models.DateTimeField(auto_now=True)
    css = models.TextField(default=u"",blank=True,null=True)
    description = models.TextField(default=u"",blank=True,null=True)

    def __unicode__(self):
        return self.title

class StandUser(models.Model):
    stand = models.ForeignKey(Stand)
    user = models.ForeignKey(User)
    access = models.CharField(max_length=16,default="student")

class StandSetting(models.Model):
    stand = models.ForeignKey(Stand)
    name = models.CharField(max_length=256,db_index=True)
    value = models.CharField(max_length=256)

