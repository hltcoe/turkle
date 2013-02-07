# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Hit'
        db.create_table('hits_hit', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('title', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('description', self.gf('django.db.models.fields.TextField')()),
            ('awsmturk_template', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['hits.AwsMTurkTemplate'])),
            ('awsmturk_template_values', self.gf('jsonfield.fields.JSONField')()),
        ))
        db.send_create_signal('hits', ['Hit'])

        # Adding model 'AwsMTurkTemplate'
        db.create_table('hits_awsmturktemplate', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('template', self.gf('django.db.models.fields.TextField')()),
        ))
        db.send_create_signal('hits', ['AwsMTurkTemplate'])


    def backwards(self, orm):
        # Deleting model 'Hit'
        db.delete_table('hits_hit')

        # Deleting model 'AwsMTurkTemplate'
        db.delete_table('hits_awsmturktemplate')


    models = {
        'hits.awsmturktemplate': {
            'Meta': {'object_name': 'AwsMTurkTemplate'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'template': ('django.db.models.fields.TextField', [], {})
        },
        'hits.hit': {
            'Meta': {'object_name': 'Hit'},
            'awsmturk_template': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['hits.AwsMTurkTemplate']"}),
            'awsmturk_template_values': ('jsonfield.fields.JSONField', [], {}),
            'description': ('django.db.models.fields.TextField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        }
    }

    complete_apps = ['hits']