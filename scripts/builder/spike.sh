#!/usr/bin/env bash
# Spike: Frappe Builder accanto al CRM, con un componente spedito da noi.
#
# Verifica in un colpo solo le quattro incognite del modulo 15:
#   1. Builder si installa accanto al CRM senza rompere le rotte esistenti
#   2. crm/builder_files/ viene sincronizzato e il componente compare nell'editor
#   3. il component_data_script gira in safe_exec e legge CRM Service
#   4. l'editor si lascia incapsulare in un iframe stesso dominio
#
# Uso (dalla root del bench):
#   ./apps/crm/scripts/builder/spike.sh <site-name>
#
# Per annullare tutto: bench --site <site> uninstall-app builder
set -euo pipefail

SITE="${1:?Uso: spike.sh <site-name>}"
BUILDER_BRANCH="${BUILDER_BRANCH:-main}"

step() { printf '\n\033[1m== %s\033[0m\n' "$1"; }

step "1/5 · Builder sul bench (ramo $BUILDER_BRANCH)"
if [ -d apps/builder ]; then
  echo "   apps/builder c'è già, salto il get-app"
else
  bench get-app builder --branch "$BUILDER_BRANCH"
fi

step "2/5 · Installazione su $SITE"
if bench --site "$SITE" list-apps | grep -qx builder; then
  echo "   builder è già installato su $SITE"
else
  bench --site "$SITE" install-app builder
fi

step "3/5 · Migrate — sincronizza crm/builder_files/"
bench --site "$SITE" migrate

step "4/5 · Il componente è arrivato?"
bench --site "$SITE" execute frappe.client.get_list \
  --kwargs "{'doctype':'Builder Component','filters':{'name':'crm-servizi'},'fields':['name','component_name']}"

step "5/5 · Il data script gira e legge i servizi?"
bench --site "$SITE" execute \
  builder.builder.doctype.builder_component.builder_component.get_component_data \
  --kwargs "{'component_name':'crm-servizi'}"

cat <<'CHECKS'

== Da verificare a mano nel browser ==

  a) Editor raggiungibile         → /builder  (serve il ruolo System Manager o Website Manager)
  b) Il componente c'è            → nuova pagina, pannello componenti, cerca "Servizi CRM"
  c) Le liste si popolano         → trascina il componente, pubblica, apri la rotta pubblica:
                                    devono comparire le card dei CRM Service abilitati
  d) Le props funzionano          → cambia "categoria" e "limite" sull'istanza, ripubblica
  e) HTML non-escaped (atteso)    → verificato sul sorgente di Frappe: get_jenv() non abilita
                                    autoescape, quindi i binding escono come HTML e il blocco
                                    "Form CRM" potrà iniettare il markup del form. Conferma sul
                                    campo: lega innerHTML a una chiave che contiene "<b>x</b>"
                                    e controlla che esca in grassetto. Corollario gia' applicato:
                                    il testo lo escapiamo noi nel data script (escape_html)
  f) Iframe stesso dominio        → in una scheda del CRM apri la console e prova:
                                    document.body.insertAdjacentHTML('beforeend',
                                      '<iframe src="/builder/page/<nome>" style="position:fixed;\
inset:0;width:100vw;height:100vh;z-index:9999"></iframe>')
                                    l'editor deve caricarsi con la sessione già attiva
  g) Rotte del CRM intatte        → /crm, /book/<rotta>, /crm-form/<rotta> rispondono come prima

Nessuno di questi controlli e' piu' un bivio: (e) e (f) sono verificati sul sorgente,
qui si conferma solo che sul bench reale si comportino come letto.
CHECKS
