<div align="center">

<img src="brand/logo/dottorcloud-orizzontale.svg" height="56" alt="DottorCloud">

**Il gestionale per i centri medici** · NPM2 Solutions Srl

</div>

## Cos'è

DottorCloud tiene tutto il centro medico in un posto solo, con ognuno che vede
solo quello che gli serve: le persone e i pazienti, l'agenda e le prenotazioni
online, la cartella clinica e i moduli da firmare, le fatture elettroniche e il
Sistema TS, WhatsApp e il telefono, i piani e i programmi che il paziente segue
dalla sua area, il marketing e le sue campagne.

## Dove leggere

| Cosa | Dove |
|---|---|
| Com'è fatto il codice, dove sono i file, le regole | [AGENTS.md](./AGENTS.md) |
| Il gestionale medico, fase per fase | [docs/gestionale-medico/](./docs/gestionale-medico/) |
| Prenotazioni online e piattaforme esterne | [docs/prenotazioni/](./docs/prenotazioni/) |
| Le pagine del prodotto, il telefono, la dashboard | [docs/progetto-ghl/](./docs/progetto-ghl/) |
| Contratti stabili e storia delle decisioni | [.pi/SPEC.md](./.pi/SPEC.md) · [.pi/ARCHIVE.md](./.pi/ARCHIVE.md) |
| Logo, design system, video, presentazione, inserzioni | [brand/](./brand/) |

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
