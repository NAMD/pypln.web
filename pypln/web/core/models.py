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
from django.conf import settings
from django.contrib.auth.models import User
from django.dispatch import receiver
from django.db import models

from rest_framework.reverse import reverse
from rest_framework.authtoken.models import Token

from pypln.backend.mongodict_adapter import MongoDictAdapter
from pypln.web.core.storage import MongoDBBase64Storage

mongodb_storage = MongoDBBase64Storage()


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

class MongoDictProxy(MongoDictAdapter):

    def __getitem__(self, key):
        if key == "all_data":
            # This code is here because of the way MongoDict stores its values.
            # We need to pass all values as unicode strings to the serializer
            # so it gets rendered correctly. This code will be removed as soon
            # as MongoDict is not a part of this codebase anymore (this work
            # has been done in pypln.backend and should be done soon here).
            result = {}

            decode_list = lambda l: map(lambda s: s.decode('utf-8'), l)

            for k in self.keys():
                value = self[k]
                if isinstance(value, str):
                    value = value.decode('utf-8')
                elif k == u"lemmas":
                    value = decode_list(value)
                elif k == u"semantic_tags":
                    value = {tag: decode_list(tagged) for tag, tagged in
                            value.items()}
                result[k] = value
            return result

        return super(MongoDictProxy, self).__getitem__(key)

    def __getattr__(self, key):
        return self[key]


class Document(models.Model):
    blob = models.FileField(upload_to='/', storage=mongodb_storage)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    owner = models.ForeignKey('auth.User')
    corpus = models.ForeignKey(Corpus)

    def __unicode__(self):
        return self.blob.name

    @property
    def properties(self):
        return MongoDictProxy(doc_id=self.id,
                host=settings.MONGODB_CONFIG['host'],
                port=settings.MONGODB_CONFIG['port'],
                database=settings.MONGODB_CONFIG['database'])


class IndexedDocument(Document):
    doc_type = models.CharField(max_length=100)
    index_name = models.CharField(max_length=100)

# Create a authentication Token for each user it's created.
@receiver(models.signals.post_save, sender=User)
def create_auth_token(sender, instance=None, created=False, **kwargs):
    if created:
        Token.objects.create(user=instance)
