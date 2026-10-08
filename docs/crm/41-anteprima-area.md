# 41 · L'anteprima dell'area pazienti

**Stato:** fatto (01/10/2026).

## Il bisogno

Prima di consegnare il gestionale a un centro, e prima di aprire l'area a un
paziente, si vuole vedere l'area come la vedrà lui. Fin qui l'unico modo era
invitare un paziente di prova ed entrare con il codice arrivato per email.

## Cosa fa

- Sulla scheda della persona, nella scheda «Area pazienti» («Area clienti» senza la
  clinica), il pulsante **Anteprima** apre l'area di quella persona in una scheda
  del browser, come la vede lei. Funziona anche prima dell'invito.
- In alto una striscia dice che è un'anteprima e di chi è l'area. «Chiudi
  l'anteprima» torna alla scheda della persona.
- Alla persona non arriva niente: nessun codice, nessuna email, nessun invito. La
  sessione è quella del centro, e l'anteprima dura mezz'ora.

## Chi la apre

Chi apre le aree (`area.invita`: la segreteria e il manager su tutto il centro,
l'operatore sulle persone che segue) e legge la persona. Un cliente dell'area non
la apre, e un collega non eredita l'anteprima di un altro.

## Cosa si vede

Le stesse pagine e le stesse chiamate dell'area, ma solo quello che chi guarda
legge in DottorCloud:

- un piano, un documento, un preventivo, una fattura, un messaggio o un
  appuntamento che non legge resta al suo posto, vuoto: «Qui Laura vede qualcosa
  che in DottorCloud tu non leggi»;
- un dato sanitario che legge finisce nel registro degli accessi, come quando lo
  apre dalla scheda;
- un manager senza la bacheca (`area.messaggi`) non legge i messaggi; senza la
  clinica, un piano con dati sanitari lo legge solo chi l'ha scritto.

## Cosa non fa

Da qui non si cambia e non si manda niente. Le chiamate dell'area che scrivono
rispondono che è un'anteprima: spuntare un esercizio, finire una tappa, la lista
d'attesa, i moduli, la chat, i messaggi segnati come letti, gli scaricamenti, le
passkey, gli avvisi. Le pagine non mostrano quei pulsanti, e i link per spostare o
annullare un appuntamento non ci sono.

## Come è fatta

- `crm/area/anteprima.py`:
  - `start(lead)` lega l'anteprima alla sessione (nella cache, per l'id della
    sessione, mezz'ora); `stop()` la chiude;
  - `in_anteprima()` dice chi la guarda e di chi è l'area;
  - `vede(doctype, nome)` chiede i permessi di DottorCloud per chi guarda e, per i
    dati sanitari, scrive il registro degli accessi; `filtra` e `coperta` lasciano
    al suo posto ciò che non si legge.
- `crm/area/api.py`: `_mia(person, anche_in_anteprima=False)` e `_utente(...)` sono
  chiuse all'anteprima per default. Le chiamate che leggono lo dicono; una chiamata
  nuova che scrive, manda o scarica non dice niente, e l'anteprima la rifiuta.
- La pagina `/area` riceve l'anteprima nel boot (`crm/www/area.py`); l'app mostra la
  striscia, nasconde le azioni (`frontend/src/area/anteprima.js`) e disegna
  `HiddenCard` per ciò che non si legge.

## Verifiche

- `crm/area/tests/test_anteprima.py`: 12 test.
  - La segreteria vede l'area prima dell'invito.
  - Chi non apre aree, un cliente dell'area e un collega non entrano.
  - Ogni scrittura è rifiutata e i link per spostare gli appuntamenti non ci sono.
  - Il piano con dati sanitari è vuoto per la segreteria; il suo autore lo legge e
    resta nel registro.
  - L'area di Anna, per lei, non cambia.
- Nel browser, dalla scheda di una paziente di prova:
  - «Anteprima» apre l'area con la striscia;
  - per il manager piani clinici, documenti e messaggi restano vuoti;
  - nessun pulsante scrive;
  - «Chiudi l'anteprima» torna alla scheda, e `/area` torna a dire che l'area è per i
    pazienti.
