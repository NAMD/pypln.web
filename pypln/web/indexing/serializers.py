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
from rest_framework import serializers
from rest_framework.reverse import reverse

INDEX_NAME_ERROR_MSG = ("Invalid index_name. "
                "Remember stored index names are always prefixed with your "
                "username. See the documentation for indexing documents for "
                "details")

class QuerySerializer(serializers.Serializer):
    index_name = serializers.CharField(max_length=100)
    q = serializers.CharField(max_length=256, allow_blank=True)

    def validate_index_name(self, value):
        if not value.startswith(self.context['request'].user.username):
            raise serializers.ValidationError(INDEX_NAME_ERROR_MSG)
        return value
