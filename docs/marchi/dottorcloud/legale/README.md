# I documenti per i centri — bozze

**Stato:** ✍️ bozze del 07/10/2026, **da far rivedere a un legale prima di usarle**.
Sono scritte da quello che il codice fa davvero: dove un fatto non è verificato,
la bozza lo dice tra parentesi quadre `[da verificare: …]`.

| Documento | A cosa serve | Chi lo firma |
|---|---|---|
| [Nomina a responsabile del trattamento](./nomina-responsabile.md) | art. 28 GDPR: NPM2 tratta i dati del centro per conto suo | il centro e NPM2, una per centro |
| [Valutazione d'impatto (DPIA)](./dpia-cartella.md) | art. 35 GDPR: i dati sanitari su larga scala la chiedono | il centro (titolare), con l'aiuto di NPM2 |
| [I tuoi dati](./i-tuoi-dati.md) | la pagina per i centri: dove stanno i dati, chi li legge, come si esce | — è il testo della pagina |
| [Condizioni di servizio](./condizioni.md) | abbonamento, pagamento, rinnovo, disdetta, uscita | il centro le accetta all'attivazione |

## Le domande per il legale

1. **Dispositivo medico.** DottorCloud tiene la cartella, i referti, le diete e gli
   esercizi, e un assistente che scrive bozze da note e dettature. Non suggerisce
   dosaggi né segnala interazioni (le linee guida MDCG 2019-11 rev. 2025 lo
   farebbero dispositivo). Basta questo perché non lo sia? L'assistente che mette
   la dettatura nei campi (farmaci, allergie, dosi, spuntati uno per uno) cambia
   la risposta?
2. **Spazio europeo dei dati sanitari** (regolamento UE 2025/327): un sistema di
   cartella elettronica dovrà autocertificarsi e avere la marcatura CE, con date
   tra il 2027 e il 2031. Quando tocca a DottorCloud, e cosa serve?
3. **Frappe Cloud.** Il fornitore dell'hosting è Frappe Technologies, una società
   indiana, sui server Hetzner in Germania. Il suo personale può accedere ai
   server per l'assistenza: è un trasferimento fuori dall'UE? Servono le clausole
   contrattuali tipo e una valutazione del trasferimento?
4. **I fornitori del centro.** Twilio, Meta (WhatsApp) e Fatture in Cloud li
   contratta il centro con il suo account: sono suoi responsabili, non sotto-
   responsabili di NPM2? E l'account Twilio dell'agenzia, con la segreteria?
5. **L'assistente.** Il modello gira presso un fornitore (Anthropic o compatibile
   OpenAI) scelto dall'agenzia, con «nessuna conservazione» richiesta
   (`no_retention`) e senza dati che identificano il paziente, solo con il suo
   consenso. È sufficiente? Serve una DPIA a parte?
6. **Il registro degli accessi** alla cartella e ai documenti sanitari: la durata
   di conservazione da scrivere.
7. **Le condizioni:** limitazione di responsabilità, foro, legge applicabile,
   recesso per i professionisti (non consumatori).
