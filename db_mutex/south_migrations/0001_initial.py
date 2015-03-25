# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'DBMutex'
        db.create_table(u'db_mutex_dbmutex', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('lock_id', self.gf('django.db.models.fields.CharField')(unique=True, max_length=256)),
            ('creation_time', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
        ))
        db.send_create_signal(u'db_mutex', ['DBMutex'])


    def backwards(self, orm):
        # Deleting model 'DBMutex'
        db.delete_table(u'db_mutex_dbmutex')


    models = {
        u'db_mutex.dbmutex': {
            'Meta': {'object_name': 'DBMutex'},
            'creation_time': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'lock_id': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '256'})
        }
    }

    complete_apps = ['db_mutex']