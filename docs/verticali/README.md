# I verticali

Un verticale è un gestionale per un servizio costruito sul CRM: un modulo del piano
che registra un `Verticale` (`crm/verticali.py`) con le sue parole sopra quelle del
CRM, le sue regole sui motori del CRM e i suoi dati. Il CRM sotto resta neutro
(clienti, appuntamenti, area cliente); il verticale acceso lo fa parlare la sua
lingua (pazienti, visite, area del paziente).

| Verticale | Cartella | Codice | Marchio che lo porta |
|---|---|---|---|
| Clinica, il gestionale per i centri medici | [`clinica/`](./clinica/) | `crm/clinica` | DottorCloud ([`../marchi/dottorcloud/`](../marchi/dottorcloud/)) |

Un verticale nuovo (un centro estetico, una palestra) ha qui la sua cartella con
lo stesso nome del suo modulo nel codice. Quello che servirebbe uguale a un altro
servizio va nel CRM, e il verticale ci registra sopra le sue regole
([`clinica/design.md`](./clinica/design.md), «Tre strati»).
