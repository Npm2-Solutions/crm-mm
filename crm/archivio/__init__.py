# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""The centre's archive: its files on the agency's object storage (doc 57).

What a centre uploads and DottorCloud writes for it - signed forms, reports,
documents, the attachments of a conversation - is a private file of the site.
Once it has been there a while (`regole.ATTESA`) it moves to an S3 bucket of the
agency's (`dottorcloud_archivio` in `common_site_config.json`), one prefix per
site, and on the server only an empty file keeps its name. Whoever opens it is
sent to the bucket by a link that lasts minutes, after the same permission check
the framework makes; code that reads it (`File.get_content`) has it brought back
first. The space a centre uses counts against what its plan includes
(`regole.compreso`), shown in Settings > The centre > Features.

- `regole`: pure - the signature (AWS Signature V4), the keys, what the plan
  includes, which files move;
- `s3`: the bucket, through `requests`;
- `archivio`: moving, bringing back, opening, deleting, the space used.
"""
