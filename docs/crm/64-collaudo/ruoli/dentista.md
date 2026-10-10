# Collaudo · Dentista

## A cosa serve

Questa è la giornata del dentista del Poliambulatorio San Luca: la prima visita
sulla sua scheda, l'odontogramma, il piano di cura come preventivo sui denti, il
pagamento a rate, la firma del paziente dalla sua area, le cure prenotate che
prendono la loro riga. Ogni riga dice cosa fare e cosa deve succedere. Quando una riga
non va come è scritto, una segnalazione con il suo codice (per esempio DEN-07):
[segnalazioni.md](../segnalazioni.md).

## Prima di cominciare

- **Chi sei:** l'utente del ruolo `dentista`: livello Professionista, qualifica di
  odontoiatra. Lavori a Milano il lunedì, il mercoledì e il venerdì, nello «Studio 4».
- **Dove:** `https://collaudo.dottorcloud.com/crm`, sul computer; l'odontogramma
  anche su un tablet; *(telefono)* sul tuo telefono.
- **I pazienti:** i colleghi che fanno i pazienti. Denti, cure e prezzi inventati.
- **Le fatture delle rate sono di prova**, come tutte quelle del collaudo.

## La mattina

- [ ] **DEN-01 · Entra.** Dal computer; cambia la password (Impostazioni › Il tuo
  account › Profilo › «Cambia la password»).
  *Atteso:* l'agenda si apre sulla tua colonna; le impostazioni del centro non ci
  sono.
  Note: ______________________________________________

- [ ] **DEN-02 · Il telefono *(telefono)*.** L'app sulla schermata Home e le notifiche
  accese (Impostazioni › Il tuo account › Notifiche).
  *Atteso:* la notifica di prova arriva.
  Note: ______________________________________________

## La prima visita

- [ ] **DEN-03 · La visita.** Al paziente della «Prima visita odontoiatrica»: scheda
  Clinica › «Nuova visita» su «Prima visita odontoiatrica».
  *Atteso:* la scheda si compila come le altre; la bozza è solo tua finché non firmi.
  Note: ______________________________________________

- [ ] **DEN-04 · L'odontogramma.** «Inizia l'odontogramma»: la dentatura, una carie
  sul 36 (superfici occlusale e mesiale), un'otturazione vecchia sul 26, il 46 da
  devitalizzare. «Salva l'odontogramma».
  *Atteso:* i denti con la numerazione FDI; scegliendo un dente si legge cosa c'è; il
  salvataggio dice «Odontogramma salvato».
  Note: ______________________________________________

- [ ] **DEN-05 · La firma.** «Firma» sulla visita.
  *Atteso:* il referto in PDF tra i Documenti; l'odontogramma resta e si corregge,
  non si cancella.
  Note: ______________________________________________

## Il piano di cura

- [ ] **DEN-06 · Il preventivo.** Scheda Preventivi › «Nuovo preventivo»: una riga
  «Otturazione» sul 36 (OM), una «Devitalizzazione» sul 46, una «Igiene orale
  professionale».
  *Atteso:* le righe si leggono «Dente 36 · OM»; i totali si fanno da soli; il
  preventivo è una tua bozza.
  Note: ______________________________________________

- [ ] **DEN-07 · A rate.** Sotto i totali, «Pagamento»: «A rate», acconto del 20%,
  10 rate, «Ogni mese», «Prima rata il» primo del mese prossimo.
  *Atteso:* una frase dice il piano («Acconto di … all'accettazione · 10 rate da … ·
  dal … al …»); le rate sono uguali al centesimo e i centesimi che avanzano vanno
  sull'ultima.
  Note: ______________________________________________

- [ ] **DEN-08 · Proporlo.** «Proponi».
  *Atteso:* il PDF del preventivo con il «Piano dei pagamenti» e «Pagamento rateale
  direttamente al centro, senza interessi né spese»; la trattativa della pipeline
  «Preventivi» si sposta.
  Note: ______________________________________________

- [ ] **DEN-09 · Chi lo legge.** Prima di proporre un secondo preventivo, chiedi alla
  segreteria di aprirlo; poi proponilo e chiediglielo di nuovo.
  *Atteso:* la bozza del dentista è un dato sanitario e la legge solo chi l'ha scritta;
  proposto, la segreteria lo legge; il marketing mai.
  Note: ______________________________________________

- [ ] **DEN-10 · La firma del paziente.** La segreteria lo manda da firmare
  ([segreteria.md](./segreteria.md), SEG-22) e il paziente lo firma dall'area con
  «Accetta e firma» ([paziente.md](./paziente.md)).
  *Atteso:* ti arriva la notifica, senza il titolo del preventivo; il preventivo è
  accettato; la sua copia firmata è tra i documenti; la trattativa è vinta con il
  valore del preventivo.
  Note: ______________________________________________

- [ ] **DEN-11 · Le rate seguono.** Il mattino dopo l'accettazione, riapri il
  preventivo.
  *Atteso:* l'acconto ha la sua fattura (di prova), emessa da sola; la riga dice
  «Fatturata» con il numero, che apre la fattura; una riga dice come vanno le rate
  («Rate: … di 10 pagate · prossima …»), anche nella scheda Preventivi e nel
  Riepilogo della persona.
  Note: ______________________________________________

- [ ] **DEN-12 · Pagata.** La segreteria segna incassata la fattura dell'acconto.
  *Atteso:* la riga dell'acconto diventa «Pagata».
  Note: ______________________________________________

- [ ] **DEN-13 · Le cure prenotate.** Prenota l'«Otturazione» per il paziente; quando
  viene, segna «Presente».
  *Atteso:* l'appuntamento prende la sua riga del preventivo al prezzo concordato, e
  la riga è fatta; l'appuntamento non è tra quelli da fatturare (lo pagano le rate).
  Note: ______________________________________________

- [ ] **DEN-14 · Saldare prima.** Sul preventivo accettato, «Salda il resto».
  *Atteso:* una fattura sola, in bozza, di tutte le righe ancora da fatturare.
  Scartala dopo averla guardata.
  Note: ______________________________________________

- [ ] **DEN-15 · Una nuova versione.** Sul preventivo accettato, «Nuova versione»:
  cambia una riga, proponila; il paziente accetta la nuova.
  *Atteso:* la versione vecchia è chiusa e le sue rate non ancora fatturate sono
  annullate (quelle fatturate restano, con le loro fatture); la nuova porta tutte le
  righe e il suo piano.
  Note: ______________________________________________

- [ ] **DEN-16 · Rifiutato.** Un terzo preventivo: il paziente risponde «Non accetto»
  con un motivo.
  *Atteso:* la notifica; il preventivo è rifiutato con il motivo, le rate annullate;
  la trattativa persa con il motivo.
  Note: ______________________________________________

## La sera

- [ ] **DEN-17 · Gli esiti.** I tuoi appuntamenti ancora senza esito: «Presente» o
  «Assente».
  *Atteso:* puoi segnare i tuoi, non quelli dei colleghi.
  Note: ______________________________________________

- [ ] **DEN-18 · Sul tablet e sul telefono *(telefono)*.** L'odontogramma sul tablet,
  poi il preventivo sul telefono.
  *Atteso:* i denti si toccano con il dito senza sbagliare dente; sul telefono ogni
  riga del preventivo è una carta, non una tabella tagliata.
  Note: ______________________________________________
