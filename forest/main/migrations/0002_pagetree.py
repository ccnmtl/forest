# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):
    depends_on = (
        ("pagetree", "0001_initial"),
    )

    def forwards(self):
        pass

    def backwards(self):
        pass
