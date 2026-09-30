# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""An exercise of the centre's library (`crm.piani.librerie`): how it is done, the
muscles, a picture or a video, and whose they are. Not clinical: a plan says who
does it, and how much."""

import re

import frappe
from frappe import _
from frappe.model.document import Document

#: Only a player we know: the area shows it in a frame.
VIDEO = re.compile(r"^https://(www\.)?(youtube\.com/watch\?v=|youtu\.be/|vimeo\.com/)[A-Za-z0-9_\-?=&/]+$")


class CRMExercise(Document):
	def validate(self):
		if self.video_url and not VIDEO.match(self.video_url.strip()):
			frappe.throw(_("The video is a YouTube or Vimeo link"))
