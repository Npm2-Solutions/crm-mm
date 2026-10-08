# 38 — I piani dei pazienti: una scheda loro, spiegati

> ✅ **FATTO (01/10/2026)**. Scrivere il piano di un paziente era difficile da
> capire: i piani stavano in fondo alla scheda "Area pazienti" della persona,
> sotto i messaggi, e chi cercava "Piani" non li trovava; il menu "Nuovo piano"
> elencava tipi in inglese senza dire cosa fossero ("Meal plan", "Exchange diet",
> "Programme of stages"); l'editor era quasi tutto in inglese; e niente diceva che
> un piano pubblicato lo legge solo chi entra nell'area. Ora i piani hanno una
> scheda loro, spiegata, in italiano.

## Com'è

```
Attività · Dati · Eventi · … · Preventivi · Piani · Area pazienti · Clinica

Piani
Quello che la persona segue fra un appuntamento e l'altro: un allenamento, delle
abitudini, una dieta, gli esercizi a casa. Lo scrivi qui e lo pubblichi; la persona
lo trova nella sua area e spunta quello che fa.                       [+ Nuovo piano]

ⓘ Il paziente non entra ancora nella sua area: invitalo dalla scheda Area pazienti,
  così vede i piani che pubblichi.

 ① Scegli cosa scrivere…   ② Scrivi i momenti…   ③ Pubblicalo…

Cosa vuoi scrivere?
┌ Menu ───────────────────┐ ┌ Dieta a scambi ─────────┐
│ I pasti della giornata… │ │ Gruppi di alimenti…     │
└─────────────────────────┘ └─────────────────────────┘
┌ Allenamento ────────────┐ ┌ Abitudini ──────────────┐
┌ Programma a tappe ┄┄┄┄┄┄┐
```

- **Una scheda "Piani"** sulla pagina della persona, sul computer e sul telefono;
  l'Area pazienti tiene chi entra e i messaggi.
- **Cos'è un piano**, in una frase in testa alla scheda.
- **Quando non ce n'è ancora nessuno**: come si fa in tre passi, e i tipi che chi
  guarda può scrivere, ognuno con la sua frase ("Menu — I pasti della giornata con
  alimenti e grammi: calorie e nutrienti contati, la lista della spesa pronta"),
  più il programma a tappe. Chi i piani li legge e basta (la segreteria) lo legge
  in una riga.
- **Se il piano non arriva**: senza nessuno che entri nell'area, o con l'area
  spenta, la scheda lo dice e dice come rimediare.
- **In italiano** l'editor del piano, il programma, la scelta dall'archivio di
  esercizi e alimenti e le schede dell'area: 123 frasi. "Desk" (l'amministrazione)
  e "Stage" (la fase di una trattativa) restano le loro: la tappa di un programma e
  la segreteria che scrive nell'area hanno parole proprie.

## Come è fatto

| File | Cosa fa |
|---|---|
| `crm/piani/regole.py`, `crm/clinica/piani_regole.py` | `TipoPiano.descrizione`: una riga per tipo, registrata con il tipo |
| `crm/piani/api.py` | `get_plans()` dà di ogni tipo la sua descrizione, e `area` (accesa, e se qualcuno ci entra) |
| `frontend/src/pages/Lead.vue`, `MobileLead.vue`, `components/Activities/` | La scheda Piani |
| `frontend/src/components/Plans/PlansCard.vue` | La spiegazione, i passi, i tipi da scegliere, l'avviso sull'area |
| `crm/clinica/parole.py` | Con la clinica "il paziente", "la scheda Area pazienti" |

## Test

- `crm/piani/tests/test_piani.py`: ogni tipo dice cos'è; la pagina sa se la persona
  vedrà il piano, prima e dopo l'invito.
- Nel browser: la scheda di chi ha piani, quella vuota di un professionista con i
  tipi da scegliere e l'avviso, quella della segreteria; il telefono; l'editor in
  italiano.
