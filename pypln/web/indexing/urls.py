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

from django.conf.urls import patterns, url, include
from rest_framework.urlpatterns import format_suffix_patterns
from pypln.web.indexing.views import IndexDocument

urlpatterns = patterns('pypln.web.indexing.views',
    url(r'^index-document/$', IndexDocument.as_view(), name='index-document'),
)

urlpatterns = format_suffix_patterns(urlpatterns, allowed=['json', 'api'])
