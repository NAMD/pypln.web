# -*- coding:utf-8 -*-
#
# Copyright 2013 NAMD-EMAP-FGV
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

from django.core.management.base import BaseCommand
from pypln.web.core.models import Document
from pypln.web.backend_adapter.pipelines import create_pipeline

class Command(BaseCommand):
    help = "Reruns the analysis for every document in the database."

    def handle(self, *args, **kwargs):
        docs = Document.objects.all()
        self.stdout.write("Sending pipelines for {} "
                "documents... ".format(len(docs)))
        for doc in docs:
            data = {"_id": str(doc.blob.file._id), "id": doc.id}
            create_pipeline(data)

        self.stdout.write("Done.")
