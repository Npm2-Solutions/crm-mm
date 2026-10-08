# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""The archive without a site (doc 57): the bucket's address and its signature,
the keys, what the plan includes and which files move.

The signature is AWS Signature Version 4, which every S3 service speaks (Hetzner,
Backblaze B2, Cloudflare R2, Scaleway, OVH, AWS): headers for the server's own
calls, a query string for the link a browser follows. Tested on AWS's own
examples.
"""

from __future__ import annotations

import datetime
import hashlib
import hmac
from dataclasses import dataclass
from urllib.parse import quote, urlsplit

#: Minutes a private file stays only on the server before it moves: what was just
#: written (a signed form, its PDF, a thumbnail) is read again in the next minutes.
#: A file brought back to be read moves out again after as long.
ATTESA = 60

#: Seconds a link to the bucket lasts: enough to start a download, short enough
#: that a link copied from the browser is worth nothing tomorrow.
DURATA_DEL_LINK = 300

#: Files moved in one round at most, and bytes: the next round takes the rest.
FILE_PER_GIRO = 500
BYTE_PER_GIRO = 20 * 1024**3

GB = 1024**3
TB = 1024 * GB

#: What each size of the plan includes (the listino, 07/10/2026): growing with
#: the size, 300 GB for one person, two terabytes from the polyclinic up. The
#: agency can write another figure on the plan.
SPAZIO_COMPRESO = {
	"Solo": 300 * GB,
	"Studio": 600 * GB,
	"Centre": 1 * TB,
	"Polyclinic": 2 * TB,
	"Large": 2 * TB,
}
#: A plan without a size yet.
SPAZIO_DI_BASE = 1 * TB

#: The hash of an empty body: what a GET, a HEAD or a DELETE sign.
VUOTO = hashlib.sha256(b"").hexdigest()
#: A link's body is never known in advance.
NON_FIRMATO = "UNSIGNED-PAYLOAD"
ALGORITMO = "AWS4-HMAC-SHA256"

#: The extensions the framework never shows in the browser, only downloads
#: (`frappe.utils.response.FORCE_DOWNLOAD_EXTENSIONS`): the bucket answers the same.
DA_SCARICARE = frozenset(
	(
		".svg",
		".svgz",
		".html",
		".htm",
		".xhtml",
		".xht",
		".shtml",
		".shtm",
		".mhtml",
		".mht",
		".xml",
		".xsl",
		".xslt",
		".swf",
	)
)

#: What `dottorcloud_archivio` must hold.
OBBLIGATORI = ("endpoint", "bucket", "access_key", "secret_key")


@dataclass(frozen=True)
class Configurazione:
	"""The agency's bucket, from `dottorcloud_archivio`.

	``endpoint``: the service's address (``https://fsn1.your-objectstorage.com``);
	``region``: its region as the signature names it (Hetzner ``fsn1``, R2
	``auto``, B2 ``eu-central-003``); ``virtual``: the bucket in the host name
	(``bucket.endpoint``) rather than in the path; ``prefisso``: the folder every
	key of this site starts with - the bucket's folder for DottorCloud
	(``prefix``, so a bucket holds other projects too), then the site's name:
	two sites never share a folder, whatever the common config says.
	"""

	endpoint: str
	bucket: str
	access_key: str
	secret_key: str
	region: str = "us-east-1"
	virtual: bool = False
	prefisso: str = ""

	def indirizzo(self, chiave: str) -> tuple[str, str, str]:
		"""(host, path, base) of an object: the base is scheme and host."""
		parti = urlsplit(self.endpoint.rstrip("/"))
		schema = parti.scheme or "https"
		host = parti.netloc or parti.path
		if self.virtual:
			host = f"{self.bucket}.{host}"
			percorso = "/" + chiave
		else:
			percorso = f"/{self.bucket}/{chiave}" if chiave else f"/{self.bucket}"
		return host, percorso, f"{schema}://{host}"


def configurazione(valore, sito: str = "") -> Configurazione | None:
	"""The bucket as `dottorcloud_archivio` describes it; None where it is not
	there or misses what it needs - the archive then stays off, nothing moves."""
	if not isinstance(valore, dict):
		return None
	if any(not str(valore.get(campo) or "").strip() for campo in OBBLIGATORI):
		return None
	if valore.get("enabled") in (0, False, "0"):
		return None
	prefisso = "/".join(
		parte for parte in (str(valore.get("prefix") or "").strip("/"), (sito or "").strip("/")) if parte
	)
	return Configurazione(
		endpoint=str(valore["endpoint"]).strip(),
		bucket=str(valore["bucket"]).strip(),
		access_key=str(valore["access_key"]).strip(),
		secret_key=str(valore["secret_key"]).strip(),
		region=str(valore.get("region") or "us-east-1").strip(),
		virtual=bool(valore.get("virtual_host")),
		prefisso=prefisso,
	)


def chiave(prefisso: str, sha256: str, nome: str) -> str:
	"""Where a file's content lives in the bucket: the site's folder, its
	fingerprint (two files with the same content are one object, a content
	rewritten under the same address is another), its name for whoever looks."""
	nome = (nome or "file").replace("/", "_").replace("\\", "_")
	return "/".join(parte for parte in (prefisso.strip("/"), sha256[:2], sha256, nome) if parte)


def da_spostare(file_url: str | None) -> bool:
	"""A file that moves: a private file of the site. A public one (a logo, a
	picture of the website, an exercise) stays, nginx serves it from the disk."""
	if not file_url or not file_url.startswith("/private/files/"):
		return False
	resto = file_url[len("/private/files/") :]
	return bool(resto) and ".." not in resto.split("/")


def compreso(taglia: str | None, scritto_gb: int | float | None = None) -> int:
	"""Bytes the plan includes: the figure the agency wrote, else the size's."""
	if scritto_gb and float(scritto_gb) > 0:
		return int(float(scritto_gb) * GB)
	return SPAZIO_COMPRESO.get(taglia or "", SPAZIO_DI_BASE)


def disposizione(nome: str) -> str:
	"""The Content-Disposition the bucket answers with: shown in the browser,
	or downloaded where the framework would download it; the name in UTF-8."""
	nome = nome or "file"
	estensione = "." + nome.rsplit(".", 1)[-1].lower() if "." in nome else ""
	modo = "attachment" if estensione in DA_SCARICARE else "inline"
	return f"{modo}; filename*=UTF-8''{quote(nome, safe='')}"


# The signature (AWS Signature Version 4)


def _codifica(testo: str, barre: bool = False) -> str:
	"""URI-encode as S3 asks: every byte but the unreserved ones; '/' kept in a path."""
	return quote(testo, safe="-_.~/" if barre else "-_.~")


def _hmac(chiave: bytes, testo: str) -> bytes:
	return hmac.new(chiave, testo.encode(), hashlib.sha256).digest()


def chiave_di_firma(segreto: str, giorno: str, regione: str, servizio: str = "s3") -> bytes:
	k = _hmac(("AWS4" + segreto).encode(), giorno)
	k = _hmac(k, regione)
	k = _hmac(k, servizio)
	return _hmac(k, "aws4_request")


def _query(parametri: dict) -> str:
	return "&".join(
		f"{_codifica(str(k))}={_codifica(str(v))}"
		for k, v in sorted((str(k), str(v)) for k, v in parametri.items())
	)


def _richiesta_canonica(metodo, percorso, parametri, intestazioni, payload) -> tuple[str, str]:
	nomi = sorted(intestazioni)
	canoniche = "".join(f"{nome}:{' '.join(str(intestazioni[nome]).split())}\n" for nome in nomi)
	firmate = ";".join(nomi)
	testo = "\n".join(
		(metodo, _codifica(percorso, barre=True), _query(parametri), canoniche, firmate, payload)
	)
	return testo, firmate


def _da_firmare(quando: datetime.datetime, ambito: str, canonica: str) -> str:
	return "\n".join(
		(ALGORITMO, quando.strftime("%Y%m%dT%H%M%SZ"), ambito, hashlib.sha256(canonica.encode()).hexdigest())
	)


def firma_intestazioni(
	metodo: str,
	host: str,
	percorso: str,
	*,
	access_key: str,
	secret_key: str,
	regione: str,
	quando: datetime.datetime,
	parametri: dict | None = None,
	intestazioni: dict | None = None,
	payload: str = VUOTO,
) -> dict:
	"""The headers of a signed call: the ones given, host, date, the body's
	hash and Authorization. ``quando`` in UTC."""
	parametri = parametri or {}
	data = quando.strftime("%Y%m%dT%H%M%SZ")
	giorno = quando.strftime("%Y%m%d")
	tutte = {k.lower(): v for k, v in (intestazioni or {}).items()}
	tutte.update({"host": host, "x-amz-date": data, "x-amz-content-sha256": payload})
	canonica, firmate = _richiesta_canonica(metodo, percorso, parametri, tutte, payload)
	ambito = f"{giorno}/{regione}/s3/aws4_request"
	firma = hmac.new(
		chiave_di_firma(secret_key, giorno, regione),
		_da_firmare(quando, ambito, canonica).encode(),
		hashlib.sha256,
	).hexdigest()
	tutte["authorization"] = (
		f"{ALGORITMO} Credential={access_key}/{ambito}, SignedHeaders={firmate}, Signature={firma}"
	)
	tutte.pop("host")
	return tutte


def url_firmato(
	metodo: str,
	host: str,
	percorso: str,
	base: str,
	*,
	access_key: str,
	secret_key: str,
	regione: str,
	quando: datetime.datetime,
	scade: int = DURATA_DEL_LINK,
	parametri: dict | None = None,
) -> str:
	"""A link anybody holding it may follow until it expires: the signature in
	its query, only the host signed."""
	giorno = quando.strftime("%Y%m%d")
	ambito = f"{giorno}/{regione}/s3/aws4_request"
	tutti = dict(parametri or {})
	tutti.update(
		{
			"X-Amz-Algorithm": ALGORITMO,
			"X-Amz-Credential": f"{access_key}/{ambito}",
			"X-Amz-Date": quando.strftime("%Y%m%dT%H%M%SZ"),
			"X-Amz-Expires": str(int(scade)),
			"X-Amz-SignedHeaders": "host",
		}
	)
	canonica, _firmate = _richiesta_canonica(metodo, percorso, tutti, {"host": host}, NON_FIRMATO)
	firma = hmac.new(
		chiave_di_firma(secret_key, giorno, regione),
		_da_firmare(quando, ambito, canonica).encode(),
		hashlib.sha256,
	).hexdigest()
	return f"{base}{_codifica(percorso, barre=True)}?{_query(tutti)}&X-Amz-Signature={firma}"


# The space


def avviso(usato: int, incluso: int, soglia: float = 0.8) -> bool:
	"""Past this share of what is included, the page warns (the listino: at 80%)."""
	return bool(incluso) and usato >= soglia * incluso


def regole_cors(origini: list[str] | tuple[str, ...] = ("*",)) -> str:
	"""The bucket's CORS: a browser that followed a link to it may read the
	answer (a text file's preview fetches it). Only GET and HEAD: nothing is
	written to the bucket from a browser."""
	righe = "".join(f"<AllowedOrigin>{o}</AllowedOrigin>" for o in origini)
	return (
		'<?xml version="1.0" encoding="UTF-8"?>'
		'<CORSConfiguration xmlns="http://s3.amazonaws.com/doc/2006-03-01/"><CORSRule>'
		f"{righe}<AllowedMethod>GET</AllowedMethod><AllowedMethod>HEAD</AllowedMethod>"
		"<AllowedHeader>*</AllowedHeader><MaxAgeSeconds>3600</MaxAgeSeconds>"
		"</CORSRule></CORSConfiguration>"
	)


VERSIONI = (
	'<?xml version="1.0" encoding="UTF-8"?>'
	'<VersioningConfiguration xmlns="http://s3.amazonaws.com/doc/2006-03-01/">'
	"<Status>Enabled</Status></VersioningConfiguration>"
)
