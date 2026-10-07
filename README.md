<div align="center">

<img src="brand/dottorcloud/logo/dottorcloud-orizzontale.svg" height="56" alt="DottorCloud">

**Il gestionale per i centri medici** · NPM2 Solutions Srl

</div>

## Cos'è

DottorCloud tiene tutto il centro medico in un posto solo, con ognuno che vede
solo quello che gli serve: le persone e i pazienti, l'agenda e le prenotazioni
online, la cartella clinica e i moduli da firmare, le fatture elettroniche e il
Sistema TS, WhatsApp e il telefono, i piani e i programmi che il paziente segue
dalla sua area, il marketing e le sue campagne.

È fatto a strati. Sotto c'è un **CRM** neutro, che serve a qualunque attività che
lavora con le persone (clienti, appuntamenti, conversazioni, fatture, area cliente);
sopra, i **verticali**, i gestionali per un servizio: oggi la clinica, che lo fa
parlare di pazienti e visite e aggiunge cartella, referti e dati sanitari; in cima,
i **marchi** con cui NPM2 li vende: oggi DottorCloud, che porta la clinica. Codice,
documenti e materiale seguono gli stessi strati: [docs/](./docs/), [brand/](./brand/),
[siti/](./siti/).

## Dove leggere

| Cosa | Dove |
|---|---|
| Com'è fatto il codice, dove sono i file, le regole | [AGENTS.md](./AGENTS.md) |
| I documenti, a strati: il CRM, i verticali, i marchi | [docs/](./docs/) |
| Il CRM di base: persone, agenda, conversazioni, fatture, telefono… (doc 00-59) | [docs/crm/](./docs/crm/) · prenotazioni in [docs/crm/prenotazioni/](./docs/crm/prenotazioni/) |
| Il gestionale per i centri medici, fase per fase | [docs/verticali/clinica/](./docs/verticali/clinica/) |
| Il listino e i documenti legali di DottorCloud | [docs/marchi/dottorcloud/](./docs/marchi/dottorcloud/) |
| Contratti stabili e storia delle decisioni | [.pi/SPEC.md](./.pi/SPEC.md) · [.pi/ARCHIVE.md](./.pi/ARCHIVE.md) |
| I marchi: logo, design system, video, presentazione, inserzioni (uno per cartella) | [brand/](./brand/) · DottorCloud in [brand/dottorcloud/](./brand/dottorcloud/) |
| I siti dei marchi (uno per cartella) | [siti/](./siti/) · `dottorcloud.com` in [siti/dottorcloud/](./siti/dottorcloud/) |

## Sviluppo

L'app gira dentro un bench, con MariaDB e Redis. In una cartella bench:

```bash
bench get-app crm <indirizzo di questo repository>
bench new-site <sito>
bench --site <sito> install-app crm
bench --site <sito> migrate
bench start
```

Il CRM è in `frontend/` (Vue 3), l'area del paziente in `frontend/src/area/`:

```bash
cd frontend
yarn install
yarn dev          # sviluppo
yarn build        # CRM e area del paziente
yarn test:run     # i test del browser
```

I test del server: `bench --site <sito> run-tests --app crm`.

## Licenza

DottorCloud è software libero, con licenza GNU Affero General Public License,
versione 3 ([LICENSE](./LICENSE)). Nasce da un CRM open source: gli avvisi di
copyright dei suoi autori restano nei file sorgenti e in LICENSE, come la licenza
chiede. Chi usa DottorCloud attraverso la rete ha diritto a ricevere il codice
sorgente della versione che usa.
