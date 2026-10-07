# Valutazione d'impatto (DPIA) della cartella clinica — bozza

> ✍️ Bozza del 07/10/2026 da far rivedere a un legale. La DPIA è del centro, che
> è il titolare: NPM2 la prepara per tutti i centri, e ogni centro la completa
> con la sua parte (sezione 6) e la firma.

## 1. Il trattamento

- **Cosa:** la cartella clinica e i documenti sanitari dei pazienti di un centro
  medico privato, in DottorCloud: visite, anamnesi, referti, immagini, piani di
  cura, diete ed esercizi, odontogramma, sintesi del paziente, moduli firmati con
  dati sanitari.
- **Perché:** la cura del paziente (art. 9 par. 2 lett. h), e gli obblighi
  amministrativi e fiscali che ne seguono (fatture, Sistema TS).
- **Chi:** i professionisti sanitari del centro, la segreteria per quello che le
  serve, il direttore sanitario; NPM2 come responsabile.
- **Perché serve una DPIA:** dati sanitari, pazienti vulnerabili (anche minori),
  uso di un fornitore cloud, un assistente con un modello linguistico (Linee guida
  WP248 e l'elenco del Garante del 2018: due criteri o più).

## 2. Necessità e proporzionalità

- Si raccoglie quello che serve alla cura: i campi della scheda clinica li sceglie
  il centro, i moduli li disegna il centro.
- **Il marketing non usa i dati sanitari:** le campagne e le automazioni non
  scelgono le persone su dati clinici né sulle righe delle fatture sanitarie, e
  il livello Marketing vede email e telefoni mascherati.
- **Il consenso dove serve:** il dossier sanitario (che i professionisti del
  centro leggano quello che hanno scritto gli altri), i referti online,
  l'assistente; si registra, si revoca, la risposta non si modifica.
- **Conservazione:** la cartella per [10 anni o più, da decidere con il legale];
  il registro degli accessi per [da decidere].
- **Diritti:** accesso e portabilità con l'esportazione completa (Impostazioni >
  Il centro > I tuoi dati); l'area paziente mostra al paziente i suoi documenti.

## 3. I rischi

| Rischio | Per chi | Probabilità prima delle misure | Gravità |
|---|---|---|---|
| Un collega legge una cartella che non lo riguarda | paziente | media | alta |
| Un addetto dell'agenzia legge dati sanitari | paziente | media | alta |
| Un account rubato (password) | paziente, centro | media | alta |
| Un file sanitario raggiunto con un link condiviso | paziente | bassa | alta |
| Un referto inviato alla persona sbagliata | paziente | media | alta |
| La perdita dei dati (guasto, cancellazione) | paziente, centro | bassa | alta |
| L'assistente manda dati identificativi al fornitore del modello | paziente | bassa | media |
| Un documento firmato modificato dopo la firma | paziente, centro | bassa | alta |
| Il fornitore dell'hosting accede da fuori UE | paziente | bassa | media |

## 4. Le misure (come DottorCloud le applica)

| Rischio | Misura |
|---|---|
| Un collega legge troppo | livelli e capacità; il dossier con il consenso; «solo io» e la disciplina sui documenti; l'oscuramento di un episodio; l'apertura fuori dall'équipe solo con un motivo scritto; ogni lettura nel registro degli accessi |
| L'agenzia legge | le capacità cliniche non vanno all'agenzia per il fatto di essere l'agenzia; un accesso a tempo solo se il centro lo apre, nel registro |
| Account rubato | [da fare: l'autenticazione a due fattori per i livelli clinici, il framework la offre]; sessioni che scadono |
| Link condiviso | i file privati si aprono dopo il controllo dei permessi, con un link firmato di cinque minuti |
| Referto alla persona sbagliata | online solo con il consenso ai referti online, con un link e un codice dato a parte, 45 giorni |
| Perdita | backup di Frappe Cloud; versioni dei file nell'archivio per 30 giorni [da verificare: frequenza e prova di ripristino] |
| Assistente | solo con il consenso del paziente; nessun dato che lo identifica nella richiesta; fornitore con nessuna conservazione richiesta; niente si salva da solo; ogni richiesta nel registro |
| Documento modificato | PDF/A con sigillo e marca temporale, impronta SHA-256, registro delle modifiche concatenato |
| Fuori UE | server in Germania; [da verificare: le clausole tipo con Frappe Technologies] |

## 5. Il rischio che resta

Con le misure del punto 4, e con quelle segnate come da fare, il rischio che resta
è [basso / da valutare con il legale]. Se resta alto, il centro consulta il
Garante prima di iniziare (art. 36).

## 6. La parte del centro

- Chi è il direttore sanitario, chi sono i professionisti e con quali livelli.
- Se usa il dossier, i referti online, l'assistente.
- Chi ha parlato con il responsabile della protezione dei dati, se il centro ne ha
  uno, e cosa ha detto.
- Data, firma del titolare.
