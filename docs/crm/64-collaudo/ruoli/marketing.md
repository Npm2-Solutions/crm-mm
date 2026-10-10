# Collaudo · Marketing

## A cosa serve

Questa è la giornata di chi fa il marketing del Poliambulatorio San Luca: le
automazioni accese dai modelli pronti, una campagna a un elenco di persone, le
richieste di recensione e il questionario di soddisfazione, il modulo del sito, i
link tracciati. E quello che il marketing **non** deve vedere: chi è paziente, la
cartella, le conversazioni, email e telefoni in chiaro. Ogni riga dice cosa fare e
cosa deve succedere. Quando una riga non va come è scritto, una segnalazione con il
suo codice (per esempio MKT-06): [segnalazioni.md](../segnalazioni.md).

## Prima di cominciare

- **Chi sei:** l'utente del ruolo `marketing`, livello Marketing.
- **Dove:** `https://collaudo.dottorcloud.com/crm`, sul computer; *(telefono)* sul
  tuo telefono per i moduli e i link.
- **Le persone:** le automazioni accese scrivono davvero. Sul collaudo ci sono solo
  le persone della squadra: va bene. Mai accendere un'automazione su un sito con
  persone vere senza averla riletta con il responsabile.

## La mattina

- [ ] **MKT-01 · Entra.** Dal computer; cambia la password (Impostazioni › Il tuo
  account › Profilo › «Cambia la password»).
  *Atteso:* nel menu il gruppo del marketing (Automazioni, Social Planner; il Sito
  web solo dove Builder è installato) e Persone; non ci sono Conversazioni, Fatture,
  Accoglienza.
  Note: ______________________________________________

- [ ] **MKT-02 · Quello che non vedi.** Persone: apri un paziente del medico.
  *Atteso:* email e telefono mascherati; niente scheda Clinica, niente chat; nessun
  segno dice che è un paziente.
  Note: ______________________________________________

## Le automazioni

- [ ] **MKT-03 · Il questionario dopo la visita.** Automazioni › «Nuova automazione» ›
  «Parti da un modello pronto» › «Questionario di soddisfazione dopo la visita».
  Leggi i passi, poi «Attiva».
  *Atteso:* nasce spenta e si accende solo con «Attiva»; dopo una visita segnata
  «Presente», il paziente riceve il link del questionario
  ([paziente.md](./paziente.md), PAZ-26).
  Note: ______________________________________________

- [ ] **MKT-04 · Il consenso.** Nelle «Iscrizioni» dell'automazione, guarda chi non
  aveva detto sì alle richieste dopo la visita né al marketing.
  *Atteso:* è «Saltata», una volta, con il motivo; non conta come passata
  dall'automazione.
  Note: ______________________________________________

- [ ] **MKT-05 · La recensione.** Impostazioni › Marketing › Richieste di recensione:
  il link di Google (sul collaudo è un indirizzo di example.com, che non si apre: è
  giusto così). Poi il modello pronto «Chiedi una recensione dopo la visita», «Attiva».
  *Atteso:* si può escludere un servizio, mai una persona (Google non lascia
  scegliere chi chiedere); il messaggio ha il suo link, la prima apertura si conta;
  nella dashboard «Richieste di recensione inviate».
  Note: ______________________________________________

- [ ] **MKT-06 · La chiamata persa.** Il modello pronto «Ti abbiamo cercato… chiamata
  persa», «Attiva». Un paziente già conosciuto chiama il centro e nessuno risponde.
  *Atteso:* dopo un minuto il paziente riceve un SMS con il link della prenotazione.
  Note: ______________________________________________

- [ ] **MKT-07 · Gli orari delle promozioni.** Un'automazione di marketing con un SMS,
  fatta partire dopo le 22 (o la domenica).
  *Atteso:* l'SMS aspetta il primo momento buono, dal lunedì al sabato dalle 8 alle
  22; un promemoria del centro, che non è marketing, parte quando deve.
  Note: ______________________________________________

## Una campagna a un elenco

- [ ] **MKT-08 · L'automazione da mano.** Una «Nuova automazione» che parte «Avviata a
  mano», con un'email, che chiede il consenso al marketing. «Attiva».
  *Atteso:* niente la fa partire da sola.
  Note: ______________________________________________

- [ ] **MKT-09 · L'elenco.** Persone, un filtro (per esempio chi è arrivato questa
  settimana), «Invia a un elenco», l'automazione di MKT-08.
  *Atteso:* la finestra conta l'elenco come lo vedi tu e dice chi resta fuori e
  perché (già dentro, senza consenso al marketing, ha scritto STOP dove arriverebbe
  solo l'SMS, nessun modo di scrivergli).
  Note: ______________________________________________

- [ ] **MKT-10 · Il resoconto.** Manda, poi apri le «Iscrizioni» dell'automazione.
  *Atteso:* il resoconto della campagna: l'elenco, gli iscritti, chi è rimasto fuori
  per quale motivo; quando ha finito, te lo dice.
  Note: ______________________________________________

- [ ] **MKT-11 · Sul telefono *(telefono)*.** La lista Persone dal telefono.
  *Atteso:* niente «Invia a un elenco»: le campagne si fanno dalla scrivania.
  Note: ______________________________________________

## Il sito e i link

- [ ] **MKT-12 · Il modulo del sito.** Impostazioni › Pazienti › Moduli: un modulo per
  il sito web («Richiesta informazioni»), con il suo indirizzo. Aprilo dal telefono
  (`/crm-form/<indirizzo>`) e compilalo come una persona nuova (un indirizzo della
  squadra con il «+»).
  *Atteso:* la persona è trovata o creata, con le risposte come suo modulo, i
  consensi registrati, la trattativa aperta; le automazioni sentono «Modulo inviato».
  Note: ______________________________________________

- [ ] **MKT-13 · Il codice per un altro sito.** Nello stesso modulo, la scheda per
  condividerlo: il codice da incollare in un'altra pagina.
  *Atteso:* il codice si copia; l'indirizzo del modulo nasce dal titolo e si legge.
  Note: ______________________________________________

- [ ] **MKT-14 · Un link tracciato.** Impostazioni › Marketing › Tracciamento › Link
  tracciati: un link a `/prenota`. Aprilo due volte dal telefono.
  *Atteso:* i clic contati; il link porta a `/prenota`.
  Note: ______________________________________________

## La sera

- [ ] **MKT-15 · La soddisfazione.** Dopo che due pazienti hanno risposto al
  questionario (MKT-03).
  *Atteso:* nella dashboard «Soddisfazione (NPS)» con il punteggio delle risposte.
  Note: ______________________________________________

- [ ] **MKT-16 · La dashboard del marketing.** I numeri dei nuovi pazienti e da dove
  arrivano.
  *Atteso:* le parole sono quelle della clinica («Nuovi pazienti»); senza una spesa
  pubblicitaria collegata non c'è un costo per nuovo paziente da calcolare, e la
  dashboard non ne inventa uno.
  Note: ______________________________________________
