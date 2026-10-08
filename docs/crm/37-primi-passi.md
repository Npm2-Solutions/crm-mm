# 37 — Primi passi: le cose da fare per cominciare, che si spuntano da sole

> ✅ **FATTO (01/10/2026)**. In fondo alla barra c'era il "Getting started" di
> frappe-ui: in inglese anche con l'app in italiano, nel blu di un altro prodotto,
> con i passi di un CRM di vendita (crea un lead, convertilo in trattativa, cambia
> lo stato della trattativa, aggiungi un commento) e un pannello che si apriva da
> solo a ogni accesso. Un centro che si iscrive a DottorCloud deve sapere altro:
> che servizi offre, quando è aperto, chi ci lavora, come si prenota. Ora i **Primi
> passi** sono quelli, in italiano, e ognuno si spunta da solo quando i dati del
> centro dicono che è fatto.

## Com'è

```
┌ Primi passi ──────────────┐        Primi passi                              ✕
│ 5 di 9 fatti              │        Le cose da fare per cominciare con DottorCloud:
│ ▓▓▓▓▓▓▓▓░░░░░░            │        ogni passo si spunta da solo quando è fatto.
│ [ Continua › ]            │        ▓▓▓▓▓▓▓▓▓▓░░░░░░░░  5 di 9 fatti
└───────────────────────────┘        ✓ Il nome e il logo del centro            ›
  (in fondo alla barra)              ○ I servizi che offri                     ›
                                     ○ Orari e turni                           ›
                                     ✓ I tuoi colleghi                         ›
                                     ✓ Moduli e consensi                       ›
                                     ○ Prenotazione online                     ›
                                     ○ L'email del centro                      ›
                                     ✓ Il tuo primo paziente                   ›
                                     ✓ Il tuo primo appuntamento               ›
                                     Nascondi i primi passi
```

- **I passi del centro**, nell'ordine in cui si fanno: il nome e il logo, i servizi,
  orari e turni, i colleghi, moduli e consensi, la prenotazione online, l'email,
  chi emette le fatture (con l'extra della fatturazione), il primo paziente, il
  primo appuntamento. Ognuno con una riga su a cosa serve.
- **Si spuntano da soli**: un passo è fatto quando i dati lo dicono (c'è un servizio
  attivo, ci sono gli orari, è partito un invito o lavora qualcun altro, c'è un
  modulo pubblicato…), comunque lo si sia fatto. Un centro che lavora già non ha
  niente da fare, e non vede niente.
- **Ognuno vede i suoi**: un passo si offre a chi ha la capacità di farlo (doc 30).
  Il manager vede l'impostazione del centro; la segreteria il primo paziente e il
  primo appuntamento; con un modulo spento i suoi passi non ci sono.
- **Un passo porta dove si fa**: la pagina delle impostazioni (con la categoria
  accesa) o la pagina dell'app; il primo paziente apre la scheda nuova.
- **In fondo alla barra** un riquadro con quanti ne mancano e "Continua"; con la
  barra chiusa un'icona; sul telefono in fondo al cassetto. Il pannello si apre
  solo quando lo si chiede: accanto alla pagina, sul telefono a tutto schermo.
- **Si possono nascondere**, e si ritrovano in Impostazioni › Il centro ›
  Funzionalità, finché ne manca qualcuno.
- **Le parole del verticale**: con la clinica "Il tuo primo paziente".
- **Via l'onboarding di frappe-ui**: il riquadro, il pannello, i passi di vendita e
  le chiamate sparse che li segnavano (dodici componenti), e l'API che dava a
  chiunque il nome del primo lead (`crm/api/onboarding.py`).

## Prima dei primi passi: il benvenuto (05/10/2026)

La prima volta che chi imposta il centro apre DottorCloud (capacità
`impostazioni.generali`) trova due schermate, prima di ogni altra pagina:

```
  [icona]  ▬ ▭                           [icona]  ▬ ▬
  Ti diamo il benvenuto in DottorCloud   Il tuo centro
  In che lingua lavora il centro? …      Il suo nome apre la pagina di prenotazione…
  ┌ Italiano                     ✚ ┐     Nome del centro ✚  [es. Studio Medico Aurora]
  │ Il centro lavora in italiano   │     Fuso orario del centro  [Europe/Rome · …]
  └────────────────────────────────┘     ┌ Prima dai un'occhiata con i dati di prova ○ ┐
  ┌ English                      › ┐     [ Inizia a usare DottorCloud ]
  │ The centre works in English    │     ‹ Lingua
  └────────────────────────────────┘
               Lo faccio dopo                       Lo faccio dopo
```

- **La lingua del centro**, italiano o inglese, ognuna detta nelle sue parole: chi
  legge l'altra trova la sua. Scelta un'altra, la pagina torna in quella lingua,
  sulla seconda schermata; chi l'ha scelta la legge da subito (la sua lingua torna
  «come il centro»).
- **Il nome del centro e il suo fuso orario** (uno d'Europa, Roma già scelto), e,
  per chi può caricarli e se non ci sono, i dati di prova: una scelta, spenta.
- **Una volta**: si offre finché il centro non ha un nome e nessuno l'ha finito
  (`crm_benvenuto_fatto`); un centro che lavora già ha il suo nome e non lo vede.
  Gli altri utenti intanto usano DottorCloud. «Lo faccio dopo» lo lascia per quella
  scheda del browser.
- **Al posto della procedura guidata del framework**, che a fine benvenuto è segnata
  fatta: nel Desk non si apre più, e finirla dopo avrebbe caricato da sola i dati di
  prova. Al suo posto c'erano le domande del framework sul modo di lavorare
  (`PersonaForm`), che servivano solo alla sua telemetria, spenta: tolte.

## Come è fatto

| File | Cosa fa |
|---|---|
| `crm/benvenuto.py`, `frontend/src/pages/Benvenuto.vue` | Il benvenuto: `da_fare()`, `per_il_boot()` (il boot e il router), `get_welcome`, `choose_language`, `finish`; la pagina con le due schermate |
| `crm/primi_passi.py` | Il registro (`Passo`, `registra_passo`, `passi()`), `da_offrire()` puro, `get_first_steps()`; i passi della base |
| `crm/moduli/__init__.py` | Il passo dei moduli e consensi, registrato con i moduli |
| `crm/registrazione.py` | I passi della base prima dei moduli |
| `frontend/src/utils/primiPassi.js` | `riassunto()` e `daMostrare()` — puro, testato |
| `frontend/src/composables/primiPassi.js` | La lista condivisa, il pannello, nascondere (su questo browser), fare un passo; si rilegge all'apertura e alla chiusura delle impostazioni |
| `frontend/src/components/FirstSteps/` | `FirstStepsCard.vue` nella barra, `FirstStepsPanel.vue` montato una volta in `GlobalModals.vue` |

Un modulo che ha passi suoi li registra dal suo `registra()`, con la capacità che
li fa, la pagina dove si fanno e come capire dai dati che sono fatti; le parole in
inglese, quelle del verticale sopra, la traduzione.

## Test

- `crm/tests/test_primi_passi.py`: a chi si offre un passo (capacità e modulo); il
  manager ha i nove passi del centro, la segreteria i suoi due; con la clinica il
  primo è un paziente; un servizio scritto a mano spunta servizi e prenotazione;
  ogni passo porta da qualche parte.
- `crm/tests/test_impostazioni.py`: le pagine dei passi esistono nel menu delle
  impostazioni.
- `tests/unit/primiPassi.test.js`: quanti fatti, il prossimo, quando si mostrano.
- Nel browser: il riquadro e il pannello in chiaro e in scuro, un passo che apre
  l'agenda e uno le impostazioni, nascondere e ritrovarli nelle Funzionalità; il
  cassetto e il pannello sul telefono; la segreteria con tutto fatto non vede
  niente.
