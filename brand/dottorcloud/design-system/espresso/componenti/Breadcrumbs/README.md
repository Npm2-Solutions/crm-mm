# Breadcrumbs

L'intestazione della pagina: dove sei e l'azione principale.

## In frappe-ui
`<Breadcrumbs :items>` (`text-lg-medium`, separatore `/` in `ink-gray-4`) dentro l'header della pagina (alto 48px, filetto sotto); a destra i pulsanti.

## Personalizzazione DottorCloud
- L'ultima voce è in `ink-gray-9`; le precedenti in `ink-gray-5`.
- Le pagine principali (Agenda, Pazienti) hanno il titolo `page-title` (20px, bold) al posto delle briciole: è l'unico testo pesante della pagina.
- A destra al massimo un solid (con la coda della nuvola).
