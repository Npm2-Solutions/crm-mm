# 35 — Le impostazioni a due livelli: prima la parte del lavoro, poi la cosa

> ✅ **FATTO (01/10/2026)**. Il doc 31 aveva messo le impostazioni in ordine, ma
> la colonna di sinistra restava lunga: trentatré voci con un'icona ciascuna,
> undici gruppi scritti piccoli sopra, e per trovare dove si imposta il piano di
> un paziente bisognava già sapere che cosa fosse una "Libreria". Ora a sinistra
> ci sono solo le parti del lavoro, ognuna con la sua icona; a destra quella che
> si apre dice a cosa serve e mostra le sue voci, ognuna con una riga che spiega
> cosa si imposta lì.

## Com'è

```
┌──────────────────┬──────────────────────────────────────────────────────┐
│ Impostazioni     │  [icona]  Agenda                                       │
│                  │  Cosa offre il centro, quando e dove: servizi, orari,  │
│ ◯ Il tuo account │  sale, promemoria, prenotazione online.                │
│ ▣ Il centro      │ ┌────────────────────────────────────────────────────┐ │
│ ▦ Agenda       ◀ │ │ Servizi                                          › │ │
│ ⚇ Pazienti       │ │ Cosa offre il centro, i suoi listini e i suoi      │ │
│                  │ │ abbonamenti.                                       │ │
│ ▥ Trattative     │ ├────────────────────────────────────────────────────┤ │
│ ✉ E-mail         │ │ Orari e turni                                    › │ │
│ ✆ WhatsApp       │ │ Quando è aperto il centro, e chi lavora quando.    │ │
│ ☏ Telefono       │ ├────────────────────────────────────────────────────┤ │
│ 📣 Marketing      │ │ …                                                  │ │
│ ⎙ Fatturazione   │ └────────────────────────────────────────────────────┘ │
│ ⚡ Integrazioni   │                                                        │
└──────────────────┴──────────────────────────────────────────────────────┘
```

- **A sinistra le categorie**, una riga ciascuna, con l'icona: le icone stanno sulle
  parti del lavoro, non sulle trentatré voci, dove si confondevano (quattro
  calendari, tre ingranaggi). Ognuno vede le sue (doc 30): chi ne ha una sola vede
  quella.
- **A destra la categoria**: il suo nome, una frase su cosa ci si imposta, e le sue
  voci, ognuna con una riga sola ("Librerie — Con cosa si scrivono i piani:
  esercizi, alimenti."). Si legge prima di aprire.
- **La voce aperta** prende tutta la destra, con le sue schede come prima (doc 31) e
  sopra la strada per tornare alla categoria: "‹ Agenda".
- **Sul telefono** è la stessa strada in tre passi: le categorie, la categoria con
  le sue voci, la voce; la freccia in alto torna indietro di un passo.
- **I link che esistevano** aprono ancora la loro pagina sulla scheda giusta, con la
  categoria accesa a sinistra: `?settings=Price Lists` apre Agenda › Servizi sulla
  scheda Listini. Le impostazioni aperte senza una pagina mostrano la prima
  categoria.
- **Le parole** sono quelle della persona: le frasi sono tradotte, e con la clinica
  "Clienti" si legge "Pazienti" (`crm/clinica/parole.py`).

## Come è fatto

| File | Cosa fa |
|---|---|
| `frontend/src/utils/impostazioni.js` | Ogni gruppo e ogni voce hanno la loro `description`: una riga, al massimo cento caratteri |
| `frontend/src/components/Settings/Settings.vue` | A sinistra i gruppi (`ICONE` per chiave di gruppo), a destra la categoria aperta (`categoria`) o la voce aperta (`activeTab`) con la strada indietro; sul telefono `indietro()` torna di un passo |
| `crm/locale/it.po` | Le frasi in italiano |

Una pagina nuova, oltre a quello che dice il doc 31: la sua riga di descrizione,
che dice cosa ci si imposta con le parole di chi la apre, e la traduzione.

## Test

- `tests/unit/impostazioni.test.js`: un'icona per ogni categoria; ogni categoria e
  ogni voce dicono a cosa servono, in una riga.
- Nel browser (Playwright), in italiano: le categorie del manager, la categoria
  Agenda con le sue voci, una voce con la strada indietro, il link dei listini; sul
  telefono le categorie, la categoria, la voce e il ritorno.
