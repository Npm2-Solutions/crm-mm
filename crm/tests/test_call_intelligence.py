# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and Contributors
# See license.txt

from unittest.mock import patch

import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils import add_to_date, now_datetime

from crm.api import call_scripts, dialer
from crm.telephony import callbacks, transcription


class CallIntelligenceCase(IntegrationTestCase):
	def setUp(self):
		frappe.set_user("Administrator")
		self.configure_transcription()

	def tearDown(self):
		frappe.db.rollback()
		for attr in ("crm_transcription_settings", "crm_answering_settings", "crm_company_hours"):
			if hasattr(frappe.local, attr):
				delattr(frappe.local, attr)

	def configure_transcription(self, **values):
		doc = frappe.get_single("CRM Transcription Settings")
		doc.update(
			{
				"enabled": 1,
				"auto_transcribe": 1,
				"base_url": "https://stt.example.com/v1",
				"model": "whisper-1",
				"language": "it",
				"max_recording_mb": 25,
				"request_timeout": 300,
				"transcript_retention_days": 0,
				"recording_retention_days": 0,
				**values,
			}
		)
		doc.save()
		if hasattr(frappe.local, "crm_transcription_settings"):
			del frappe.local.crm_transcription_settings
		return doc

	def make_call(self, **values):
		log = frappe.get_doc(
			{
				"doctype": "CRM Call Log",
				"to": "+390210000000",
				"type": "Outgoing",
				"status": "Completed",
				"telephony_medium": "Twilio",
				**values,
			}
		)
		log.insert(ignore_permissions=True)
		return log

	def make_script(self, name="Sales call", steps=None, **values):
		return call_scripts.save_script(
			{
				"script_name": name,
				"enabled": 1,
				"steps": steps or [{"title": "Greet"}, {"title": "Qualify"}, {"title": "Close"}],
				**values,
			}
		)


# ---------------------------------------------------------------------------
# transcription
# ---------------------------------------------------------------------------


class TestTranscriptionQueueing(CallIntelligenceCase):
	def test_a_call_without_a_recording_is_never_queued(self):
		log = self.make_call()
		with patch("frappe.enqueue") as enqueued:
			self.assertFalse(transcription.request_transcription(log.name))
			enqueued.assert_not_called()

	def test_a_recording_is_queued_and_claimed(self):
		log = self.make_call(recording_url="https://example.com/r.mp3")
		with patch("frappe.enqueue") as enqueued:
			self.assertTrue(transcription.request_transcription(log.name))
			enqueued.assert_called_once()
		self.assertEqual(
			frappe.db.get_value("CRM Call Log", log.name, "transcription_status"), transcription.PENDING
		)

	def test_a_claimed_call_is_not_queued_twice(self):
		log = self.make_call(recording_url="https://example.com/r.mp3")
		with patch("frappe.enqueue"):
			transcription.request_transcription(log.name)
			# a second webhook for the same recording must not buy the same audio again
			self.assertFalse(transcription.request_transcription(log.name))

	def test_a_finished_call_is_only_redone_on_request(self):
		log = self.make_call(recording_url="https://example.com/r.mp3")
		frappe.db.set_value("CRM Call Log", log.name, "transcription_status", transcription.COMPLETED)
		with patch("frappe.enqueue"):
			self.assertFalse(transcription.request_transcription(log.name))
			self.assertTrue(transcription.request_transcription(log.name, force=True))

	def test_nothing_is_queued_while_the_service_is_off(self):
		self.configure_transcription(enabled=0, base_url="", model="")
		log = self.make_call(recording_url="https://example.com/r.mp3")
		with patch("frappe.enqueue") as enqueued:
			self.assertFalse(transcription.request_transcription(log.name))
			enqueued.assert_not_called()

	def test_a_half_filled_endpoint_counts_as_unconfigured(self):
		def config(**values):
			return frappe._dict({"enabled": 1, "base_url": "https://stt.example.com/v1", **values})

		self.assertTrue(transcription.is_enabled(config(model="whisper-1")))
		self.assertFalse(transcription.is_enabled(config(model="")))
		self.assertFalse(transcription.is_enabled(config(model="whisper-1", base_url="")))
		self.assertFalse(transcription.is_enabled(config(model="whisper-1", enabled=0)))


class TestTranscriptionJob(CallIntelligenceCase):
	def test_a_successful_run_stores_the_text(self):
		log = self.make_call(recording_url="https://example.com/r.mp3")
		with (
			patch("crm.integrations.api.download_recording", return_value=(b"audio", "audio/mpeg")),
			patch("crm.telephony.transcription._post_audio", return_value="Buongiorno, la richiamo io."),
		):
			text = transcription.transcribe_call(log.name)

		self.assertEqual(text, "Buongiorno, la richiamo io.")
		row = frappe.db.get_value(
			"CRM Call Log",
			log.name,
			["transcript", "transcription_status", "transcript_language", "transcribed_on"],
			as_dict=True,
		)
		self.assertEqual(row.transcript, "Buongiorno, la richiamo io.")
		self.assertEqual(row.transcription_status, transcription.COMPLETED)
		self.assertEqual(row.transcript_language, "it")
		self.assertTrue(row.transcribed_on)

	def test_a_provider_failure_lands_on_the_record(self):
		log = self.make_call(recording_url="https://example.com/r.mp3")
		with (
			patch("crm.integrations.api.download_recording", return_value=(b"audio", "audio/mpeg")),
			patch("crm.telephony.transcription._post_audio", side_effect=ValueError("model overloaded")),
		):
			# a failed transcription is still a call; the job must not raise
			self.assertIsNone(transcription.transcribe_call(log.name))

		row = frappe.db.get_value(
			"CRM Call Log", log.name, ["transcription_status", "transcription_error"], as_dict=True
		)
		self.assertEqual(row.transcription_status, transcription.FAILED)
		self.assertIn("model overloaded", row.transcription_error)

	def test_a_call_whose_recording_vanished_is_skipped_not_failed(self):
		log = self.make_call()
		self.assertIsNone(transcription.transcribe_call(log.name))
		self.assertEqual(
			frappe.db.get_value("CRM Call Log", log.name, "transcription_status"), transcription.SKIPPED
		)

	def test_the_filename_follows_the_audio_type(self):
		self.assertTrue(transcription._filename("CALL-1", "audio/wav").endswith(".wav"))
		self.assertTrue(transcription._filename("CALL-1", "audio/ogg; codecs=opus").endswith(".ogg"))
		# an unknown type still gets a name the provider will accept
		self.assertTrue(transcription._filename("CALL-1", "application/octet-stream").endswith(".mp3"))


class TestTranscriptionRetention(CallIntelligenceCase):
	def age(self, name, days):
		frappe.db.set_value(
			"CRM Call Log", name, "creation", add_to_date(now_datetime(), days=-days), update_modified=False
		)

	def test_old_transcripts_are_forgotten(self):
		self.configure_transcription(transcript_retention_days=30)
		old = self.make_call(recording_url="https://example.com/a.mp3")
		frappe.db.set_value("CRM Call Log", old.name, "transcript", "vecchia")
		self.age(old.name, 60)

		recent = self.make_call(recording_url="https://example.com/b.mp3")
		frappe.db.set_value("CRM Call Log", recent.name, "transcript", "recente")

		cleared = transcription.expire_transcripts()

		self.assertEqual(cleared["transcripts"], 1)
		self.assertIsNone(frappe.db.get_value("CRM Call Log", old.name, "transcript"))
		self.assertEqual(frappe.db.get_value("CRM Call Log", recent.name, "transcript"), "recente")

	def test_recording_links_are_forgotten_separately(self):
		self.configure_transcription(transcript_retention_days=0, recording_retention_days=10)
		old = self.make_call(recording_url="https://example.com/a.mp3")
		frappe.db.set_value("CRM Call Log", old.name, "transcript", "resta")
		self.age(old.name, 30)

		cleared = transcription.expire_transcripts()

		self.assertEqual(cleared["recordings"], 1)
		self.assertIsNone(frappe.db.get_value("CRM Call Log", old.name, "recording_url"))
		# retention of the two is configured apart, so the text survives the audio
		self.assertEqual(frappe.db.get_value("CRM Call Log", old.name, "transcript"), "resta")

	def test_zero_means_keep_everything(self):
		self.configure_transcription(transcript_retention_days=0, recording_retention_days=0)
		old = self.make_call(recording_url="https://example.com/a.mp3")
		frappe.db.set_value("CRM Call Log", old.name, "transcript", "per sempre")
		self.age(old.name, 3650)

		self.assertEqual(transcription.expire_transcripts(), {"transcripts": 0, "recordings": 0})
		self.assertEqual(frappe.db.get_value("CRM Call Log", old.name, "transcript"), "per sempre")


# ---------------------------------------------------------------------------
# call scripts
# ---------------------------------------------------------------------------


class TestCallScripts(CallIntelligenceCase):
	def test_a_script_round_trips_with_its_steps(self):
		script = self.make_script(description="Prima chiamata")
		self.assertEqual(script["script_name"], "Sales call")
		self.assertEqual([s["title"] for s in script["steps"]], ["Greet", "Qualify", "Close"])

	def test_a_script_needs_at_least_one_step(self):
		with self.assertRaises(frappe.ValidationError):
			call_scripts.save_script({"script_name": "Empty", "steps": []})

	def test_a_script_needs_a_name(self):
		with self.assertRaises(frappe.ValidationError):
			call_scripts.save_script({"script_name": "  ", "steps": [{"title": "Greet"}]})

	def test_blank_steps_are_dropped(self):
		script = self.make_script(steps=[{"title": "Greet"}, {"title": "   "}])
		self.assertEqual(len(script["steps"]), 1)

	def test_editing_replaces_the_steps_rather_than_appending(self):
		script = self.make_script()
		updated = call_scripts.save_script(
			{"script_name": "Sales call", "steps": [{"title": "Only one"}]}, name=script["name"]
		)
		self.assertEqual([s["title"] for s in updated["steps"]], ["Only one"])

	def test_disabled_scripts_stay_out_of_the_agent_list(self):
		self.make_script(name="Live")
		self.make_script(name="Retired", enabled=0)
		names = [s["script_name"] for s in call_scripts.list_scripts()]
		self.assertIn("Live", names)
		self.assertNotIn("Retired", names)
		self.assertIn("Retired", [s["script_name"] for s in call_scripts.list_scripts(include_disabled=True)])


# ---------------------------------------------------------------------------
# the script while the call is running
# ---------------------------------------------------------------------------


class TestScriptDuringCall(CallIntelligenceCase):
	def setUp(self):
		super().setUp()
		self.lead = frappe.get_doc(
			{
				"doctype": "CRM Lead",
				"first_name": "Marta",
				"lead_name": "Marta Bianchi",
				"mobile_no": "+393331234567",
			}
		).insert(ignore_permissions=True)
		self.script = self.make_script()
		self.session = dialer.create_session(doctype="CRM Lead", limit=5)
		self.idx = self.session["current"]["idx"]

	def steps_of(self, script):
		return frappe.get_all(
			"CRM Call Script Step",
			filters={"parenttype": "CRM Call Script", "parent": script["name"]},
			pluck="name",
			order_by="idx asc",
		)

	def test_a_script_can_be_attached_to_the_call_in_hand(self):
		payload = dialer.update_entry_script(self.session["name"], self.idx, script=self.script["name"])
		self.assertEqual(payload["current"]["script"], self.script["name"])

	def test_steps_are_ticked_and_remembered(self):
		dialer.update_entry_script(self.session["name"], self.idx, script=self.script["name"])
		first, second = self.steps_of(self.script)[:2]
		payload = dialer.update_entry_script(self.session["name"], self.idx, steps_done=[first, second])
		self.assertEqual(sorted(payload["current"]["steps_done"]), sorted([first, second]))

	def test_steps_from_another_script_are_refused(self):
		other = self.make_script(name="Other script")
		dialer.update_entry_script(self.session["name"], self.idx, script=self.script["name"])
		payload = dialer.update_entry_script(self.session["name"], self.idx, steps_done=self.steps_of(other))
		self.assertEqual(payload["current"]["steps_done"], [])

	def test_switching_script_clears_the_ticks(self):
		dialer.update_entry_script(self.session["name"], self.idx, script=self.script["name"])
		dialer.update_entry_script(self.session["name"], self.idx, steps_done=self.steps_of(self.script)[:1])
		other = self.make_script(name="Other script")
		payload = dialer.update_entry_script(self.session["name"], self.idx, script=other["name"])
		# ticks belong to the script they were made against
		self.assertEqual(payload["current"]["steps_done"], [])

	def test_clearing_the_script_is_not_the_same_as_leaving_it_alone(self):
		dialer.update_entry_script(self.session["name"], self.idx, script=self.script["name"])
		payload = dialer.update_entry_script(self.session["name"], self.idx, script="")
		self.assertIsNone(payload["current"]["script"])

	def test_an_unknown_script_is_refused(self):
		with self.assertRaises(frappe.ValidationError):
			dialer.update_entry_script(self.session["name"], self.idx, script="No Such Script")

	def test_the_outcome_note_records_how_far_the_script_got(self):
		dialer.update_entry_script(self.session["name"], self.idx, script=self.script["name"])
		dialer.update_entry_script(self.session["name"], self.idx, steps_done=self.steps_of(self.script)[:2])
		dialer.complete_entry(self.session["name"], self.idx, disposition="Interested")

		comment = frappe.get_all(
			"Comment",
			filters={"reference_doctype": "CRM Lead", "reference_name": self.lead.name},
			pluck="content",
			order_by="creation desc",
			limit=1,
		)
		self.assertTrue(comment)
		self.assertIn("2/3", comment[0])


# ---------------------------------------------------------------------------
# what the agent sees beside the call
# ---------------------------------------------------------------------------


class TestEntryContext(CallIntelligenceCase):
	def setUp(self):
		super().setUp()
		self.lead = frappe.get_doc(
			{
				"doctype": "CRM Lead",
				"first_name": "Giulio",
				"lead_name": "Giulio Rossi",
				"organization": "Studio Rossi",
				"mobile_no": "+393339876543",
				"email": "giulio@example.com",
			}
		).insert(ignore_permissions=True)
		self.session = dialer.create_session(doctype="CRM Lead", limit=5)
		self.idx = self.session["current"]["idx"]

	def test_the_record_behind_the_number_comes_back(self):
		context = dialer.get_entry_context(self.session["name"], self.idx)
		self.assertEqual(context["record"]["name"], self.lead.name)
		self.assertEqual(context["record"]["organization"], "Studio Rossi")
		self.assertEqual(context["record"]["doctype"], "CRM Lead")

	def test_the_available_scripts_come_in_the_same_round_trip(self):
		self.make_script()
		context = dialer.get_entry_context(self.session["name"], self.idx)
		self.assertEqual([s["script_name"] for s in context["scripts"]], ["Sales call"])

	def test_upcoming_appointments_are_listed(self):
		service = frappe.get_doc(
			{
				"doctype": "CRM Service",
				"service_name": "Consulenza",
				"duration": 30,
				"enabled": 1,
				"staff_selection": "Any one",
			}
		).insert(ignore_permissions=True)
		appointment = frappe.get_doc(
			{
				"doctype": "CRM Appointment",
				"service": service.name,
				"status": "Scheduled",
				"starts_on": add_to_date(now_datetime(), days=2),
				"ends_on": add_to_date(now_datetime(), days=2, minutes=30),
				"participants": [
					{
						"party_type": "CRM Lead",
						"party": self.lead.name,
						"participant_name": "Giulio Rossi",
					}
				],
			}
		).insert(ignore_permissions=True)

		context = dialer.get_entry_context(self.session["name"], self.idx)
		self.assertIn(appointment.name, [a["name"] for a in context["appointments"]])

	def test_a_callback_from_an_unknown_number_still_returns_a_context(self):
		log = self.make_call(type="Incoming", recording_url=None)
		setattr(log, "from", "+390000000000")
		log.save(ignore_permissions=True)
		callbacks.queue_callback(log)
		frappe.db.set_value("CRM Call Log", log.name, "callback_due", add_to_date(now_datetime(), hours=-1))
		dialer.end_session(self.session["name"], cancel=True)

		session = dialer.create_session(source="Callbacks")
		context = dialer.get_entry_context(session["name"], session["current"]["idx"])
		self.assertIsNone(context["record"])
		self.assertEqual(context["appointments"], [])
