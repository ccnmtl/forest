# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding model 'Stand'
        db.create_table('main_stand', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('title', self.gf('django.db.models.fields.CharField')(default=u'', max_length=256, null=True, blank=True)),
            ('hostname', self.gf('django.db.models.fields.CharField')(max_length=256, db_index=True)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('css', self.gf('django.db.models.fields.TextField')(default=u'', null=True, blank=True)),
            ('description', self.gf('django.db.models.fields.TextField')(default=u'', null=True, blank=True)),
            ('access', self.gf('django.db.models.fields.CharField')(default='open', max_length=256)),
        ))
        db.send_create_signal('main', ['Stand'])

        # Adding model 'StandUser'
        db.create_table('main_standuser', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('stand', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['main.Stand'])),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'])),
            ('access', self.gf('django.db.models.fields.CharField')(default='student', max_length=16)),
        ))
        db.send_create_signal('main', ['StandUser'])

        # Adding model 'StandGroup'
        db.create_table('main_standgroup', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('stand', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['main.Stand'])),
            ('group', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.Group'])),
            ('access', self.gf('django.db.models.fields.CharField')(default='student', max_length=16)),
        ))
        db.send_create_signal('main', ['StandGroup'])

        # Adding model 'StandSetting'
        db.create_table('main_standsetting', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('stand', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['main.Stand'])),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=256, db_index=True)),
            ('value', self.gf('django.db.models.fields.CharField')(max_length=256)),
        ))
        db.send_create_signal('main', ['StandSetting'])

        # Adding model 'StandAvailablePageBlock'
        db.create_table('main_standavailablepageblock', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('stand', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['main.Stand'])),
            ('block', self.gf('django.db.models.fields.CharField')(max_length=256, db_index=True)),
        ))
        db.send_create_signal('main', ['StandAvailablePageBlock'])


    def backwards(self, orm):
        
        # Deleting model 'Stand'
        db.delete_table('main_stand')

        # Deleting model 'StandUser'
        db.delete_table('main_standuser')

        # Deleting model 'StandGroup'
        db.delete_table('main_standgroup')

        # Deleting model 'StandSetting'
        db.delete_table('main_standsetting')

        # Deleting model 'StandAvailablePageBlock'
        db.delete_table('main_standavailablepageblock')


    models = {
        'auth.group': {
            'Meta': {'object_name': 'Group'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        },
        'auth.permission': {
            'Meta': {'ordering': "('content_type__app_label', 'content_type__model', 'codename')", 'unique_together': "(('content_type', 'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        'auth.user': {
            'Meta': {'object_name': 'User'},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Group']", 'symmetrical': 'False', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'main.stand': {
            'Meta': {'object_name': 'Stand'},
            'access': ('django.db.models.fields.CharField', [], {'default': "'open'", 'max_length': '256'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'css': ('django.db.models.fields.TextField', [], {'default': "u''", 'null': 'True', 'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'default': "u''", 'null': 'True', 'blank': 'True'}),
            'hostname': ('django.db.models.fields.CharField', [], {'max_length': '256', 'db_index': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'default': "u''", 'max_length': '256', 'null': 'True', 'blank': 'True'})
        },
        'main.standavailablepageblock': {
            'Meta': {'object_name': 'StandAvailablePageBlock'},
            'block': ('django.db.models.fields.CharField', [], {'max_length': '256', 'db_index': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'stand': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['main.Stand']"})
        },
        'main.standgroup': {
            'Meta': {'object_name': 'StandGroup'},
            'access': ('django.db.models.fields.CharField', [], {'default': "'student'", 'max_length': '16'}),
            'group': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.Group']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'stand': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['main.Stand']"})
        },
        'main.standsetting': {
            'Meta': {'object_name': 'StandSetting'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '256', 'db_index': 'True'}),
            'stand': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['main.Stand']"}),
            'value': ('django.db.models.fields.CharField', [], {'max_length': '256'})
        },
        'main.standuser': {
            'Meta': {'ordering': "('user__last_name', 'user__first_name')", 'object_name': 'StandUser'},
            'access': ('django.db.models.fields.CharField', [], {'default': "'student'", 'max_length': '16'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'stand': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['main.Stand']"}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"})
        }
    }

    complete_apps = ['main']
