# -*- coding:utf-8 -*-
#
# Copyright 2012 NAMD-EMAP-FGV
#
# This file is part of PyPLN. You can get more information at: http://pypln.org/.
#
# PyPLN is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# PyPLN is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with PyPLN.  If not, see <http://www.gnu.org/licenses/>.
from UserDict import DictMixin

from django.conf import settings
from django.contrib.auth.models import User
from django.dispatch import receiver
from django.db import models

from mongodict import MongoDict
from rest_framework.reverse import reverse
from rest_framework.authtoken.models import Token

from pypln.web.core.storage import GridFSStorage


gridfs_storage = GridFSStorage(location='/',
                               host=settings.MONGODB_CONFIG['host'],
                               port=settings.MONGODB_CONFIG['port'],
                               database=settings.MONGODB_CONFIG['database'],
                               collection=settings.MONGODB_CONFIG['gridfs_collection'])


class Corpus(models.Model):
    name = models.CharField(max_length=60)
    description = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    owner = models.ForeignKey('auth.User')

    class Meta:
        verbose_name_plural = 'corpora'
        unique_together = ('name', 'owner')

    def __unicode__(self):
        return self.name

class StoreProxy(DictMixin, dict):
    def __init__(self, document_id, store):
        self._store = store
        self.document_id = document_id

    def __getitem__(self, key):
        try:
            return self._store['id:{}:{}'.format(self.document_id, key)]
        except KeyError:
            if key == "_properties":
                msg = "Can't find information for document with id {document_id}"
            else:
                msg = "Can't find key {key} for document with id {document_id}"
            raise KeyError(msg.format(key=key, document_id=self.document_id))

    def __setitem__(self, key, value):
        raise AttributeError("StoreProxy is read-only.")

    def keys(self, *args, **kwargs):
        return self['_properties']


class Document(models.Model):
    blob = models.FileField(upload_to='/', storage=gridfs_storage)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    owner = models.ForeignKey('auth.User')
    corpus = models.ForeignKey(Corpus)

    _store = None

    def __unicode__(self):
        return self.blob.name

    @property
    def properties(self):
        if self.id is None:
            raise ValueError("This document was not saved, so you cannot "
                    "retrieve it's information from the backend.")
        if self._store is None:
            self._store = MongoDict(host=settings.MONGODB_CONFIG['host'],
                   port=settings.MONGODB_CONFIG['port'],
                   database=settings.MONGODB_CONFIG['database'],
                   collection=settings.MONGODB_CONFIG['analysis_collection'])
        return StoreProxy(self.id, self._store)


# Create a authentication Token for each user it's created.
@receiver(models.signals.post_save, sender=User)
def create_auth_token(sender, instance=None, created=False, **kwargs):
    if created:
        Token.objects.create(user=instance)
