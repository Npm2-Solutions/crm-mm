# Qualita' dei lead: far imparare le inserzioni dalle vendite

**Stato:** ✅ fatto (18/09/2026) — poi serve la configurazione lato cliente

## Cosa cambia davvero

Tutto il resto dell'integrazione Meta **legge**. Questo **scrive**, ed e' l'unica
parte che rende le inserzioni *migliori* invece che piu' comprensibili.

Meta, da sola, sa solo che qualcuno ha compilato il modulo. Quindi ottimizza per
**chi compila i moduli**: ed e' bravissima a trovare le persone che compilano
qualunque cosa e non rispondono piu' al telefono. Rimandandole gli stadi del
funnel — lead grezzo, qualificato, appuntamento, venduto — Meta puo' ottimizzare
per **chi compra**. Si chiama *Conversion Leads*, ed e' quello che i CRM grossi
vendono come funzionalita'.

Noi siamo in una posizione insolitamente comoda: Meta chiede che ogni evento
porti il proprio **lead id** (il numero a 15-17 cifre della compilazione) e noi
lo salviamo su ogni lead (`facebook_lead_id`). Nessun hash di email, nessun click
id, nessun accoppiamento da indovinare.

## Come funziona

**Una coda, non una chiamata.** Chi cambia uno stato nel CRM non deve aspettare
Facebook; un evento rifiutato alle 23 va ritentato, non perso; e la copertura su
cui Meta giudica l'integrazione si puo' leggere solo da un registro di cosa e'
stato mandato davvero. Quindi ogni stadio diventa una riga `Meta Conversion
Event`, e ogni ora la coda si svuota in una chiamata sola.

**Gli stadi sono i vostri.** L'`event_name` e' il nome dello stato del lead o
della trattativa, come si chiama nel CRM. Non c'e' una mappatura da inventare:
il funnel si configura in Events Manager, che e' esattamente il passaggio che
Meta assegna all'inserzionista.

**Il lead grezzo si manda sempre.** Non solo le buone notizie: senza il primo
evento Meta non puo' mettere in proporzione quelli dopo. E' l'errore piu' comune
di queste integrazioni.

**Lo stesso stadio non si ripete.** Uno stato spostato avanti e indietro a mano
non e' due qualificazioni.

**Una trattativa rapporta sul suo lead.** Il lead id e' l'unica cosa che Meta
sa accoppiare, quindi una trattativa inserita a mano, senza lead dietro, non ha
niente da rapportare — e rapportarla sul lead sbagliato sarebbe peggio.

**Il payload e' quello giusto.** `action_source: "system_generated"` e
`user_data.lead_id`: il sapore web della stessa API usa valori diversi, e quello
sbagliato viene ignorato in silenzio. Il batch viaggia nel **corpo** della
richiesta, perche' duecento eventi non stanno in una URL.

**Si ritenta, ma non per sempre.** Cinque tentativi, poi la riga passa a Failed:
un payload che Meta non accettera' mai bloccherebbe per sempre la coda dietro di
se'.

## I requisiti, detti chiari

Questa e' una funzione che paga dopo settimane, non domani. Meta chiede:

| Requisito | Numero |
|---|---|
| Copertura dei lead rapportati | **almeno 60%** |
| Stadi diversi mandati | almeno 2, meglio 3 (lead grezzo incluso) |
| Volume | ~200 lead al mese |
| Frequenza di invio | almeno una volta al giorno (noi: ogni ora) |
| Tasso di conversione dello stadio ottimizzato | tra 1% e 40% |
| Finestra | lo stadio deve avvenire entro 28 giorni dal lead |
| Apprendimento | 3-4 settimane prima del pieno effetto |

La copertura sta in cima a Settings → Integrations → Meta → **Lead quality**, con il numero e non con
un semaforo: sotto il 60% Meta non si fida abbastanza dei dati per ottimizzarci
sopra, e vale la pena saperlo prima di vendere il risultato a un cliente.

## Cosa deve fare il cliente (una volta)

1. In **Events Manager** creare un dataset per gli eventi CRM (non il pixel del
   sito, non il modulo).
2. Incollare l'id del dataset in Settings → Integrations → Meta → Lead quality e accendere
   l'interruttore.
3. Verificare in Events Manager che gli eventi arrivino (c'e' il campo per il
   *test event code*, da svuotare subito dopo: gli eventi di test non contano).
4. Configurare il funnel in Events Manager, cioe' dire a Meta quale dei nostri
   stadi e' quello da ottimizzare.
5. Creare la campagna con l'obiettivo **Conversion Leads**.
