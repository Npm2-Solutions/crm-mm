The schemas the XML is checked against (test_schema_ufficiale.py), as published:

- Schema_VFPR12_v1.2.3.xsd (in force from 01/04/2025: TD29, RF20)
  https://www.fatturapa.gov.it/export/documenti/fatturapa/v1.4/Schema_VFPR12_v1.2.3.xsd
  One change: the xmldsig import points at the copy beside it, so nothing is fetched.
- xmldsig-core-schema.xsd
  https://www.w3.org/TR/2002/REC-xmldsig-core-20020212/xmldsig-core-schema.xsd

A new version of the specification replaces both files whole.
