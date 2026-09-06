# builder_files — quello che il CRM spedisce a Frappe Builder

Se sul site è installata l'app [builder](https://github.com/frappe/builder), il suo
`after_app_install` / `after_migrate` sincronizza tutto ciò che trova qui dentro:

```
builder_files/
├── components/<nome>/<nome>.json   → Builder Component
├── pages/<nome>/<nome>.json        → Builder Page (starter)
├── client_scripts/<nome>/…         → Builder Client Script
├── variables/<nome>/…              → Builder Token (colori, font del brand)
└── fonts/                          → font caricati
```

Ogni file è un fixture Frappe standard (`doctype`, `name`, campi). Il nome della
cartella, del file e il campo `name` devono coincidere: `make_records` cerca
`<cartella>/<cartella>.json`.

Se Builder **non** è installato, questa cartella è inerte: nessun hook, nessun costo.

## Il contratto dei componenti

Un `Builder Component` è due cose:

1. **`block`** — l'albero dei blocchi, come stringa JSON.
2. **`component_data_script`** — Python eseguito server-side a ogni render, in
   `safe_exec`. Riceve `props` (i valori dell'istanza) e riempie `component`.

```python
component["servizi"] = [...]      # → disponibile come component.servizi
```

### Come si legano i dati ai blocchi

| Cosa | Dove | Effetto |
|---|---|---|
| Prop del componente | `props` sul blocco radice | il cliente la compila nell'editor |
| Valore da una prop | `dynamicValues: [{key, type:"key", property:"innerHTML", comesFrom:"props"}]` | `{{ props.<key> }}` |
| Valore dal data script | `…comesFrom: "componentData"` | `{{ component.<key> }}` |
| Lista | `isRepeaterBlock: true` + `dataKey: {key, property:"dataKey", type:"key", comesFrom:"componentData"}` | `{% for component in component.<key> %}` |

⚠️ **Dentro un repeater `componentData` la variabile di ciclo si chiama `component`** e
oscura quella esterna (`get_loop_info` in `builder_page.py`). Quindi i figli della card
legano i campi della riga sempre con `comesFrom: "componentData"`, e il blocco radice del
repeater deve avere **esattamente un figlio**.

Il valore statico del blocco resta come fallback: `{{ chiave if chiave else 'statico' }}`.

## Regole di casa

- **Il data script lo scriviamo noi**, il cliente compila solo le props.
- Legge **solo campi pubblicabili**: mai costi, staff, note interne.
- Deve essere veloce: gira a ogni render della pagina.
- Va tenuto compatibile con `safe_exec` (niente import, niente dunder).
- `crm/tests/test_builder_files.py` valida struttura e compilabilità di ogni file qui dentro.
