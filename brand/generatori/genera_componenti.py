# Copyright (c) 2026, NPM2 Solutions Srl and contributors
"""Le anteprime e i README dei componenti (Espresso + DottorCloud).
Scrive ../design-system/espresso/componenti/<Componente>/{anteprima.html,README.md}.
Le anteprime usano tokens.css e componenti.css (vedi design-system/espresso).
Uso: python3 genera_componenti.py"""

import os
import re

from percorsi import ESPRESSO, ICONE

OUT = str(ESPRESSO / "componenti")
LOGO_LIGHT = "../../../../logo/dottorcloud-orizzontale.svg"
LOGO_DARK = "../../../../logo/dottorcloud-orizzontale-negativo.svg"


def ic(name, cls="dc-icon"):
	s = open(ICONE / f"{name}.svg").read()
	inner = re.search(r">\s*(.*)</svg>", re.sub(r"<!--.*?-->", "", s, flags=re.S), re.S).group(1)
	inner = re.sub(r"\s+", " ", inner).replace("> <", "><").strip()
	return f'<svg class="{cls}" viewBox="0 0 24 24" aria-hidden="true">{inner}</svg>'


def page(group, height, body, extra_css=""):
	return (
		"<!doctype html>\n"
		f'<!-- @dsCard group="{group}" height={height} -->\n'
		'<html data-theme="light">\n'
		'<script>if(location.hash==="#dark")document.documentElement.dataset.theme="dark"</script>'
		'<head><meta charset="utf-8"><link rel="stylesheet" href="../../tokens.css"><link rel="stylesheet" href="../componenti.css"><style>'
		"html,body{margin:0;background:var(--surface-base);}"
		".stage{padding:20px;display:flex;flex-wrap:wrap;gap:12px;align-items:center;}"
		".col{display:flex;flex-direction:column;gap:12px;}"
		".row{display:flex;flex-wrap:wrap;gap:8px;align-items:center;}.grid3{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:16px;align-items:start}.grid2{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:16px;align-items:start}"
		'[data-theme="dark"] .only-light{display:none}:root:not([data-theme="dark"]) .only-dark{display:none}'
		+ extra_css
		+ "</style></head><body>\n"
		+ body
		+ "\n</body></html>\n"
	)


C = {}


def X(s=10, extra=""):
	return f'<i class="dc-cross" style="--s:{s}px{extra}" aria-hidden="true"></i>'


def R(summary, frappe, custom, rules=None):
	s = (
		summary
		+ "\n\n## In frappe-ui\n"
		+ frappe.strip()
		+ "\n\n## Personalizzazione DottorCloud\n"
		+ custom.strip()
		+ "\n"
	)
	if rules:
		s += "\n## Regole\n" + rules.strip() + "\n"
	return s


C["Button"] = (
	"Azioni",
	150,
	f"""<div class="dc stage col" style="align-items:flex-start">
 <div class="row">
  <button class="dc-btn dc-btn--solid dc-btn--md">{ic('plus')}Nuovo appuntamento</button>
  <button class="dc-btn dc-btn--brand dc-btn--md">{ic('send-horizontal')}Invia promemoria</button>
  <button class="dc-btn dc-btn--subtle dc-btn--md">Esporta</button>
  <button class="dc-btn dc-btn--outline dc-btn--md">{ic('paperclip')}Allega</button>
  <button class="dc-btn dc-btn--ghost dc-btn--md">Annulla</button>
  <button class="dc-btn dc-btn--danger dc-btn--md">Elimina</button>
 </div>
 <div class="row">
  <button class="dc-btn dc-btn--solid dc-btn--lg">Prenota la visita</button>
  <button class="dc-btn dc-btn--solid">Salva</button>
  <button class="dc-btn dc-btn--subtle">{ic('search')}Cerca</button>
  <button class="dc-btn dc-btn--danger-subtle">Annulla la visita</button>
  <button class="dc-btn dc-btn--subtle dc-btn--icon" aria-label="Altre azioni">{ic('more-horizontal')}</button>
  <button class="dc-btn dc-btn--ghost dc-btn--icon" aria-label="Chiudi">{ic('x')}</button>
  <button class="dc-btn dc-btn--solid dc-btn--xs">Conferma</button>
  <button class="dc-btn dc-btn--solid" disabled>Non disponibile</button>
 </div>
</div>""",
	R(
		"Il pulsante di frappe-ui, alle sue misure, con il pieno del marchio e la coda della nuvola.",
		"""`<Button variant="solid|subtle|outline|ghost" theme="gray|red" size="sm|md|lg">`. Misure: xs 24px, **sm 28px (predefinito)**, md 32px, lg 40px; raggio `rounded-4` (8px), lg `rounded-5`.""",
		"""- **solid gray** diventa il pieno del marchio: `brand-solid` (teal-700, menta nel tema scuro), testo `on-brand-solid`, hover `brand-solid-hover`. È già così in `marchio.css` (`--brand-action`).
- **La nuvola-D**: il solid (e il solid rosso) ha l'angolo in basso a sinistra a `radius-tail` (2px). È l'unica differenza di forma: per riconoscere l'azione principale a colpo d'occhio.
- **subtle del marchio** (`dc-btn--brand`): `brand-subtle` / `on-brand-subtle`, per l'azione secondaria che riguarda il paziente (Invia promemoria). In frappe-ui: `variant="subtle"` con la classe `dc-brand`.
- Grigi tinti di verde (subtle, outline, ghost) e anello di focus `focus` vengono dalle variabili, senza toccare il componente.""",
		"""- Un solo solid per vista, in alto a destra (PageHeader) o in fondo alla finestra.
- Nel gestionale: `sm` nelle barre e nelle righe, `md` per l'azione della pagina. `lg` solo su telefono e nell'area paziente.
- Etichette con verbo e oggetto; solo icona: `aria-label` o Tooltip.""",
	),
)

C["Dropdown"] = (
	"Azioni",
	270,
	f"""<div class="dc stage" style="align-items:flex-start;gap:24px">
 <div class="col" style="gap:6px"><button class="dc-btn dc-btn--subtle dc-btn--icon" aria-label="Azioni">{ic('more-horizontal')}</button>
 <div class="dc-menu">
  <div class="dc-menu__item">{ic('pencil')}Modifica</div>
  <div class="dc-menu__item is-active">{ic('copy')}Duplica<span class="dc-menu__hint">⌘D</span></div>
  <div class="dc-menu__item">{ic('send-horizontal')}Invia promemoria</div>
  <div class="dc-menu__sep"></div>
  <div class="dc-menu__item dc-menu__item--danger">{ic('trash-2')}Annulla la visita</div>
 </div></div>
 <div class="dc-menu" style="margin-top:34px">
  <div class="dc-menu__group">Stato</div>
  <div class="dc-menu__item is-selected"><span class="dc-badge__dot" style="color:var(--success)"></span>Confermato{X(8)}</div>
  <div class="dc-menu__item"><span class="dc-badge__dot" style="color:var(--warning)"></span>Da confermare</div>
  <div class="dc-menu__item"><span class="dc-badge__dot" style="color:var(--info)"></span>In sala d'attesa</div>
  <div class="dc-menu__item"><span class="dc-badge__dot" style="color:var(--danger)"></span>Annullato</div>
 </div>
</div>""",
	R(
		"Il menu a tendina per le azioni di una riga o di una pagina, e la lista aperta di Select e Autocomplete.",
		"""`<Dropdown :options="[{ label, icon, onClick, theme }]">` con gruppi (`group`); la stessa superficie per `Select` e `Autocomplete`. Voci alte 28px, `rounded-3`, menu `rounded-lg` su `surface-elevation-1` con `shadow-lg`.""",
		"""- La voce scelta è segnata dalla **croce** in `brand` a destra, al posto della spunta.
- Il menu ha la coda della nuvola (angolo in basso a sinistra 2px).
- Voci distruttive in `danger` (`theme: 'red'`), sempre ultime e dopo un separatore.""",
		"""Al massimo 7 voci per gruppo; scorciatoie a destra in `ink-gray-5`.""",
	),
)

C["TextInput"] = (
	"Moduli",
	200,
	f"""<div class="dc stage grid3">
 <label class="dc-field"><span class="dc-label">Cognome{X(7,';--c:var(--danger)')}</span><span class="dc-input"><input value="Rossi"></span></label>
 <label class="dc-field"><span class="dc-label">Cerca paziente</span><span class="dc-input is-focus">{ic('search')}<input placeholder="Nome, codice fiscale o telefono"></span></label>
 <label class="dc-field"><span class="dc-label">Codice fiscale{X(7,';--c:var(--danger)')}</span><span class="dc-input dc-input--error"><input value="RSSMRA80A01H50"></span><span class="dc-error">{ic('circle-alert')}Mancano due caratteri.</span></label>
 <label class="dc-field"><span class="dc-label">Telefono</span><span class="dc-input dc-input--outline">{ic('phone')}<input value="+39 333 123 4567"></span><span class="dc-help">Per i promemoria WhatsApp.</span></label>
 <label class="dc-field"><span class="dc-label">Email</span><span class="dc-input dc-input--md"><input placeholder="nome@esempio.it"></span></label>
 <label class="dc-field"><span class="dc-label">Numero cartella</span><span class="dc-input"><input value="CC-2026-0412" disabled></span></label>
</div>""",
	R(
		"Il campo di testo di frappe-ui, compatto, con l'etichetta piccola sopra.",
		"""`<TextInput variant="subtle|outline" size="sm|md|lg" label="…" :required>` (anche dentro `FormControl`). Predefinito **subtle**: fondo `surface-gray-2`, alto 28px, `rounded`; al focus fondo `surface-base`, bordo `outline-gray-4`, `shadow-sm`. Etichetta `text-xs` in `ink-gray-5`.""",
		"""- **Obbligatorio**: una piccola **croce** rossa dopo l'etichetta, al posto dell'asterisco.
- Al focus l'icona iniziale prende `brand-solid`; l'anello di focus è `focus`.
- **Errore**: fondo `danger-subtle`, bordo `danger` e sotto una frase in `danger` con l'icona `circle-alert` (in frappe-ui: `ErrorMessage`).
- Grigi tinti dalle variabili.""",
		"""- `subtle` nei moduli del gestionale; `outline` quando il campo sta su `surface-gray-*` o in un filtro.
- L'errore dice come rimediare ("Mancano due caratteri.").""",
	),
)

C["Textarea"] = (
	"Moduli",
	150,
	"""<div class="dc stage grid2">
 <label class="dc-field"><span class="dc-label">Nota interna</span><span class="dc-input dc-textarea"><textarea>Paziente preferisce gli appuntamenti al mattino. Allergia alla penicillina segnalata dal medico di base.</textarea></span><span class="dc-help">Visibile solo al personale.</span></label>
 <label class="dc-field"><span class="dc-label">Motivo della visita</span><span class="dc-input dc-textarea is-focus"><textarea placeholder="Descrivi in breve"></textarea></span></label>
</div>""",
	R(
		"Il campo su più righe, per note e motivi.",
		"""`<Textarea variant="subtle|outline" size="sm|md" :rows>`: stesso fondo e stessi stati del TextInput, `py-1.5 px-2`, testo `text-base` con interlinea 1.5.""",
		"""Come il TextInput: grigi tinti, focus `focus`, croce per l'obbligatorio. Le note interne si distinguono con il tag `amber` accanto all'etichetta quando sono mostrate in lettura.""",
	),
)

C["Select"] = (
	"Moduli",
	120,
	f"""<div class="dc stage grid3">
 <label class="dc-field"><span class="dc-label">Medico</span><span class="dc-input dc-select"><span class="dc-avatar dc-avatar--xs dc-avatar--staff">GB</span><span>Dott.ssa Bianchi</span>{ic('chevron-down').replace('dc-icon','dc-icon dc-chev')}</span></label>
 <label class="dc-field"><span class="dc-label">Prestazione</span><span class="dc-input dc-select">{ic('stethoscope')}<span>Visita cardiologica</span>{ic('chevron-down').replace('dc-icon','dc-icon dc-chev')}</span></label>
 <label class="dc-field"><span class="dc-label">Sede</span><span class="dc-input dc-select"><span class="dc-ph">Scegli una sede</span>{ic('chevron-down').replace('dc-icon','dc-icon dc-chev')}</span></label>
</div>""",
	R(
		"La scelta da un elenco breve.",
		"""`<Select :options size variant placeholder>`: il trigger ha l'aspetto del TextInput con `chevron-down` in `ink-gray-4`; la lista aperta è la superficie del Dropdown.""",
		"""Avatar a nuvola per le persone (medico, paziente) prima del valore; voce scelta segnata con la croce del marchio nella lista aperta.""",
		"""Per elenchi lunghi o da cercare usa Autocomplete.""",
	),
)

C["Autocomplete"] = (
	"Moduli",
	270,
	f"""<div class="dc stage" style="align-items:flex-start;display:block;max-width:340px">
 <label class="dc-field"><span class="dc-label">Paziente</span><span class="dc-input is-focus">{ic('search')}<input value="ros"></span></label>
 <div class="dc-menu" style="margin-top:4px">
  <div class="dc-menu__item is-active"><span class="dc-avatar dc-avatar--sm">MR</span><span>Mario <b>Ros</b>si</span><span class="dc-menu__hint">RSSMRA80A01</span></div>
  <div class="dc-menu__item"><span class="dc-avatar dc-avatar--sm dc-avatar--blue">AR</span><span>Anna <b>Ros</b>ati</span><span class="dc-menu__hint">RSTNNA72C41</span></div>
  <div class="dc-menu__item"><span class="dc-avatar dc-avatar--sm dc-avatar--violet">RR</span><span><b>Ros</b>a Rinaldi</span><span class="dc-menu__hint">RNLRSO65E50</span></div>
  <div class="dc-menu__sep"></div>
  <div class="dc-menu__item" style="color:var(--on-brand-subtle)">{X(9)}Nuovo paziente "ros"</div>
 </div>
</div>""",
	R(
		"Il campo che cerca mentre scrivi: pazienti, prestazioni del listino, medici.",
		"""`<Autocomplete :options placeholder>` / `<Combobox>`: campo come TextInput, lista come Dropdown, voci 28px.""",
		"""- Le persone hanno l'avatar a nuvola; il testo cercato è in grassetto; a destra un dato che distingue gli omonimi (codice fiscale) in `ink-gray-5`.
- L'ultima voce crea il nuovo record ed è segnata dalla **croce** in `on-brand-subtle`: è il "+" del marchio dove si crea qualcosa.""",
	),
)

C["Checkbox"] = (
	"Moduli",
	170,
	"""<div class="dc stage" style="align-items:flex-start;gap:36px">
 <div class="col" style="gap:10px">
  <label class="dc-check"><input type="checkbox" checked> Invia promemoria via WhatsApp</label>
  <label class="dc-check"><input type="checkbox"> Consenso al trattamento per marketing</label>
  <label class="dc-check"><input type="checkbox" class="ind"> Seleziona tutti (3 di 12)</label>
  <label class="dc-check"><input type="checkbox" disabled checked> Privacy firmata</label>
  <label class="dc-check"><input type="checkbox" disabled> Non disponibile</label>
 </div>
 <div class="col" style="gap:4px;width:300px">
  <label class="dc-check dc-check--md dc-check--row"><input type="checkbox" checked><span>Promemoria il giorno prima<span class="dc-check__desc">WhatsApp alle 18:00</span></span></label>
  <label class="dc-check dc-check--md dc-check--row"><input type="checkbox"><span>Promemoria un'ora prima<span class="dc-check__desc">SMS</span></span></label>
 </div>
</div>
<script>document.querySelectorAll('input.ind').forEach(function(i){i.indeterminate=true})</script>""",
	R(
		"La casella di spunta: spuntata, vuota, a metà, disabilitata.",
		"""`<Checkbox v-model label size="sm|md" :padding :disabled>`: 14px (sm) o 16px (md), `rounded-sm`, bordo `outline-gray-4`; spuntata prende il colore del testo (`ink-gray-9`). Con `padding` diventa una riga cliccabile.""",
		"""- Spuntata e a metà: fondo `brand-solid` con spunta `on-brand-solid` (in `marchio.css` già `color: var(--brand-action)` sulle checkbox spuntate).
- Forma a nuvola: angolo in basso a sinistra a 2px.
- Riga con `padding`: quando è spuntata il fondo diventa `brand-subtle`.""",
		"""I consensi non sono mai pre-spuntati. Per un'impostazione con effetto immediato usa Switch.""",
	),
)

C["Radio"] = (
	"Moduli",
	150,
	"""<div class="dc stage" style="align-items:flex-start;gap:36px">
 <div class="col" style="gap:10px">
  <label class="dc-check"><input type="radio" name="a" checked> Prima visita</label>
  <label class="dc-check"><input type="radio" name="a"> Controllo</label>
  <label class="dc-check"><input type="radio" name="a" disabled> Visita domiciliare</label>
 </div>
 <div class="col" style="gap:4px;width:300px">
  <label class="dc-check dc-check--md dc-check--row"><input type="radio" name="b" checked><span>In sede<span class="dc-check__desc">Via Roma 12, studio 2</span></span></label>
  <label class="dc-check dc-check--md dc-check--row"><input type="radio" name="b"><span>Videovisita<span class="dc-check__desc">Link inviato via email</span></span></label>
 </div>
</div>""",
	R(
		"La scelta singola fra poche opzioni visibili. Il segno del radio scelto è la croce del marchio.",
		"""frappe-ui non ha un componente Radio: si usa `<input type="radio" class="form-radio">` (stile di `@tailwindcss/forms`) dentro `FormControl`, o una riga come quella del Checkbox con `padding`.""",
		"""- Scelto: cerchio pieno `brand-solid` con dentro la **croce** `on-brand-solid` (al posto del punto bianco). In CSS: `background-image` dell'`input[type=radio]:checked` con la croce in SVG (vedi la sezione frappe-ui).
- Vuoto: bordo `outline-gray-4`, 14px (sm) o 16px (md).
- In riga: come il Checkbox con `padding`, fondo `brand-subtle` quando è scelto.""",
		"""2–5 opzioni; oltre, Select.""",
	),
)

C["Switch"] = (
	"Moduli",
	120,
	"""<div class="dc stage" style="gap:40px;align-items:flex-start">
 <div class="col" style="gap:12px">
  <label class="dc-switch-row"><button class="dc-switch" role="switch" aria-checked="true" data-state="checked"><span class="dc-switch__thumb"></span></button>Prenotazioni online</label>
  <label class="dc-switch-row"><button class="dc-switch" role="switch" aria-checked="false" data-state="unchecked"><span class="dc-switch__thumb"></span></button>Lista d'attesa automatica</label>
  <label class="dc-switch-row" style="color:var(--ink-gray-4)"><button class="dc-switch" role="switch" disabled><span class="dc-switch__thumb"></span></button>Videovisite (non attive)</label>
 </div>
 <div class="col" style="gap:12px">
  <label class="dc-switch-row"><button class="dc-switch dc-switch--md" role="switch" aria-checked="true" data-state="checked"><span class="dc-switch__thumb"></span></button>Taglia md, accesa</label>
  <label class="dc-switch-row"><button class="dc-switch dc-switch--md" role="switch" aria-checked="false" data-state="unchecked"><span class="dc-switch__thumb"></span></button>Taglia md, spenta</label>
 </div>
</div>""",
	R(
		"L'interruttore con effetto immediato. Acceso, il pomello mostra la croce del marchio, centrata.",
		"""`<Switch v-model label size="sm|md">` (reka-ui): sm 26×16 con pomello 12px, md 32×20 con pomello 14px; acceso `bg-surface-gray-10`.""",
		"""- Acceso: binario `brand-solid` (già in `marchio.css`), pomello `surface-base` con la **croce** `brand-solid` centrata (6px nel sm, 7px nel md); nel tema scuro pomello `teal-950` e croce menta.
- La croce è disegnata come sfondo del pomello (`background-position: center`), così resta al centro a ogni taglia; entra con un piccolo rimbalzo.
- Spento: binario `surface-gray-4`.""",
	),
)

C["Badge"] = (
	"Dati",
	110,
	f"""<div class="dc stage col" style="align-items:flex-start;gap:10px">
 <div class="row"><span class="dc-badge dc-badge--green">Confermato</span><span class="dc-badge dc-badge--amber">Da confermare</span><span class="dc-badge dc-badge--red">Annullato</span><span class="dc-badge dc-badge--blue">In sala d'attesa</span><span class="dc-badge dc-badge--gray">Bozza</span><span class="dc-badge dc-badge--brand">{X(7)}In visita</span></div>
 <div class="row"><span class="dc-badge dc-badge--sm dc-badge--green">Pagato</span><span class="dc-badge dc-badge--lg dc-badge--brand">{X(8)}In corso</span><span class="dc-badge dc-badge--solid">Nuovo</span><span class="dc-badge dc-badge--outline">12</span><span class="dc-badge dc-badge--green"><span class="dc-badge__dot"></span>Online</span></div>
</div>""",
	R(
		"Lo stato di una cosa, in una pillola.",
		"""`<Badge theme="gray|blue|green|amber|red|violet" variant="solid|subtle|outline|ghost" size="sm|md|lg" label>`: altezze 16/20/24, `rounded-full`, `text-xs`.""",
		"""- Stati: `green` confermato/pagato, `amber` da confermare, `red` annullato/errore, `blue` in attesa, `gray` bozza. I colori del testo sono `success`, `warning`, `danger`, `info` (più scuri dell'Espresso dove serviva per arrivare a 4.5:1).
- **In corso** (in visita, in chiamata): `brand-subtle` con la **croce** al posto del pallino. Uno solo per riga.""",
		"""Sempre la parola; il colore da solo non basta.""",
	),
)

C["Tag"] = (
	"Dati",
	90,
	f"""<div class="dc stage row">
 <span class="dc-tag dc-tag--blue">{ic('file-text')}Referto</span><span class="dc-tag dc-tag--violet">Esercizi</span><span class="dc-tag dc-tag--amber">Nota interna</span><span class="dc-tag dc-tag--rose">{ic('heart-pulse')}Cardiologia</span><span class="dc-tag dc-tag--rose">Allergia: penicillina</span><span class="dc-tag dc-tag--green">WhatsApp</span><span class="dc-tag dc-tag--brand">Prima visita</span>
</div>""",
	R(
		"L'etichetta della categoria: che tipo di cosa è. Componente DottorCloud.",
		"""Non c'è in frappe-ui: è un `<Badge>` con `class="dc-tag dc-tag--<categoria>"` (forma squadrata a nuvola invece della pillola, per distinguerla dagli stati).""",
		"""Colori fissi: `blue` documenti ed ecografie, `violet` esercizi e marketing, `amber` lista d'attesa e note interne, `rose` cardiologia e allergie, `green` WhatsApp e fatto, `brand` ciò che è del centro. Testo `cat-*-text` su `cat-*-subtle`; 20px, `text-xs` medium.""",
	),
)

C["Avatar"] = (
	"Dati",
	100,
	"""<div class="dc stage row" style="gap:14px">
 <span class="dc-avatar dc-avatar--2xl">MR</span><span class="dc-avatar dc-avatar--xl dc-avatar--staff">GB</span><span class="dc-avatar dc-avatar--lg">AN</span><span class="dc-avatar dc-avatar--blue">LV</span><span class="dc-avatar dc-avatar--sm dc-avatar--violet">SC</span><span class="dc-avatar dc-avatar--xs">RR</span>
 <span class="dc-avatars"><span class="dc-avatar">GB</span><span class="dc-avatar dc-avatar--staff">LV</span><span class="dc-avatar dc-avatar--blue">SC</span><span class="dc-avatar dc-avatar--gray">+3</span></span>
 <span class="dc-avatar dc-avatar--lg dc-avatar--round dc-avatar--gray">FR</span>
</div>""",
	R(
		"La persona dentro la nuvola: tre lati tondi e la punta in basso a sinistra, come il marchio.",
		"""`<Avatar :label :image size="xs…3xl" shape="circle|square">`: 16→46px, iniziali `uppercase`, fondo `surface-gray-2`.""",
		"""- Forma a nuvola (`border-radius: 50% 50% 50% 22%`) per pazienti e personale: in frappe-ui `class="dc-avatar"` sul componente.
- Pazienti `brand-subtle`, personale medico `brand-solid` (`dc-avatar--staff`), colleghi con un accento; tondo (`dc-avatar--round`) solo per chi è fuori dal centro (fornitori, sistemi).""",
		"""Gruppo: al massimo 3 più il contatore.""",
	),
)

C["ListView"] = (
	"Dati",
	260,
	f"""<div class="dc" style="padding:20px">
 <div class="dc-list">
  <div class="dc-list__head"><label class="dc-check"><input type="checkbox" class="ind"></label><span>Paziente</span><span>Prestazione</span><span>Stato</span><span style="text-align:right">Importo</span></div>
  <div class="dc-list__row"><label class="dc-check"><input type="checkbox"></label><span class="dc-person"><span class="dc-avatar dc-avatar--sm">MR</span><span class="dc-person__name">Mario Rossi</span></span><span><span class="dc-tag dc-tag--rose">Cardiologia</span></span><span><span class="dc-badge dc-badge--green">Pagato</span></span><span class="dc-num">€ 120,00</span></div>
  <div class="dc-list__row is-selected"><label class="dc-check"><input type="checkbox" checked></label><span class="dc-person"><span class="dc-avatar dc-avatar--sm dc-avatar--blue">GB</span><span class="dc-person__name">Giulia Bianchi</span></span><span><span class="dc-tag dc-tag--blue">Ecografia</span></span><span><span class="dc-badge dc-badge--amber">Da pagare</span></span><span class="dc-num">€ 85,00</span></div>
  <div class="dc-list__row"><label class="dc-check"><input type="checkbox"></label><span class="dc-person"><span class="dc-avatar dc-avatar--sm dc-avatar--violet">LV</span><span class="dc-person__name">Luca Verdi</span></span><span><span class="dc-tag dc-tag--violet">Fisioterapia</span></span><span><span class="dc-badge dc-badge--brand">{X(7)}In visita</span></span><span class="dc-num">€ 60,00</span></div>
  <div class="dc-list__bar"><span>1 selezionato</span><span class="row" style="gap:4px"><button class="dc-btn dc-btn--ghost">{ic('send-horizontal')}Invia promemoria</button><button class="dc-btn dc-btn--ghost">{ic('receipt-text')}Fattura</button><button class="dc-btn dc-btn--ghost dc-btn--icon" aria-label="Deseleziona">{ic('x')}</button></span></div>
 </div>
</div>
<script>document.querySelectorAll('input.ind').forEach(function(i){{i.indeterminate=true}})</script>""",
	R(
		"L'elenco di pazienti, appuntamenti, fatture.",
		"""`<ListView :columns :rows :options="{ selectable }">`: intestazione su `surface-gray-2` alta 32px, righe 40px separate da un filetto, hover `surface-gray-1`, selezione `surface-gray-2`; con righe selezionate compare `ListSelectBanner`.""",
		"""- Riga selezionata: `brand-subtle` invece del grigio.
- La barra delle righe selezionate è un **blocco** `block-deep` con la coda della nuvola: le azioni in blocco si vedono subito.
- Persone con l'avatar a nuvola; stato con Badge, tipo con Tag; importi a destra con cifre tabulari.""",
		"""Le azioni della singola riga in un Dropdown `more-horizontal`.""",
	),
)

C["Progress"] = (
	"Dati",
	170,
	f"""<div class="dc stage grid2" style="align-items:center">
 <div class="dc-progress"><div class="dc-progress__label"><span>Moduli firmati</span><span>3 di 4</span></div><div class="dc-progress__track"><div class="dc-progress__fill" style="width:75%"></div></div></div>
 <div class="dc-progress"><div class="dc-progress__label"><span>Ciclo di fisioterapia</span><span>3/10</span></div><div class="dc-steps"><span class="is-done"></span><span class="is-done"></span><span class="is-done"></span><span></span><span></span><span></span><span></span><span></span><span></span><span></span></div></div>
 <div class="dc-progress"><div class="dc-progress__label"><span>Invio a Sistema TS</span><span>62%</span></div><div class="dc-progress__track dc-progress__track--md"><div class="dc-progress__fill" style="width:62%"></div></div></div>
 <div class="row" style="gap:16px"><span class="dc-spinner"></span><span class="dc-spinner dc-spinner--md"></span><span class="dc-loader-mark">{X(12)}</span><span class="dc-muted" style="font-size:13px">Caricamento dell'agenda…</span></div>
</div>""",
	R(
		"Avanzamento e attesa.",
		"""`<Progress :value size="sm|md|lg" label>`: binario `surface-gray-2`, riempimento `surface-gray-10`, `rounded-xl`. `<Spinner>` / `<LoadingIndicator>` per l'attesa.""",
		"""- Riempimento in `brand` (il verde del logo).
- A tappe (cicli di sedute): segmenti separati, i fatti in `brand`.
- Spinner con l'arco `brand-solid`; per i caricamenti di pagina la **croce** che ruota (`dc-loader-mark`).""",
	),
)

C["Tabs"] = (
	"Navigazione",
	130,
	f"""<div class="dc stage col" style="align-items:stretch;gap:16px">
 <div class="dc-tabs" role="tablist"><button class="dc-tab" role="tab" aria-selected="true">{ic('calendar-days')}Attività <span class="dc-tab__count">12</span></button><button class="dc-tab" role="tab">{ic('heart-pulse')}Cartella clinica</button><button class="dc-tab" role="tab">{ic('file-text')}Documenti <span class="dc-tab__count">4</span></button><button class="dc-tab" role="tab">{ic('receipt-text')}Fatture</button></div>
 <div class="row"><div class="dc-segmented"><button aria-pressed="true">Giorno</button><button>Settimana</button><button>Mese</button></div><div class="dc-segmented"><button aria-pressed="true">{ic('calendar-days')}Agenda</button><button>{ic('users')}Lista</button></div></div>
</div>""",
	R(
		"Le schede di una pagina (Tabs) e il controllo segmentato (TabButtons).",
		"""`<Tabs :tabs v-model>`: schede a `gap-5`, testo `text-base` `ink-gray-5`, attiva `ink-gray-9` con un indicatore che scorre (`bg-surface-gray-10`). `<TabButtons :buttons>`: segmentato su `surface-gray-2`, attivo `surface-base` con `shadow-sm`.""",
		"""- **Scheda attiva**: testo `ink-gray-9` e una **linea di 2px in `brand-solid`** sotto, a tutta larghezza della scheda (l'indicatore di frappe-ui ricolorato, niente forme in più); l'icona della scheda attiva prende `brand-solid`, il contatore `brand-subtle`.
- **Segmentato**: il pulsante attivo ha la coda della nuvola.""",
	),
)

C["Breadcrumbs"] = (
	"Navigazione",
	150,
	f"""<div class="dc" style="padding:20px;display:flex;flex-direction:column;gap:14px">
 <div class="dc-header" style="border:1px solid var(--outline-gray-1);border-radius:10px"><div class="dc-crumbs"><a>Pazienti</a><span class="dc-sep">/</span><span class="is-current">Mario Rossi</span></div><div class="row"><button class="dc-btn dc-btn--subtle dc-btn--icon" aria-label="Altre azioni">{ic('more-horizontal')}</button><button class="dc-btn dc-btn--solid">{ic('plus')}Nuovo appuntamento</button></div></div>
 <div class="dc-header" style="border:1px solid var(--outline-gray-1);border-radius:10px"><span class="dc-page-title">Agenda</span><div class="row"><div class="dc-segmented"><button aria-pressed="true">Giorno</button><button>Settimana</button></div><button class="dc-btn dc-btn--solid">{ic('plus')}Nuovo</button></div></div>
</div>""",
	R(
		"L'intestazione della pagina: dove sei e l'azione principale.",
		"""`<Breadcrumbs :items>` (`text-lg-medium`, separatore `/` in `ink-gray-4`) dentro l'header della pagina (alto 48px, filetto sotto); a destra i pulsanti.""",
		"""- L'ultima voce è in `ink-gray-9`; le precedenti in `ink-gray-5`.
- Le pagine principali (Agenda, Pazienti) hanno il titolo `page-title` (20px, bold) al posto delle briciole: è l'unico testo pesante della pagina.
- A destra al massimo un solid (con la coda della nuvola).""",
	),
)

C["Sidebar"] = (
	"Navigazione",
	420,
	f"""<div class="dc" style="padding:16px;display:flex"><nav class="dc-sidebar" aria-label="Principale" style="border:1px solid var(--outline-gray-1);border-radius:12px">
 <div class="dc-sidebar__head"><img class="only-light" src="{LOGO_LIGHT}" alt="DottorCloud"><img class="only-dark" src="{LOGO_DARK}" alt="DottorCloud"></div>
 <a class="dc-nav" aria-current="page">{ic('calendar-days')}Agenda<span class="dc-nav__count">38</span></a>
 <a class="dc-nav">{ic('users')}Pazienti</a>
 <a class="dc-nav">{ic('message-circle')}Messaggi<span class="dc-nav__count">5</span></a>
 <a class="dc-nav">{ic('receipt-text')}Fatture</a>
 <a class="dc-nav">{ic('file-signature')}Moduli</a>
 <div class="dc-sidebar__label">Il centro</div>
 <a class="dc-nav">{ic('stethoscope')}Prestazioni</a>
 <a class="dc-nav">{ic('lock')}Permessi</a>
 <a class="dc-nav">{ic('settings-2')}Impostazioni</a>
</nav></div>""",
	R(
		"La barra laterale del gestionale.",
		"""`<Sidebar :header :sections>`: fondo `surface-sidebar`, voci alte 28px `text-sm` in `ink-gray-6`, voce attiva `surface-elevation-3` con `shadow-sm`; etichette di sezione `text-sm` `ink-gray-5`.""",
		"""- In testa il **logo orizzontale** (20px; negativo nel tema scuro) al posto del nome dell'app.
- Voce attiva: fondo `surface-elevation-2`, `shadow-sm`, icona `brand-solid` e la coda della nuvola.
- Etichette di sezione in `tiny` (maiuscolo).""",
		"""Le voci senza permesso spariscono.""",
	),
)

C["Alert"] = (
	"Feedback",
	260,
	f"""<div class="dc stage col" style="align-items:stretch;gap:8px">
 <div class="dc-alert dc-alert--blue">{ic('info')}<div><div class="dc-alert__title">Sistema TS</div><div class="dc-alert__body">L'invio delle spese di settembre parte stanotte alle 2:00.</div></div><span></span></div>
 <div class="dc-alert dc-alert--amber">{ic('triangle-alert')}<div><div class="dc-alert__title">Consenso mancante</div><div class="dc-alert__body">Il paziente non ha firmato il modulo privacy.</div></div><button class="dc-btn dc-btn--outline">Invia il modulo</button></div>
 <div class="dc-alert dc-alert--red">{ic('circle-alert')}<div><div class="dc-alert__title">Fattura scartata</div><div class="dc-alert__body">Lo SdI segnala la partita IVA del destinatario come non valida.</div></div><button class="dc-btn dc-btn--ghost dc-btn--icon dc-btn--xs" aria-label="Chiudi">{ic('x')}</button></div>
 <div class="dc-alert dc-alert--brand">{X(12)}<div><div class="dc-alert__title">Novità: prenotazioni dalla lista d'attesa</div><div class="dc-alert__body">Quando si libera uno slot, DottorCloud propone il primo paziente in coda.</div></div><span></span></div>
</div>""",
	R(
		"L'avviso dentro la pagina.",
		"""`<Alert theme="blue|green|amber|red" title description dismissable>`: `rounded-md`, `px-4 py-3.5`, icona 16px nel colore del tema, titolo `ink-gray-9`, testo `ink-gray-6`.""",
		"""- La coda della nuvola sull'angolo in basso a sinistra.
- In più un tema **del marchio** (`brand-subtle` con la croce) per le novità e i suggerimenti di DottorCloud.
- Colori delle icone: `info`, `success`, `warning`, `danger`.""",
	),
)

C["Toast"] = (
	"Feedback",
	130,
	f"""<div class="dc stage col" style="align-items:flex-start;gap:8px">
 <div class="dc-toast">{ic('check').replace('dc-icon','dc-icon dc-icon--ok')}<span>Appuntamento spostato alle 11:00.</span><button class="dc-toast__action">Annulla</button></div>
 <div class="dc-toast"><i class="dc-cross dc-toast__mark"></i><span>Promemoria inviato a 12 pazienti.</span><button class="dc-btn dc-btn--ghost dc-btn--icon dc-btn--xs" style="margin-left:auto" aria-label="Chiudi">{ic('x')}</button></div>
</div>""",
	R(
		"La conferma di qualcosa appena fatto.",
		"""`toast.success(…)`, `toast.error(…)` (`<Toasts />`): fondo `surface-gray-9`, `rounded-md`, alto ~40px, azione in `ink-blue-link`.""",
		"""- Fondo **`block-deep`** (verde profondo) invece del grigio, con la coda della nuvola.
- Segno a sinistra in menta: la spunta per i successi, la **croce** per gli invii e le creazioni; azione ("Annulla") in menta.
- Errori: restano sul rosso di frappe-ui.""",
	),
)

C["Tooltip"] = (
	"Feedback",
	90,
	"""<div class="dc stage row" style="gap:28px;padding-top:28px">
 <span class="dc-tooltip">Invia promemoria</span>
 <span class="dc-tooltip">Duplica <kbd>⌘D</kbd></span>
 <span class="dc-tooltip">Ultimo accesso: oggi 09:12</span>
</div>""",
	R(
		"La spiegazione breve al passaggio del mouse.",
		"""`<Tooltip text placement>`: `rounded`, `px-2 py-1`, `text-xs`, fondo `surface-gray-10`.""",
		"""Fondo `surface-gray-10`, il grigio più scuro di Espresso, tinto di verde come gli altri: non il pieno del marchio, perché il tooltip non è un'azione. La freccia ha lo stesso colore del fumetto. Obbligatorio sui pulsanti con sola icona.""",
	),
)

C["Dialog"] = (
	"Feedback",
	330,
	f"""<div class="dc" style="padding:16px"><div class="dc-overlay">
 <div class="dc-dialog" role="dialog" aria-labelledby="t"><div class="dc-dialog__body">
  <div class="dc-dialog__head"><span class="dc-dialog__icon dc-dialog__icon--red">{ic('calendar-days')}</span><h2 class="dc-dialog__title" id="t">Annullare la visita?</h2><button class="dc-btn dc-btn--ghost dc-btn--icon dc-btn--xs" aria-label="Chiudi">{ic('x')}</button></div>
  <p class="dc-dialog__text">Mario Rossi riceverà un messaggio WhatsApp con l'annullamento. Lo slot delle 10:30 torna libero per la lista d'attesa.</p>
  <label class="dc-check" style="margin-top:14px"><input type="checkbox" checked> Proponi un nuovo orario</label>
  <div class="dc-dialog__actions"><button class="dc-btn dc-btn--subtle dc-btn--md">Indietro</button><button class="dc-btn dc-btn--danger dc-btn--md">Annulla la visita</button></div>
 </div></div></div></div>""",
	R(
		"La finestra per una decisione o un modulo breve.",
		"""`<Dialog v-model :options="{ title, message, icon, size, actions }">`: `rounded-xl`, `bg-surface-elevation-1`, `px-6 pt-5 pb-6`; icona in un cerchio da 28px; azioni a destra.""",
		"""- Forma: `rounded-xl` con la coda della nuvola; anche l'icona sta in una piccola nuvola.
- Velo `overlay` tinto di verde.
- L'azione: `solid` (o `solid` rosso se distruttiva) con verbo e oggetto; "Indietro" `subtle`.""",
		"""`size: 'md'` per le conferme, `'xl'`/`'2xl'` per i moduli. Esc chiude.""",
	),
)

C["EmptyState"] = (
	"Feedback",
	260,
	"""<div class="dc" style="padding:20px"><div class="dc-card"><div class="dc-empty">
 <div class="dc-empty__art" aria-hidden="true">
  <i style="left:0;top:10px;width:36px;height:50px;border-radius:10px 10px 10px 2px;background:var(--teal-700)"></i>
  <i class="dc-cross" style="--s:14px;--c:var(--mint-300);left:11px;top:22px;position:absolute"></i>
  <i style="left:42px;top:0;width:54px;height:28px;border-radius:10px 10px 10px 2px;background:var(--brand)"></i>
  <i style="left:42px;top:34px;width:30px;height:26px;border-radius:10px 10px 10px 2px;background:var(--mint-300)"></i>
  <i style="left:49px;top:25px;width:16px;height:16px;border-radius:50%;background:var(--mint-300);clip-path:inset(0 0 50% 0)"></i>
  <i style="left:78px;top:34px;width:18px;height:26px;border-radius:7px 7px 7px 2px;background:var(--ink-gray-9)"></i>
 </div>
 <h3 class="dc-empty__title">Nessuna visita oggi</h3>
 <p class="dc-empty__text">L'agenda della Dott.ssa Bianchi è libera. Puoi aprire gli slot alla lista d'attesa o prenotare una visita.</p>
 <div class="row" style="justify-content:center;margin-top:6px"><button class="dc-btn dc-btn--outline">Apri alla lista d'attesa</button><button class="dc-btn dc-btn--solid">Nuovo appuntamento</button></div>
</div></div></div>""",
	R(
		"Quando non c'è niente da mostrare: una piccola composizione di blocchi del marchio, una frase, l'azione.",
		"""In frappe-ui è lo slot vuoto di `ListView` (`ListEmptyState`) o un blocco in pagina.""",
		"""- L'illustrazione è sempre fatta con i pezzi della copertina: blocchi `teal-700`, `brand`, `mint-300`, `ink-gray-9` con la coda della nuvola, una gobba e la croce. 96×60px: piccola, non una scena.
- Titolo `lg-semibold`, testo `text-sm` in `ink-gray-5`, poi uno o due pulsanti.""",
		"""Il titolo dice lo stato ("Nessuna visita oggi"); il testo usa i nomi veri e propone l'azione.""",
	),
)

C["Card"] = (
	"Contenitori",
	200,
	f"""<div class="dc stage grid2">
 <div class="dc-card"><div class="dc-card__head"><h3 class="dc-card__title"><span class="dc-card__mark">{ic('calendar-days')}</span>Prossimo appuntamento</h3><span class="dc-badge dc-badge--green">Confermato</span></div>
  <div class="dc-person"><span class="dc-avatar dc-avatar--lg">MR</span><div><div class="dc-person__name" style="font-weight:500">Mario Rossi</div><div class="dc-muted" style="font-size:13px;margin-top:3px">Visita cardiologica · 10:30 · Studio 2</div></div></div></div>
 <div class="dc-card"><div class="dc-card__head"><h3 class="dc-card__title"><span class="dc-card__mark" style="background:var(--cat-rose-subtle);color:var(--cat-rose-text)">{ic('heart-pulse')}</span>Dati clinici</h3><button class="dc-btn dc-btn--ghost dc-btn--icon dc-btn--xs" aria-label="Modifica">{ic('pencil')}</button></div>
  <dl class="dc-kv" style="margin:0"><dt>Allergie</dt><dd><span class="dc-tag dc-tag--rose">Penicillina</span></dd><dt>Gruppo sanguigno</dt><dd>A+</dd><dt>Medico curante</dt><dd>Dott. Verdi</dd></dl></div>
</div>""",
	R(
		"Il riquadro di un argomento: blocchi della scheda paziente, riepiloghi.",
		"""Non c'è un Card in frappe-ui 1.0: è un `div` con `rounded-lg border border-outline-gray-1 p-4` (o `shadow` per le carte che galleggiano).""",
		"""- `rounded-lg` (12px) con la coda della nuvola; filetto `outline-gray-1`.
- Titolo `lg-semibold` con un piccolo segno a nuvola (24px) in `brand-subtle` o nel colore della categoria.
- Dati come coppie etichetta/valore (`ink-gray-5` / `ink-gray-8`).""",
	),
)

C["StatTile"] = (
	"Contenitori",
	160,
	"""<div class="dc stage" style="display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:12px">
 <div class="dc-stat dc-stat--brand"><i class="dc-crosses"></i><span class="dc-stat__label">Visite di oggi</span><span class="dc-stat__value">38<span class="dc-stat__delta">+6</span></span></div>
 <div class="dc-stat"><i class="dc-crosses"></i><span class="dc-stat__label">Incassato a settembre</span><span class="dc-stat__value">€ 48.250</span></div>
 <div class="dc-stat"><i class="dc-crosses"></i><span class="dc-stat__label">In lista d'attesa</span><span class="dc-stat__value">12</span></div>
 <div class="dc-stat"><i class="dc-crosses"></i><span class="dc-stat__label">Moduli da firmare</span><span class="dc-stat__value">4</span></div>
</div>""",
	R(
		"Il numero della dashboard. Il primo della fila è un blocco pieno con il motivo delle croci, come la copertina.",
		"""Nel gestionale è il widget numerico della dashboard (`components/Dashboard/`); in frappe-ui si costruisce con un `div` `rounded-xl`.""",
		"""- `rounded-xl` (16px) con la coda della nuvola; numero `metric` (28px bold, cifre tabulari), etichetta `text-sm` `ink-gray-6`.
- Il motivo delle **croci** nell'angolo in alto a destra: in `brand-subtle` sui riquadri chiari, in menta sul blocco.
- Il numero più importante della fila è un **blocco** `block-deep` (`dc-stat--brand`): uno per fila.""",
		"""Altezza minima 96px; 3–4 per fila.""",
	),
)

C["AgendaEvent"] = (
	"Agenda",
	190,
	f"""<div class="dc stage grid3" style="gap:8px">
 <div class="dc-event dc-event--rose"><span class="dc-event__time">09:00 – 09:30</span><span class="dc-event__title">Mario Rossi</span><span class="dc-event__meta">Visita cardiologica · Studio 2</span></div>
 <div class="dc-event dc-event--now"><span class="dc-event__time">{X(8)}Adesso · 09:30 – 10:00</span><span class="dc-event__title">Giulia Bianchi</span><span class="dc-event__meta">Ecografia addome</span></div>
 <div class="dc-event dc-event--violet"><span class="dc-event__time">10:00 – 11:00</span><span class="dc-event__title">Luca Verdi</span><span class="dc-event__meta">Fisioterapia · ciclo 3/10</span></div>
 <div class="dc-event dc-event--brand"><span class="dc-event__time">11:00 – 11:20</span><span class="dc-event__title">Anna Neri</span><span class="dc-event__meta">Prima visita</span></div>
 <div class="dc-event dc-event--free"><span class="dc-event__time">11:30 – 12:00</span><span class="dc-event__title">Slot libero</span><span class="dc-event__meta">3 pazienti in lista d'attesa</span></div>
 <div class="dc-event dc-event--cancelled"><span class="dc-event__time">12:00 – 12:30</span><span class="dc-event__title">Sara Conti</span><span class="dc-event__meta">Annullato dal paziente</span></div>
</div>""",
	R(
		"La visita nella griglia dell'agenda. Componente DottorCloud.",
		"""Nel gestionale è l'evento del calendario (frappe-ui `Calendar`, slot dell'evento): fondo e barretta vengono dalla categoria della prestazione.""",
		"""- `rounded` (8px) con la coda della nuvola, `text-sm`, orario `text-xs` tabulare nel colore della categoria.
- **Prima visita** e prestazioni del centro: blocco pieno `brand-solid`.
- **Adesso**: anello `brand` e la croce prima dell'orario.
- **Slot libero**: a strisce ambra con contorno, per proporlo alla lista d'attesa.
- **Annullato**: grigio e barrato.""",
	),
)

C["DatePicker"] = (
	"Agenda",
	330,
	"""<div class="dc stage" style="align-items:flex-start;gap:24px">
 <div class="col" style="gap:6px"><label class="dc-field" style="width:244px"><span class="dc-label">Data della visita</span><span class="dc-input is-focus"><span>15/10/2026</span></span></label>
 <div class="dc-cal">
  <div class="dc-cal__head">Ottobre 2026<span class="row" style="gap:2px"><button class="dc-btn dc-btn--ghost dc-btn--icon dc-btn--xs" aria-label="Mese precedente">‹</button><button class="dc-btn dc-btn--ghost dc-btn--icon dc-btn--xs" aria-label="Mese successivo">›</button></span></div>
  <div class="dc-cal__grid">"""
	+ "".join(f'<span class="dc-cal__dow">{d}</span>' for d in ["L", "M", "M", "G", "V", "S", "D"])
	+ "".join(f'<span class="dc-cal__day is-out">{d}</span>' for d in [28, 29, 30])
	+ "".join(
		f'<span class="dc-cal__day{" is-today" if d==1 else ""}{" is-selected" if d==15 else ""}{" has-dot" if d in (7,9,21) else ""}">{d}</span>'
		for d in range(1, 32)
	)
	+ "".join(f'<span class="dc-cal__day is-out">{d}</span>' for d in [1])
	+ """</div>
  <div class="dc-cal__foot"><button class="dc-btn dc-btn--ghost dc-btn--xs">Oggi</button><button class="dc-btn dc-btn--ghost dc-btn--xs">Cancella</button></div>
 </div></div>
</div>""",
	R(
		"La scelta di una data.",
		"""`<DatePicker v-model>` / `<DateTimePicker>`: campo come TextInput, calendario in un popover (`rounded-lg`, `shadow-lg`), giorni in griglia, oggi evidenziato, scelto in `surface-gray-10`.""",
		"""- Giorno scelto: `brand-solid` con la coda della nuvola.
- **Oggi**: numero in `brand-solid` con una piccola **croce** sotto, al posto del punto.
- Pallino ambra sui giorni con posti dalla lista d'attesa (facoltativo, solo nell'agenda).""",
		"""Formato `gg/mm/aaaa`, settimana che parte dal lunedì.""",
	),
)

C["FileUploader"] = (
	"Moduli",
	170,
	f"""<div class="dc stage grid2">
 <div class="col" style="gap:8px">
  <div class="dc-drop"><span class="dc-drop__mark">{ic('paperclip')}</span><span><b style="color:var(--ink-gray-8);font-weight:500">Trascina qui il referto</b><br><span style="font-size:12px">oppure scegli un file · PDF o immagine, fino a 10 MB</span></span></div>
  <div class="dc-drop is-over"><span class="dc-drop__mark">{X(11)}</span><span><b style="font-weight:500">Rilascia per allegare</b></span></div>
 </div>
 <div class="col" style="gap:6px">
  <div class="dc-file"><span class="dc-tag dc-tag--blue">PDF</span><span style="flex:1"><span class="dc-file__name">Ecografia_addome.pdf</span><br><span class="dc-file__meta">1,2 MB · caricato ora</span></span><button class="dc-btn dc-btn--ghost dc-btn--icon dc-btn--xs" aria-label="Rimuovi">{ic('x')}</button></div>
  <div class="dc-file"><span class="dc-spinner"></span><span style="flex:1"><span class="dc-file__name">Referto_cardiologico.pdf</span><div class="dc-progress__track" style="margin-top:6px"><div class="dc-progress__fill" style="width:40%"></div></div></span></div>
 </div>
</div>""",
	R(
		"Il caricamento di documenti: referti, consensi, immagini.",
		"""`<FileUploader :fileTypes :validateFile @success>` con uno slot per l'area di rilascio; avanzamento con `Progress`.""",
		"""- L'area di rilascio ha la coda della nuvola e un segno a nuvola; quando ci passa sopra un file diventa `brand-subtle` e il segno mostra la **croce**.
- File caricati come righe con il Tag del tipo (PDF `blue`).""",
	),
)

C["PatientJourney"] = (
	"Agenda",
	110,
	f"""<div class="dc stage" style="display:block"><ol class="dc-journey">
 <li class="is-done"><span class="dc-journey__dot">{ic('check')}</span><span class="dc-journey__label">Arriva</span><span class="dc-journey__meta">Da Instagram · 2 set</span></li>
 <li class="is-done"><span class="dc-journey__dot">{ic('check')}</span><span class="dc-journey__label">Prenota</span><span class="dc-journey__meta">Online · 3 set</span></li>
 <li class="is-current"><span class="dc-journey__dot">{X(9)}</span><span class="dc-journey__label">Visita</span><span class="dc-journey__meta">Oggi, 10:30</span></li>
 <li><span class="dc-journey__dot">4</span><span class="dc-journey__label">Dopo</span><span class="dc-journey__meta">Referto e fattura</span></li>
 <li><span class="dc-journey__dot">5</span><span class="dc-journey__label">A casa</span><span class="dc-journey__meta">Piano di esercizi</span></li>
</ol></div>""",
	R(
		"Il percorso del paziente, Arriva → Prenota → Visita → Dopo → A casa, compatto. Componente DottorCloud.",
		"""Non c'è in frappe-ui: è una lista di 5 tappe in testa alla scheda paziente e nell'area paziente.""",
		"""Tappe a nuvola da 20px: fatte `brand-solid` con la spunta, la corrente menta con la **croce**, le prossime con il numero; linea `brand` fra le tappe fatte.""",
	),
)

for name, (group, h, body, readme) in C.items():
	d = f"{OUT}/{name}"
	os.makedirs(d, exist_ok=True)
	open(f"{d}/anteprima.html", "w").write(page(group, h, body))
	open(f"{d}/README.md", "w").write(f"# {name}\n\n" + readme)
print(len(C))
