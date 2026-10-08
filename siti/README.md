# I siti dei marchi

Il sito pubblico di ogni marchio, uno per cartella, con la chiave del marchio
([`brand/`](../brand/)): oggi c'è [`dottorcloud/`](./dottorcloud/) per
`dottorcloud.com`.

Ogni sito ha le sue pagine e i suoi file, e prende logo, carattere, token e video
da `brand/<chiave>/`. Per essere pubblicato ha:

- `build.mjs`, che lo costruisce in `dist/` (ignorata da git);
- `test/*.test.mjs`, i test che devono passare prima di andare online;
- `deploy.sh <dominio> --crea --nginx`, che lo pubblica sul server HestiaCP di NPM2;
- `domini.txt`, i domini dove va, uno per riga.

Il workflow «Pubblica il sito» (`.github/workflows/sito-pubblica.yml`) fa girare i
test di ogni cartella e pubblica ogni sito sui suoi domini, a ogni push che cambia
`siti/` o `brand/`. Serve il segreto `HOSTING_SSH_KEY`: senza, il workflow lo dice e
non pubblica niente. Come si pubblica a mano e la prima volta:
[`dottorcloud/README.md`](./dottorcloud/README.md).

I siti dei marchi non sono le pagine pubbliche del gestionale (`/prenota`, l'area,
il sito che ogni centro fa con il builder): quelle sono di ogni centro.
