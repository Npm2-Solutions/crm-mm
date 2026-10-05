# Copyright (c) 2026, NPM2 Solutions Srl and contributors
# For license information, please see license.txt

"""The exercises' pictures on a server, with nobody asking: the missing ones
fetched from the dataset at the library's commit, written whole, one run at a
time, the dataset out of reach stopping the run; the hourly look that starts it.
No network: the dataset answers through a fake session."""

from __future__ import annotations

import json
import os
import tempfile
import time
from pathlib import Path
from unittest.mock import patch

import frappe
import requests
from frappe.tests import UnitTestCase

from crm.piani import immagini as I
from crm.piani import librerie

VOCI = [
	{
		"id": f"000{n}",
		"name": f"exercise {n}",
		"body_part": "waist",
		"equipment": "body weight",
		"target": "abs",
		"image": f"images/000{n}-x.jpg",
		"gif_url": f"videos/000{n}-x.gif",
	}
	for n in range(1, 4)
]


class Risposta:
	def __init__(self, stato: int, contenuto: bytes):
		self.status_code = stato
		self.content = contenuto


def _risponde_sempre(indirizzo: str) -> Risposta:
	return Risposta(200, b"GIF89a" + indirizzo.encode())


class Dataset:
	"""The dataset as a session reaches it: what it was asked, and what it answers."""

	def __init__(self, risponde=None):
		self.chiesti: list[str] = []
		self.risponde = risponde or _risponde_sempre

	def get(self, indirizzo, timeout=None):
		self.chiesti.append(indirizzo)
		return self.risponde(indirizzo)


class LeImmaginiSulServer(UnitTestCase):
	def setUp(self):
		cartella = tempfile.TemporaryDirectory()
		self.addCleanup(cartella.cleanup)
		self.base = Path(cartella.name) / "assets" / I.CARTELLA
		libreria = Path(cartella.name) / "esercizi.json"
		libreria.write_text(json.dumps(VOCI))
		for patcher in (
			patch.object(I, "cartella", return_value=self.base),
			patch.object(librerie, "LIBRERIA", libreria),
		):
			patcher.start()
			self.addCleanup(patcher.stop)

	def test_quelle_che_mancano_dal_dataset_al_suo_commit(self):
		self.assertIsNone(I.indirizzo())
		self.assertEqual(len(I.mancanti()), 6)
		dataset = Dataset()
		fatti = I.scarica(dataset)
		self.assertEqual((fatti["downloaded"], fatti["failed"], fatti["stopped"]), (6, 0, False))
		self.assertIn(
			f"https://raw.githubusercontent.com/hasaneyldrm/exercises-dataset/{I.COMMIT}/images/0001-x.jpg",
			dataset.chiesti,
		)
		self.assertTrue((self.base / "videos" / "0003-x.gif").read_bytes().startswith(b"GIF89a"))
		# no file left half-way beside them
		self.assertEqual([f.name for f in self.base.rglob("*.parziale")], [])
		self.assertEqual(
			I.stato(), {"images": {"present": 3, "of": 3}, "animations": {"present": 3, "of": 3}}
		)
		self.assertEqual(I.indirizzo(), "/assets/crm-esercizi")
		# what is there is not fetched again
		di_nuovo = Dataset()
		self.assertEqual(I.scarica(di_nuovo)["downloaded"], 0)
		self.assertEqual(di_nuovo.chiesti, [])

	def test_una_risposta_vuota_o_sbagliata_non_scrive_niente(self):
		def risponde(indirizzo):
			if indirizzo.endswith("0001-x.jpg"):
				return Risposta(404, b"Not Found")
			if indirizzo.endswith("0002-x.jpg"):
				return Risposta(200, b"")
			return Risposta(200, b"GIF89a")

		fatti = I.scarica(Dataset(risponde))
		self.assertEqual((fatti["downloaded"], fatti["failed"]), (4, 2))
		self.assertFalse((self.base / "images" / "0001-x.jpg").exists())
		self.assertFalse((self.base / "images" / "0002-x.jpg").exists())
		self.assertEqual(sorted(I.mancanti()), ["images/0001-x.jpg", "images/0002-x.jpg"])

	def test_il_dataset_irraggiungibile_ferma_il_giro(self):
		def risponde(indirizzo):
			raise requests.ConnectionError("unreachable")

		dataset = Dataset(risponde)
		with patch.object(I, "DI_FILA", 2):
			fatti = I.scarica(dataset)
		self.assertEqual((fatti["downloaded"], fatti["failed"], fatti["stopped"]), (0, 2, True))
		self.assertEqual(len(dataset.chiesti), 2)

	def test_un_giro_alla_volta_sul_server(self):
		with I._da_solo() as mio:
			self.assertTrue(mio)
			dataset = Dataset()
			# another site's job, while this one fetches
			self.assertTrue(I.scarica(dataset)["busy"])
			self.assertEqual(dataset.chiesti, [])
		self.assertEqual(I.scarica(Dataset())["downloaded"], 6)

	def test_ogni_ora_si_guarda_se_ne_mancano(self):
		with patch.object(frappe, "enqueue") as accoda:
			I.assicura()
			accoda.assert_called_once()
			self.assertEqual(accoda.call_args.args[0], "crm.piani.immagini.scarica")
			self.assertEqual(accoda.call_args.kwargs["job_id"], I.LAVORO)
			# a run began a little while ago, on this site or another: none now
			accoda.reset_mock()
			self.base.mkdir(parents=True)
			(self.base / I.ULTIMO_GIRO).touch()
			I.assicura()
			accoda.assert_not_called()
			# an hour later, and every one of them there: none either
			prima = time.time() - I.GIRO - 60
			os.utime(self.base / I.ULTIMO_GIRO, (prima, prima))
			I.scarica(Dataset())
			os.utime(self.base / I.ULTIMO_GIRO, (prima, prima))
			I.assicura()
			accoda.assert_not_called()
