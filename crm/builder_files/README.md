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

`client_scripts/` è il posto dove finirà `tracker.js` (modulo 15): montato su ogni pagina
pubblicata, le visite e i submit del sito entrano nella pipeline di attribuzione che il CRM
ha già, senza che nessuno debba incollare un tag.

## Cosa spediamo

| Componente | Come prende i dati |
|---|---|
| **Servizi CRM** | data script su `CRM Service` con `publish_on_website` |
| **Prodotti CRM** | data script su `CRM Product` |
| **Form CRM** | `{{ crm_form_html(props.modulo, …) }}` — il form del CRM reso inline |
| **Prenota** | `{{ crm_booking_html(props.calendario, …) }}` |
| **Contatti** | `{{ crm_contact_html() }}` |

I JSON **non si scrivono a mano**: li genera `scripts/builder/build_components.py`.
Modifica quello e rilancialo — un albero di blocchi sbagliato non fallisce in fase di
salvataggio, fallisce in silenzio sulla pagina di un cliente.

```bash
python3 scripts/builder/build_components.py
```

## Due modi di portare dati in un blocco

**Data script** — Python server-side sul componente, per le liste. Vedi sotto.

**Metodo Jinja** — per i frammenti che il CRM sa già rendere (un form, una CTA di
prenotazione). Builder passa ogni pagina per `render_template`, quindi un blocco il cui
`innerHTML` è `{{ crm_form_html(props.modulo) }}` riceve il markup vero. I metodi sono
registrati in `crm/hooks.py` (`jinja.methods`) e implementati in `crm/api/site_render.py`;
il nome è prefissato perché lo spazio dei nomi Jinja è condiviso con tutte le app.
Un test verifica che ogni chiamata presente nei blocchi sia davvero registrata.

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

## ⚠️ Il rendering non fa autoescape — escapa tu

`FrappeSandboxedEnvironment` non passa `autoescape`, e il default di Jinja è `False`;
Builder, dal canto suo, non emette `|safe`. Quindi **ogni valore che finisce in un binding
esce come HTML**.

Ha due conseguenze, e vanno tenute insieme:

1. **Il testo va escapato nel data script.** Un `<` nel nome di un servizio finirebbe in
   pagina come markup. Si usa `frappe.utils.escape_html()` su tutto ciò che è testo — è
   l'unico punto in cui possiamo farlo, perché il template non lo farà.
2. **L'HTML voluto passa così com'è.** È ciò che rende possibile il componente *Form CRM*:
   il data script può rendere il markup del form e consegnarlo come dato, senza bisogno di
   un blocco HTML custom. Per il rich text che arriva dagli utenti (`CRM Product.description`
   è un Text Editor) si passa da `frappe.utils.sanitize_html()`.

## Cosa è disponibile dentro `safe_exec`

Il data script gira con `safe_exec` se `server_script_enabled` è attivo, altrimenti con il
`safer_exec` di Builder: in entrambi i casi è RestrictedPython, quindi niente import e
niente dunder. `frappe.utils` espone la lista `VALID_UTILS` del framework — fra le altre
`cint`, `cstr`, `flt`, `escape_html`, `sanitize_html`, `strip_html`, `fmt_money`,
`format_datetime`, `get_url`, `parse_json`.

`get_component_data` è registrata da Builder come metodo Jinja (`hooks.jinja.methods`), e
i metodi da hook vengono aggiunti ai globals **dopo** la scelta fra globals ristretti e
non: quindi funziona anche con `disable_render_safe_exec` non impostato.

## Regole di casa

- **Il data script lo scriviamo noi**, il cliente compila solo le props.
- Legge **solo campi pubblicabili**: mai costi, staff, note interne.
- **Escapa ogni testo** con `escape_html`; `sanitize_html` per il rich text.
- Deve essere veloce: gira a ogni render della pagina.
- Niente import, niente dunder, solo `VALID_UTILS`.
- `crm/tests/test_builder_files.py` valida struttura e compilabilità di ogni file qui dentro.
