# Pipeline di vendita

> Piu' funnel nello stesso CRM: ogni trattativa vive dentro una pipeline e si
> muove tra gli stage di quella pipeline.

---

## Cos'e' una pipeline

Prima esisteva un solo elenco di stati per le trattative (`CRM Deal Status`):
tutti i deal, di qualunque tipo, condividevano lo stesso funnel.

Ora c'e' il DocType **`CRM Pipeline`** e ogni stato appartiene a una pipeline:

```
CRM Pipeline "Sales"            CRM Pipeline "Onboarding"
├── Qualification               ├── Kickoff
├── Demo/Making                 ├── Setup
├── Proposal/Quotation          └── Live
├── Negotiation
├── Ready to Close
├── Won
└── Lost
```

Il deal ha due campi: `status` (lo stage) e `pipeline`. **Lo stage e' la fonte di
verita'**: `pipeline` rispecchia sempre la pipeline del suo stage, quindi i due
non possono divergere. Cambiare `pipeline` su un deal esistente lo sposta sul
primo stage aperto della nuova pipeline.

---

## Come si configura

**Impostazioni → Vendite → Pipeline** (solo Sales Manager / System Manager).

| Azione | Dove |
|---|---|
| Creare una pipeline | pulsante **New**: nasce con gli stage standard |
| Rinominare / descrivere | campi in cima all'editor, poi **Save** |
| Aggiungere uno stage | **Add stage** in fondo alla lista |
| Riordinare gli stage | trascinare la maniglia a sinistra della riga |
| Colore, tipo, probabilita' | controlli sulla riga dello stage |
| Cancellare uno stage | icona cestino: se contiene deal, chiede dove spostarli |
| Pipeline di default | menu `⋯` nella lista → **Set as default** |
| Disattivare una pipeline | menu `⋯` → **Disable** (resta consultabile, non accoglie deal nuovi) |
| Cancellare una pipeline | menu `⋯` → **Delete**: chiede dove spostare i deal |

La pipeline di default e' quella in cui finiscono i deal creati senza indicarne
una (form pubblici, API, conversione da lead). Non si puo' cancellare ne'
disattivare: prima si nomina default un'altra pipeline.

### I nomi degli stage sono unici su tutto il sito

Il deal punta allo stage **per nome** (`status` e' un Link a `CRM Deal Status`),
quindi due pipeline non possono avere entrambe uno stage chiamato
"Qualification". Conseguenze pratiche:

- creando una pipeline nuova, gli stage standard prendono un suffisso se il nome
  e' gia' occupato: `Qualification (Onboarding)`;
- rinominandoli subito dopo (es. "Primo contatto") il suffisso sparisce;
- se si prova a usare un nome gia' preso l'errore lo dice, con la pipeline che
  lo sta usando.

E' il prezzo della compatibilita': dashboard, automazioni, filtri salvati, viste
e script continuano a riferirsi agli stati per nome, come prima.

---

## Cosa cambia nell'uso quotidiano

- **Board kanban dei deal** (`Deals → Kanban`): il selettore in alto a destra
  sceglie la pipeline; le colonne diventano i suoi stage, nell'ordine impostato.
  "All pipelines" mostra tutti gli stage. La scelta vive nelle colonne della
  vista, quindi resta anche al rientro e non sovrascrive board personalizzate.
- **Pagina del deal**: accanto allo stato c'e' il selettore di pipeline (compare
  con due o piu' pipeline). Il menu degli stati offre solo gli stage della
  pipeline del deal.
- **Creazione deal**: il modale mostra pipeline e stage; cambiando pipeline gli
  stage si aggiornano.
- **Lista deal**: `pipeline` e' un campo come gli altri — filtri, quick filter,
  raggruppamenti, colonne, ordinamento.

---

## API

Tutto sotto `crm.api.pipeline` (le scritture richiedono Sales Manager):

| Metodo | Cosa fa |
|---|---|
| `get_pipelines(with_counts=0)` | pipeline con i loro stage; con `with_counts` anche quanti deal ci sono dentro |
| `get_pipeline(name)` | una pipeline con i suoi stage |
| `create_pipeline(pipeline_name, description, stages)` | crea; senza `stages` usa quelli standard |
| `update_pipeline(name, pipeline_name, description, disabled)` | rinomina / aggiorna |
| `set_default_pipeline(name)` | sposta il flag di default |
| `save_stages(pipeline, stages)` | crea, rinomina, ricolora e riordina gli stage in un colpo solo |
| `delete_stage(stage, move_deals_to)` | cancella uno stage spostando prima i suoi deal |
| `delete_pipeline(name, move_deals_to)` | cancella una pipeline spostando prima i suoi deal |

Helper Python: `crm.fcrm.doctype.crm_pipeline.crm_pipeline` espone
`get_default_pipeline()`, `get_pipeline_stages()`, `get_first_stage()`,
`get_pipeline_of_stage()`.

Frontend: store `pipelinesStore` (`@/stores/pipelines`) con `getStages`,
`getStageNames`, `getPipelineOfStage`, `pipelineOptions`, `defaultPipeline`;
funzioni pure in `@/utils/pipelines` (testate in `tests/unit/pipelines.test.js`).

---

## Migrazione dei siti esistenti

La patch `crm.patches.v1_0.create_default_pipeline`:

1. crea la pipeline **Sales** (se non esiste gia' una pipeline);
2. ci mette dentro tutti gli stage che non ne hanno una;
3. assegna a ogni deal la pipeline del proprio stato;
4. aggiunge `pipeline` ai quick filter e al Quick Entry del deal.

Nulla da fare a mano: dopo `bench migrate` il CRM si comporta esattamente come
prima, con una sola pipeline, finche' non se ne crea una seconda.

---

## Note di implementazione

- Le colonne del kanban sono ordinate per `position` degli stage (prima era
  `modified asc`, cioe' un ordine casuale) e, se la vista filtra per pipeline,
  contengono solo gli stage di quella pipeline
  (`crm.utils.get_kanban_column_options`).
- Spostare uno stage in un'altra pipeline (`CRM Deal Status.on_update`) si porta
  dietro i suoi deal con un update massivo.
- Anche `delete_stage` / `delete_pipeline` spostano i deal via SQL: essendo
  operazioni di configurazione su molte righe non passano dai hook del deal, per
  cui non generano voci nello status change log.
