The schemas the XML is checked against (test_schema_ufficiale.py), as published:

- Schema_del_file_xml_FatturaPA_v1.2.2.xsd
  https://www.fatturapa.gov.it/export/documenti/fatturapa/v1.2.2/Schema_del_file_xml_FatturaPA_v1.2.2.xsd
  One change: the xmldsig import points at the copy beside it, so nothing is fetched.
- xmldsig-core-schema.xsd
  https://www.w3.org/TR/2002/REC-xmldsig-core-20020212/xmldsig-core-schema.xsd

A new version of the specification replaces both files whole.
