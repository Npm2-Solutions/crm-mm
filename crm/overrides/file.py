# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""A file, as DottorCloud keeps it (doc 57).

A private file may be on the agency's archive, an empty file on the server keeping
its name (`crm.archivio`). Whatever reads its content - the framework's
`get_content`, a thumbnail, a zip opened, a file made public - finds it whole:
brought back first.
"""

from frappe.core.doctype.file.file import File
from frappe.utils import cint

from crm.archivio import archivio


class FileDiDottorCloud(File):
	def _sul_disco(self):
		if not self.is_folder and self.file_url:
			archivio.riporta(self.file_url)

	def get_content(self, encodings=None):
		if not self.get("content"):
			self._sul_disco()
		return super().get_content(encodings)

	def make_thumbnail(self, *args, **kwargs):
		self._sul_disco()
		return super().make_thumbnail(*args, **kwargs)

	def unzip(self):
		self._sul_disco()
		return super().unzip()

	def optimize_file(self):
		self._sul_disco()
		return super().optimize_file()

	def handle_is_private_changed(self):
		# made public: the file moves to the public folder, whole
		if not cint(self.is_private):
			self._sul_disco()
		return super().handle_is_private_changed()
