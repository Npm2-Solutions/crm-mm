# I documenti

I documenti seguono gli strati del codice: un **CRM** di base, neutro, che serve
a qualunque attività che lavora con le persone; sopra, i **verticali**, i
gestionali per un servizio (oggi la clinica, il gestionale per i centri medici);
in cima, i **marchi** con cui NPM2 li vende (oggi DottorCloud). Un marchio porta un
verticale, un verticale si appoggia al CRM, mai il contrario.

| Strato | Cartella | Nel codice | Cosa c'è |
|---|---|---|---|
| Il CRM | [`crm/`](./crm/) | `crm/` (tutto quello che non è un verticale) | I documenti numerati (00-59): persone, trattative, agenda, conversazioni, telefono, fatturazione, moduli, area cliente, impostazioni, permessi e piano; le [prenotazioni](./crm/prenotazioni/); la [gerarchia degli utenti](./crm/gerarchia-utenti.md); il [collaudo prima della produzione](./crm/64-collaudo/) |
| I verticali | [`verticali/`](./verticali/) | un modulo del piano che registra un `Verticale` (`crm/verticali.py`) | [`clinica/`](./verticali/clinica/): il gestionale per i centri medici (`crm/clinica`), il suo design a tre strati, i requisiti, le ricerche |
| I marchi | [`marchi/`](./marchi/) | `crm/marchio.py`, `brand/<marchio>/`, `siti/<marchio>/` | [`dottorcloud/`](./marchi/dottorcloud/): il listino e i documenti legali |

Dove va un documento nuovo: nel CRM se serve a ogni attività (un centro estetico,
una palestra, un centro medico), in un verticale se esiste solo per quel servizio
(i dati sanitari, la cartella), in un marchio se riguarda come lo si vende (prezzi,
contratti, privacy del fornitore). I documenti del CRM sono numerati e il numero non
cambia: il codice li cita come «doc 57».
