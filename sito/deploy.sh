#!/usr/bin/env bash
# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt
#
# Publishes the DottorCloud site on the HestiaCP server: builds it for the
# domain, then copies sito/dist into the domain's public_html.
#
#   sito/deploy.sh dottorcloud.preview.npm2solutions.com   # a preview, kept out of search engines
#   sito/deploy.sh dottorcloud.com                          # the site
#   sito/deploy.sh dottorcloud.com --crea                   # also add the domain in the panel if missing,
#                                                          # with its certificate once the DNS points here
#   sito/deploy.sh dottorcloud.com --nginx                  # also install server/nginx.ssl.conf_sito
#   sito/deploy.sh dottorcloud.com --prova                  # only show what would change
#
#   SITO_SSH=root@hosting.npm2solutions.com   who to connect as (the default)
#   SITO_SSH_KEY=~/.ssh/chiave                the key, when ssh-agent or ~/.ssh/config do not have it
#   HESTIA_USER=admin                         the panel user that owns the domain (the default)
#
# It refuses a folder that holds something else, such as a WordPress site: it
# replaces only an empty public_html, the panel's placeholder page, or a copy
# of this site (the .sito-dottorcloud file the build leaves).

set -euo pipefail

usage() {
	sed -n '5,18p' "$0" | sed 's/^# \{0,1\}//'
	exit "${1:-0}"
}

DOMAIN=""
CREATE=0
DRY_RUN=0
NGINX=0
for arg in "$@"; do
	case "$arg" in
	--crea) CREATE=1 ;;
	--prova) DRY_RUN=1 ;;
	--nginx) NGINX=1 ;;
	-h | --help) usage 0 ;;
	-*) echo "Unknown option: $arg" >&2; usage 1 ;;
	*) DOMAIN="$arg" ;;
	esac
done
[[ -n "$DOMAIN" ]] || usage 1
if [[ ! "$DOMAIN" =~ ^[a-z0-9]([a-z0-9-]*[a-z0-9])?(\.[a-z0-9]([a-z0-9-]*[a-z0-9])?)+$ ]]; then
	echo "\"$DOMAIN\" is not a domain name" >&2
	exit 1
fi

SSH_TARGET="${SITO_SSH:-root@hosting.npm2solutions.com}"
PANEL_USER="${HESTIA_USER:-admin}"
SITE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SSH=(ssh -o BatchMode=yes -o ConnectTimeout=15)
if [[ -n "${SITO_SSH_KEY:-}" ]]; then
	SSH+=(-i "$SITO_SSH_KEY" -o IdentitiesOnly=yes)
fi
WEB="/home/$PANEL_USER/web/$DOMAIN"

# a preview answers to its own name and stays out of search engines
export SITO_URL="https://$DOMAIN"
if [[ "$DOMAIN" == *.preview.* ]]; then
	export SITO_ANTEPRIMA=1
else
	export SITO_ANTEPRIMA=""
fi
node "$SITE/build.mjs"

if [[ "$CREATE" == 1 && "$DRY_RUN" == 0 ]]; then
	echo "Preparing $DOMAIN in HestiaCP…"
	"${SSH[@]}" "$SSH_TARGET" bash -s -- "$PANEL_USER" "$DOMAIN" <<'REMOTE'
set -euo pipefail
export HESTIA=/usr/local/hestia
export PATH="$HESTIA/bin:$PATH"
user="$1" domain="$2"
web="/home/$user/web/$domain"
conf="$HESTIA/data/users/$user/web.conf"
here="$(ip -4 route get 1.1.1.1 | awk '{for (i = 1; i < NF; i++) if ($i == "src") print $(i + 1)}')"

points_here() { [[ "$(getent ahostsv4 "$1" | awk 'NR == 1 {print $1}')" == "$here" ]]; }
field() { { grep "^DOMAIN='$domain' " "$conf" || true; } | sed -n "s/.* $1='\([^']*\)'.*/\1/p"; }
has_alias() { [[ ",$(field ALIAS)," == *",$1,"* ]]; }

if [[ ! -d "$web" ]]; then
	v-add-web-domain "$user" "$domain"
	# a brand new domain holds only the panel's page: the site may take it over
	touch "$web/public_html/.sito-dottorcloud"
	echo "Added the web domain $domain."
fi

if ! points_here "$domain"; then
	echo "::warning::$domain does not point to this server ($here) yet: the files go up, the certificate waits for the DNS."
	exit 0
fi

# a certificate can only name what reaches this server
for alias in $(field ALIAS | tr ',' ' '); do
	if ! points_here "$alias"; then
		v-delete-web-domain-alias "$user" "$domain" "$alias"
		echo "Dropped the alias $alias: it does not point here."
	fi
done
if [[ "$domain" != www.* ]] && points_here "www.$domain" && ! has_alias "www.$domain"; then
	v-add-web-domain-alias "$user" "$domain" "www.$domain"
fi

if [[ "$(field LETSENCRYPT)" != yes ]]; then
	if v-add-letsencrypt-domain "$user" "$domain" "$(field ALIAS)"; then
		echo "Let's Encrypt certificate for $domain."
	else
		echo "::warning::Let's Encrypt refused $domain: the site stays on http for now."
		exit 0
	fi
fi
if [[ "$(field SSL_FORCE)" != yes ]]; then
	v-add-web-domain-ssl-force "$user" "$domain"
fi
# www.<domain> answers with a redirect to <domain>
if has_alias "www.$domain" && [[ -z "$(field REDIRECT)" ]]; then
	v-add-web-domain-redirect "$user" "$domain" "$domain" 301
fi
REMOTE
fi

echo "Checking $WEB on $SSH_TARGET…"
"${SSH[@]}" "$SSH_TARGET" bash -s -- "$WEB" <<'REMOTE'
set -euo pipefail
web="$1"
if [[ ! -d "$web/public_html" ]]; then
	echo "$web/public_html does not exist: add the web domain in HestiaCP first (or use --crea)" >&2
	exit 1
fi
cd "$web/public_html"
if [[ -e .sito-dottorcloud ]]; then
	exit 0
fi
# what HestiaCP puts in a new domain, and nothing else
for entry in * .[!.]*; do
	[[ -e "$entry" ]] || continue
	case "$entry" in
	index.html | robots.txt) ;;
	*)
		echo "$web/public_html holds something else ($entry): not touching it" >&2
		exit 1
		;;
	esac
done
if [[ -e index.html ]] && ! grep -qi "hestia" index.html; then
	echo "$web/public_html/index.html is not the panel's placeholder: not touching it" >&2
	exit 1
fi
REMOTE

RSYNC=(rsync -rlz --delete --chmod=D755,F644 -e "${SSH[*]}")
if [[ "$DRY_RUN" == 1 ]]; then
	"${RSYNC[@]}" --dry-run --itemize-changes "$SITE/dist/" "$SSH_TARGET:$WEB/public_html/"
	echo "Nothing was changed (--prova)."
	exit 0
fi
"${RSYNC[@]}" "$SITE/dist/" "$SSH_TARGET:$WEB/public_html/"

# owner, the 404 where the panel looks for it, the form's settings if missing
"${SSH[@]}" "$SSH_TARGET" bash -s -- "$WEB" "$PANEL_USER" "$DOMAIN" <<'REMOTE'
set -euo pipefail
web="$1" user="$2" domain="$3"
chown -R "$user:$user" "$web/public_html"
if [[ -d "$web/document_errors" ]]; then
	cp "$web/public_html/404.html" "$web/document_errors/404.html"
	chown "$user:$user" "$web/document_errors/404.html"
fi
mkdir -p "$web/private"
if [[ ! -e "$web/private/sito.ini" ]]; then
	sender="sito@${domain#www.}"
	cat >"$web/private/sito.ini" <<INI
; The demo form of the DottorCloud site (sito/api/richiesta-demo.php)
destinatario = "info@npm2solutions.com"
mittente = "$sender"
cartella = "$web/private"
; archivio = "$web/private/richieste-demo.jsonl"
INI
	echo "Wrote $web/private/sito.ini: check who receives the requests and who sends them."
fi
chown -R "$user:$user" "$web/private"
chmod 750 "$web/private"
chmod 640 "$web/private/sito.ini"
REMOTE

if [[ "$NGINX" == 1 ]]; then
	CONF="/home/$PANEL_USER/conf/web/$DOMAIN/nginx.ssl.conf_sito"
	"${SSH[@]}" "$SSH_TARGET" "cat > '$CONF.new'" <"$SITE/server/nginx.ssl.conf_sito"
	"${SSH[@]}" "$SSH_TARGET" bash -s -- "$CONF" <<'REMOTE'
set -euo pipefail
conf="$1"
if [[ -e "$conf" ]] && cmp -s "$conf" "$conf.new"; then
	rm -f "$conf.new"
	echo "nginx: $conf unchanged."
	exit 0
fi
if [[ -e "$conf" ]]; then cp "$conf" "$conf.prima"; fi
mv "$conf.new" "$conf"
if nginx -t 2>/dev/null; then
	systemctl reload nginx
	echo "nginx: $conf installed and reloaded."
else
	# put back what was there, so the other sites keep working
	if [[ -e "$conf.prima" ]]; then mv "$conf.prima" "$conf"; else rm -f "$conf"; fi
	nginx -t
	echo "nginx refused the configuration: nothing changed." >&2
	exit 1
fi
REMOTE
fi

echo "Published: $SITO_URL"
