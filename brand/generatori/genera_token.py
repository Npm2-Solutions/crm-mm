# Copyright (c) 2026, NPM2 Solutions Srl and contributors
"""I token del design system: grigi di Espresso tinti, colori del marchio, stati, categorie,
tipografia, spazi, raggi, ombre. Controlla i contrasti e scrive ../design-system/espresso/tokens.json.
Uso: python3 genera_token.py"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from contrasto import cr
from oklch import tint
from percorsi import TOKEN

H = 182  # tinta del marchio (#12a594 in OKLCH)


def t(h):
	return tint(h, 0.009, H)


C = []


def c(name, light, dark, usage):
	C.append((name, light, dark, usage))


# ---------- Palette del marchio ----------
c(
	"teal-50",
	"#f0faf8",
	None,
	"Fondo appena tinto: righe selezionate nel tema chiaro, zone del marchio molto leggere.",
)
c("teal-100", "#e1f5f1", None, "Verde chiaro del marchio: fondi di chip, cerchi delle icone, pulsanti tenui.")
c("teal-200", "#bfeae2", None, "Bordi e anelli su fondi verdi chiari.")
c("teal-300", "#8fdbcf", None, "Tracce di avanzamento e grafici, sul chiaro.")
c(
	"mint-300",
	"#5fe0cc",
	None,
	"Menta: il marchio su fondo scuro, la croce sui blocchi verdi, il colore d'azione nel tema scuro.",
)
c("teal-400", "#17b8a4", None, "Inizio della sfumatura dell'icona dell'app. Solo nell'icona.")
c(
	"teal-500",
	"#12a594",
	None,
	"Verde acqua, il colore del logo. Nell'interfaccia solo per segni non testuali (indicatori, barre, anello di focus): 3:1 sul bianco.",
)
c("teal-600", "#0e8a7c", None, "Passo intermedio della scala, per grafici e hover su teal-500.")
c(
	"teal-700",
	"#0b6f64",
	None,
	"Verde acqua scuro: il pulsante principale e la casella spuntata su chiaro (bianco sopra 6:1).",
)
c("teal-800", "#095a51", None, "Hover e premuto del pulsante principale.")
c("teal-900", "#0b3f39", None, "Testo verde su fondi menta e teal-100 quando serve più contrasto.")
c("teal-950", "#0b2e2a", None, "Verde profondo: testo sulla menta, toast, blocco scuro.")
c("ink-900", "#16201e", None, 'Inchiostro del logo ("Dottor").')
c("night-950", "#111413", None, "Notte: copertine, video, slide di apertura.")

# ---------- Espresso (frappe-ui), grigi tinti di verde ----------
fr_l = {
	"surface-gray-1": "#f8f8f8",
	"surface-gray-2": "#f3f3f3",
	"surface-gray-3": "#ededed",
	"surface-gray-4": "#e2e2e2",
	"surface-gray-5": "#c7c7c7",
	"surface-gray-6": "#999999",
	"surface-gray-7": "#7c7c7c",
	"surface-gray-8": "#525252",
	"surface-gray-9": "#383838",
	"surface-gray-10": "#171717",
}
fr_d = {
	"surface-gray-1": "#1f1f1f",
	"surface-gray-2": "#292929",
	"surface-gray-3": "#383838",
	"surface-gray-4": "#424242",
	"surface-gray-5": "#575757",
	"surface-gray-6": "#7a7a7a",
	"surface-gray-7": "#999999",
	"surface-gray-8": "#afafaf",
	"surface-gray-9": "#d9d9d9",
	"surface-gray-10": "#f8f8f8",
}
use = {
	"surface-gray-1": "Fondo appena staccato: barra laterale, intestazioni di lista, campi disabilitati.",
	"surface-gray-2": "Il fondo dei campi (TextInput subtle), dei pulsanti subtle, delle intestazioni di lista, del segmentato.",
	"surface-gray-3": "Hover di righe, voci di menu e pulsanti ghost/subtle.",
	"surface-gray-4": "Premuto (active) di pulsanti e voci; binario dello switch spento.",
	"surface-gray-5": "Separatori forti, binari di slider.",
	"surface-gray-6": "Segni neutri pieni (pallini di stato neutri).",
	"surface-gray-7": "Segni neutri pieni scuri.",
	"surface-gray-8": "Superfici scure secondarie.",
	"surface-gray-9": "Tooltip e superfici scure (in Espresso anche il toast).",
	"surface-gray-10": "Il pieno più scuro di Espresso. In DottorCloud il pulsante solid e lo switch acceso lo sostituiscono con brand-solid (marchio.css).",
}
c(
	"surface-base",
	"#ffffff",
	t("#171717"),
	"Fondo della pagina, delle carte e dei campi outline (Espresso: surface-base).",
)
for k in fr_l:
	c(k, t(fr_l[k]), t(fr_d[k]), use[k])
c("surface-sidebar", t("#f8f8f8"), t("#171717"), "Fondo della barra laterale.")
c("surface-elevation-1", "#ffffff", t("#1f1f1f"), "Menu, popover, select aperte.")
c("surface-elevation-2", "#ffffff", t("#242424"), "Finestre di dialogo; la voce attiva della barra laterale.")
ink_l = {
	"ink-gray-2": "#e2e2e2",
	"ink-gray-3": "#c7c7c7",
	"ink-gray-4": "#999999",
	"ink-gray-5": "#7c7c7c",
	"ink-gray-6": "#525252",
	"ink-gray-7": "#383838",
	"ink-gray-8": "#171717",
	"ink-gray-9": "#0f0f0f",
}
ink_d = {
	"ink-gray-2": "#383838",
	"ink-gray-3": "#424242",
	"ink-gray-4": "#7a7a7a",
	"ink-gray-5": "#7a7a7a",
	"ink-gray-6": "#999999",
	"ink-gray-7": "#afafaf",
	"ink-gray-8": "#d9d9d9",
	"ink-gray-9": "#f8f8f8",
}
iu = {
	"ink-gray-2": "Testo su fondi scuri molto attenuato.",
	"ink-gray-3": "Disabilitato.",
	"ink-gray-4": "Segnaposto e icone di contorno (chevron). Non per testo da leggere: 2.8:1.",
	"ink-gray-5": "Testo terziario: etichette dei campi e di sezione, contatori, orari secondari. ≥4.5:1 su surface-base, surface-gray-1 e (chiaro) surface-gray-2: un passo più scuro del grigio di Espresso, che si fermava a 4.2:1.",
	"ink-gray-6": "Testo secondario e icone dei controlli: metadati, aiuti sotto i campi (≥7:1).",
	"ink-gray-7": "Testo del corpo un po' più morbido (descrizioni).",
	"ink-gray-8": "Testo principale: campi, liste, pulsanti subtle/outline.",
	"ink-gray-9": "Titoli e testo in evidenza.",
}
c("ink-base", "#ffffff", t("#171717"), "Testo su pieni scuri (Espresso: ink-base).")
# the labels' gray a step darker than Espresso's tinted one, so that it reads
# at 4.5:1 on white and on the sidebar (Espresso's stops at 4.2): the values
# chosen in the browser when the system was applied (design-system/espresso/frappe-ui.md)
FISSI = {"ink-gray-5": ("#6a716f", "#858c8a")}
for k in ink_l:
	c(k, *FISSI.get(k, (t(ink_l[k]), t(ink_d[k]))), iu[k])
out_l = {
	"outline-gray-1": "#ededed",
	"outline-gray-2": "#e2e2e2",
	"outline-gray-3": "#c7c7c7",
	"outline-gray-4": "#999999",
	"outline-gray-5": "#7c7c7c",
}
out_d = {
	"outline-gray-1": "#242424",
	"outline-gray-2": "#383838",
	"outline-gray-3": "#424242",
	"outline-gray-4": "#575757",
	"outline-gray-5": "#7a7a7a",
}
ou = {
	"outline-gray-1": "Filetti: bordi delle carte, separatori delle liste, bordo sotto le schede.",
	"outline-gray-2": "Bordo dei controlli outline (pulsante, campo); come in Espresso è un bordo leggero: il controllo si riconosce anche dalla forma e dal fondo.",
	"outline-gray-3": "Hover del bordo dei controlli outline.",
	"outline-gray-4": "Focus dei campi e bordo della checkbox vuota (3:1 sul bianco: il segno che deve vedersi).",
	"outline-gray-5": "Bordi forti.",
}
for k in out_l:
	c(k, t(out_l[k]), t(out_d[k]), ou[k])

# ---------- DottorCloud: marchio nei componenti ----------
c(
	"brand",
	"{teal-500}",
	"{mint-300}",
	"Il marchio nell'interfaccia: logo, indicatore della scheda attiva, barre di avanzamento, la croce. Non per testo su chiaro (3:1).",
)
c(
	"brand-solid",
	"{teal-700}",
	"{mint-300}",
	"Il pieno d'azione: pulsante solid, checkbox spuntata, radio scelto, switch acceso. È --brand-action di marchio.css.",
)
c("brand-solid-hover", "{teal-800}", "#86e8d8", "Hover e premuto di brand-solid.")
c("on-brand-solid", "#ffffff", "{teal-950}", "Testo, spunta e croce su brand-solid (6:1 chiaro, 9:1 scuro).")
c(
	"brand-subtle",
	"{teal-100}",
	"#12302c",
	"Fondo tenue del marchio: voce attiva della barra laterale, pulsante subtle del marchio, avatar dei pazienti.",
)
c("brand-subtle-hover", "#c9ece5", "#18403b", "Hover di brand-subtle.")
c("on-brand-subtle", "{teal-700}", "{mint-300}", "Testo e icone su brand-subtle (5.3:1 chiaro).")
c(
	"focus",
	"{teal-600}",
	"{mint-300}",
	"Anello di focus: 2px pieno attorno al controllo (sostituisce il grigio di Espresso); ≥3:1 su surface-base e surface-gray-2.",
)
c("text-link", "{teal-700}", "{mint-300}", "Link nel testo.")
c("overlay", "rgba(11, 46, 42, 0.32)", "rgba(0, 0, 0, 0.6)", "Velo dietro le finestre di dialogo.")

# ---------- Blocchi pieni (copertina, StatTile, toast) ----------
c(
	"block-deep",
	"{teal-950}",
	"#123b36",
	"Verde profondo: toast, fascia delle finestre importanti, il numero principale.",
)
c("on-block-deep", "{teal-100}", "#e1f5f1", "Testo su block-deep (12.9:1).")
c("on-block-deep-muted", "#8fc7bd", "#9fd3c9", "Testo secondario su block-deep.")
c("block-mint", "{mint-300}", "{mint-300}", "Blocco menta: la croce in evidenza, piccoli blocchi d'accento.")
c("on-block-mint", "{teal-950}", "{teal-950}", "Testo e croce su block-mint (9:1).")

# ---------- Stati ----------
c(
	"success",
	"#177a42",
	"#4cd38a",
	"Fatto, confermato, pagato: testo e icone su surface-base e success-subtle. In Espresso: ink-green-8.",
)
c("success-subtle", "#e3f6ea", "#133222", "Fondo di badge e avvisi di successo (surface-green-2).")
c(
	"warning",
	"#8a5300",
	"#f5b544",
	"Da controllare, in scadenza: testo e icone su surface-base e warning-subtle. Più scuro dell'ink-amber-8 di Espresso, che sul suo fondo non arriva a 4.5:1.",
)
c("warning-subtle", "#fdf2dc", "#3a2a0c", "Fondo di badge e avvisi di attenzione (surface-amber-2).")
c(
	"danger",
	"#c8323c",
	"#ff7a80",
	"Errori, annullato: testo e icone su surface-base e danger-subtle; fondo del pulsante solid rosso.",
)
c("danger-subtle", "#fdeaea", "#3a1517", "Fondo di badge e avvisi d'errore (surface-red-2).")
c("on-danger", "#ffffff", "#2a0b0d", "Testo sul pulsante solid rosso.")
c("info", "#2459c9", "#7aa5ff", "Informazioni: testo e icone su surface-base e info-subtle.")
c("info-subtle", "#e6eefe", "#15233f", "Fondo di badge e avvisi informativi (surface-blue-2).")

# ---------- Categorie ----------
for key, solid, soft, text, dsolid, dsoft, dtext, what in [
	(
		"blue",
		"#2f6fed",
		"#e6eefe",
		"#2459c9",
		"#7aa5ff",
		"#15233f",
		"#a9c4ff",
		"documenti, ecografie, i nostri messaggi in chat",
	),
	("violet", "#7c5cf0", "#efeafe", "#5b3fd0", "#b9a6ff", "#231a44", "#cfc2ff", "esercizi, marketing"),
	(
		"amber",
		"#d98a0b",
		"#fdf2dc",
		"#8a5300",
		"#f5b544",
		"#3a2a0c",
		"#f8cb7a",
		"lista d'attesa, nutrizione, note interne",
	),
	(
		"rose",
		"#e0487a",
		"#fde8ef",
		"#b02a5a",
		"#ff8fb4",
		"#3d1424",
		"#ffb3cc",
		"cardiologia, allergie, registrazione",
	),
	(
		"green",
		"#1f9d55",
		"#e3f6ea",
		"#177a42",
		"#4cd38a",
		"#133222",
		"#86e3b0",
		"fatto e confermato, WhatsApp",
	),
]:
	extra = (
		" Valore storico tenuto esatto: 2.8:1 sul bianco; per icone piccole usa cat-amber-text."
		if key == "amber"
		else ""
	)
	c(
		f"cat-{key}",
		solid,
		dsolid,
		f"Accento pieno per {what}: pallini, barrette degli eventi, icone grandi. Non per testo.{extra}",
	)
	c(f"cat-{key}-subtle", soft, dsoft, f"Fondo per {what}: tag, eventi in agenda, cerchi icona.")
	c(f"cat-{key}-text", text, dtext, f"Testo e icone piccole su cat-{key}-subtle e surface-base.")


def resolve(v, theme):
	while v and v.startswith("{"):
		n = v[1:-1]
		tt = next(x for x in C if x[0] == n)
		v = tt[1] if theme == "light" or tt[2] is None else tt[2]
	return v


tokens = [
	{"name": n, "value": ({"light": l} if d is None else {"light": l, "dark": d}), "usage": u}
	for n, l, d, u in C
]

checks = (
	[
		(
			"ink-gray-9",
			["surface-base", "surface-gray-1", "surface-gray-2", "surface-gray-3", "surface-elevation-2"],
			4.5,
		),
		(
			"ink-gray-8",
			["surface-base", "surface-gray-1", "surface-gray-2", "surface-gray-3", "brand-subtle"],
			4.5,
		),
		("ink-gray-6", ["surface-base", "surface-gray-1", "surface-gray-2"], 4.5),
		("ink-gray-5", ["surface-base", "surface-gray-1"], 4.5),
		("on-brand-solid", ["brand-solid", "brand-solid-hover"], 4.5),
		("on-brand-subtle", ["brand-subtle", "brand-subtle-hover"], 4.5),
		("on-block-deep", ["block-deep"], 4.5),
		("on-block-deep-muted", ["block-deep"], 4.5),
		("on-block-mint", ["block-mint"], 4.5),
		("on-danger", ["danger"], 4.5),
		("text-link", ["surface-base"], 4.5),
		("focus", ["surface-base", "surface-gray-2"], 3),
		("outline-gray-4", ["surface-base"], 2.4),
	]
	+ [(s, ["surface-base", s + "-subtle"], 4.5) for s in ["success", "warning", "danger", "info"]]
	+ [
		(f"cat-{k}-text", ["surface-base", f"cat-{k}-subtle"], 4.5)
		for k in ["blue", "violet", "amber", "rose", "green"]
	]
)
bad = 0
for fg, grounds, need in checks:
	for th in ["light", "dark"]:
		for g in grounds:
			a = resolve("{" + fg + "}", th)
			b = resolve("{" + g + "}", th)
			r = cr(a, b)
			if r < need:
				bad += 1
				print(f"FAIL {th}: {fg} {a} on {g} {b} = {r:.2f} < {need}")
print("fails", bad)

T = {
	"name": "DottorCloud",
	"version": 4,
	"meta": {
		"source": "github",
		"repo": "Npm2-Solutions/crm-mm",
		"ref": "develop@4d5b871",
		"basedOn": "frappe-ui 1.0.0-beta.29 (Espresso)",
		"paths": {
			"tokens": [
				"brand/design-system/tokens.css",
				"frontend/src/utils/marchio.js",
				"frontend/src/marchio.css",
				"frontend/package.json (frappe-ui)",
			],
			"fonts": ["brand/font/Inter-Variable-latin.woff2"],
			"assets": ["brand/logo/"],
			"docs": ["brand/design-system/README.md", "brand/logo/README.md"],
		},
		"synced": "2026-10-01",
		"note": "Espresso di frappe-ui con il marchio DottorCloud: grigi tinti, colore d'azione del marchio, nuvola e croce come segni.",
	},
	"color": {
		"themes": [{"id": "light", "name": "Chiaro"}, {"id": "dark", "name": "Scuro"}],
		"tokens": tokens,
	},
	"type": {
		"fonts": [
			{
				"family": "Inter",
				"file": "fonts/Inter-Variable-latin.woff2",
				"weight": "100 900",
				"style": "normal",
			}
		],
		"families": {
			"sans": '"InterVar", "Inter", -apple-system, "Segoe UI", system-ui, sans-serif',
			"office": '"Calibri", "Carlito", sans-serif',
		},
		"groups": [
			{
				"name": "Espresso",
				"family": "sans",
				"styles": [
					{
						"name": "tiny",
						"fontSize": "11px",
						"lineHeight": 1.15,
						"fontWeight": 500,
						"letterSpacing": "0.09em",
						"sample": "IL CENTRO",
						"usage": "text-tiny: etichette di sezione in maiuscolo (uppercase), in ink-gray-5.",
					},
					{
						"name": "xs",
						"fontSize": "12px",
						"lineHeight": 1.15,
						"fontWeight": 420,
						"letterSpacing": "0.02em",
						"sample": "10:30 – 11:00",
						"usage": "text-xs: badge, orari negli eventi, didascalie.",
					},
					{
						"name": "sm",
						"fontSize": "13px",
						"lineHeight": 1.15,
						"fontWeight": 420,
						"letterSpacing": "0.02em",
						"sample": "Ultima modifica 3 minuti fa",
						"usage": "text-sm: metadati, voci della barra laterale, aiuti sotto i campi.",
					},
					{
						"name": "base",
						"fontSize": "14px",
						"lineHeight": 1.15,
						"fontWeight": 420,
						"letterSpacing": "0.02em",
						"sample": "Mario Rossi · visita cardiologica",
						"usage": "text-base: il testo del gestionale (campi, liste, menu, pulsanti).",
					},
					{
						"name": "base-medium",
						"fontSize": "14px",
						"lineHeight": 1.15,
						"fontWeight": 500,
						"letterSpacing": "0.015em",
						"sample": "Salva",
						"usage": "text-base-medium: etichette dei pulsanti md, nomi nelle righe.",
					},
					{
						"name": "p-base",
						"fontSize": "14px",
						"lineHeight": 1.5,
						"fontWeight": 420,
						"letterSpacing": "0.02em",
						"sample": "Riceverà un messaggio WhatsApp con l'annullamento.",
						"usage": "text-p-base: testo su più righe (finestre, note, avvisi).",
					},
					{
						"name": "lg-semibold",
						"fontSize": "16px",
						"lineHeight": 1.15,
						"fontWeight": 600,
						"letterSpacing": "0.01em",
						"sample": "Prossime visite",
						"usage": "text-lg-semibold: titoli di carte e sezioni.",
					},
					{
						"name": "xl-semibold",
						"fontSize": "17px",
						"lineHeight": 1.15,
						"fontWeight": 600,
						"letterSpacing": "0.01em",
						"sample": "Annullare la visita?",
						"usage": "text-xl-semibold: titolo delle finestre di dialogo.",
					},
				],
			},
			{
				"name": "DottorCloud",
				"family": "sans",
				"styles": [
					{
						"name": "page-title",
						"fontSize": "20px",
						"lineHeight": 1.15,
						"fontWeight": 700,
						"letterSpacing": "-0.01em",
						"sample": "Agenda",
						"usage": "Titolo della pagina (PageHeader). Più pieno di Espresso: il titolo è il marchio della pagina.",
					},
					{
						"name": "metric",
						"fontSize": "28px",
						"lineHeight": 1.1,
						"fontWeight": 700,
						"letterSpacing": "-0.02em",
						"sample": "1.284",
						"usage": "Il numero di uno StatTile, con font-variant-numeric: tabular-nums.",
					},
					{
						"name": "tabular",
						"fontSize": "14px",
						"lineHeight": 1.15,
						"fontWeight": 500,
						"letterSpacing": "0.01em",
						"sample": "€ 1.250,00 · 10:30",
						"usage": "Importi e orari in colonna: tabular-nums.",
					},
				],
			},
			{
				"name": "Sito e slide",
				"family": "sans",
				"styles": [
					{
						"name": "display-xl",
						"fontSize": "64px",
						"lineHeight": 0.95,
						"fontWeight": 800,
						"letterSpacing": "-0.045em",
						"sample": "Il centro in un posto solo",
						"usage": "Copertine, sito, video. Mai nel gestionale.",
					},
					{
						"name": "display",
						"fontSize": "40px",
						"lineHeight": 1.0,
						"fontWeight": 800,
						"letterSpacing": "-0.035em",
						"sample": "La fattura nasce dalla visita",
						"usage": "Titoli del sito e delle slide.",
					},
				],
			},
		],
	},
	"spacing": {
		"note": "La scala di Tailwind (4px) usata da frappe-ui.",
		"tokens": [
			{"name": "space-0-5", "value": "2px", "usage": "p-0.5: aggiustamenti ottici."},
			{
				"name": "space-1",
				"value": "4px",
				"usage": "p-1, gap-1: padding dei menu, fra icona e testo nei controlli xs.",
			},
			{
				"name": "space-1-5",
				"value": "6px",
				"usage": "py-1.5, gap-1.5: padding verticale di campi e voci.",
			},
			{
				"name": "space-2",
				"value": "8px",
				"usage": "px-2, gap-2: padding dei controlli sm, gap fra controlli.",
			},
			{"name": "space-2-5", "value": "10px", "usage": "px-2.5: padding dei pulsanti md."},
			{
				"name": "space-3",
				"value": "12px",
				"usage": "p-3: padding delle carte compatte e degli avvisi.",
			},
			{"name": "space-4", "value": "16px", "usage": "p-4: padding delle carte e delle finestre."},
			{
				"name": "space-5",
				"value": "20px",
				"usage": "gap-5: fra le schede (Tabs); margini della pagina.",
			},
			{"name": "space-6", "value": "24px", "usage": "px-6: padding orizzontale delle finestre."},
			{"name": "space-8", "value": "32px", "usage": "Fra sezioni di una pagina."},
		],
	},
	"radius": {
		"note": "I raggi di Espresso (--radius-N di frappe-ui) più la coda della nuvola.",
		"tokens": [
			{"name": "radius-1", "value": "4px", "usage": "rounded-sm: checkbox, tooltip piccoli."},
			{"name": "radius-3", "value": "6px", "usage": "rounded-3: pulsanti xs, voci di menu."},
			{
				"name": "radius-4",
				"value": "8px",
				"usage": "rounded (rounded-4): pulsanti sm/md, campi, voci della barra laterale, righe.",
			},
			{"name": "radius-5", "value": "10px", "usage": "rounded-md: pulsanti lg, segmentato, avvisi."},
			{"name": "radius-6", "value": "12px", "usage": "rounded-lg: carte, menu, popover."},
			{"name": "radius-7", "value": "16px", "usage": "rounded-xl: finestre di dialogo, StatTile."},
			{
				"name": "radius-full",
				"value": "999px",
				"usage": "rounded-full: badge, switch, avatar rotondi.",
			},
			{
				"name": "radius-tail",
				"value": "2px",
				"usage": "La coda della nuvola-D: l'angolo in basso a sinistra di pulsanti solid, avatar, carte, finestre, toast, voce attiva. Il segno del marchio nei componenti.",
			},
		],
	},
	"size": {
		"tokens": [
			{"name": "control-xs", "value": "24px", "usage": "h-6: pulsanti xs, badge lg."},
			{
				"name": "control-sm",
				"value": "28px",
				"usage": "h-7: la misura base di frappe-ui (pulsanti sm, campi, voci della barra laterale).",
			},
			{
				"name": "control-md",
				"value": "32px",
				"usage": "h-8: pulsanti e campi md, azioni principali delle pagine.",
			},
			{
				"name": "control-lg",
				"value": "40px",
				"usage": "h-10: pulsanti lg; su telefono e nell'area paziente.",
			},
			{
				"name": "icon-sm",
				"value": "16px",
				"usage": "size-4: icone dei controlli, delle voci e delle righe.",
			},
		]
	},
	"shadow": {
		"note": "Le elevazioni di Espresso con l'ombra tinta del verde scuro del marchio.",
		"tokens": [
			{
				"name": "elevation-sm",
				"value": {
					"light": "0px 0px 1px 0px rgba(11, 46, 42, 0.2), 0px 1px 3px 0px rgba(11, 46, 42, 0.14)",
					"dark": "0px 0px 14px 0px rgba(0, 0, 0, 0.18), 0px 1px 3px 0px rgba(0, 0, 0, 0.7)",
				},
				"usage": "shadow-sm: campi al focus, voce attiva, pulsante del segmentato.",
			},
			{
				"name": "elevation-base",
				"value": {
					"light": "0px 0px 1.5px 0px rgba(11, 46, 42, 0.16), 0px 2px 5px 0px rgba(11, 46, 42, 0.12)",
					"dark": "0px 0px 14px 0px rgba(0, 0, 0, 0.18), 0px 2px 5px 0px rgba(0, 0, 0, 0.6)",
				},
				"usage": "shadow: carte.",
			},
			{
				"name": "elevation-lg",
				"value": {
					"light": "0px 0px 1.5px 0px rgba(11, 46, 42, 0.18), 0px 18px 22px -6px rgba(11, 46, 42, 0.12)",
					"dark": "0px 0px 16px 0px rgba(0, 0, 0, 0.1), 0px 18px 20px -8px rgba(0, 0, 0, 0.52)",
				},
				"usage": "shadow-lg: menu, popover, toast.",
			},
			{
				"name": "elevation-2xl",
				"value": {
					"light": "0px 0px 1.5px 0px rgba(11, 46, 42, 0.25), 0px 44px 52px -10px rgba(11, 46, 42, 0.12)",
					"dark": "0px 0px 14px 10px rgba(0, 0, 0, 0.12), 0px 44px 52px -4px rgba(0, 0, 0, 0.42)",
				},
				"usage": "shadow-2xl: finestre di dialogo.",
			},
		],
	},
}
OUT = Path(sys.argv[1]) if len(sys.argv) > 1 else TOKEN
OUT.write_text(json.dumps(T, ensure_ascii=False, indent=1) + "\n")
print(len(tokens), "colors")
