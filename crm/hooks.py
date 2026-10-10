app_name = "crm"
app_title = "DottorCloud"
app_publisher = "NPM2 Solutions Srl"
app_description = "Management software for medical centres"
app_email = ""
app_license = "AGPLv3"
app_icon_url = "/assets/crm/images/dottorcloud-icona.svg"
app_icon_title = "DottorCloud"
app_icon_route = "/crm"

# The product's brand - the vertical's - where the framework shows its own
# (`crm.marchio`). These are the fallbacks of a site not set up yet: the brand that
# is on writes the Website Settings (login page, desk, favicon, splash) and every
# web page takes its favicon and splash from it (`update_website_context`).
app_logo_url = "/assets/crm/images/dottorcloud-icona.svg"
website_context = {
	"favicon": "/assets/crm/images/favicon.png",
	"splash_image": "/assets/crm/images/dottorcloud-icona.svg",
}
update_website_context = ["crm.marchio.contesto"]
# the desk names the apps by their titles: the framework's is "Frappe Framework"
extend_bootinfo = ["crm.marchio.boot"]

# Apps
# ------------------

# required_apps = []
add_to_apps_screen = [
	{
		"name": "crm",
		"logo": "/assets/crm/images/dottorcloud-icona.svg",
		"title": "DottorCloud",
		"route": "/crm",
		"has_permission": "crm.api.check_app_permission",
	}
]

get_site_info = "crm.activation.get_site_info"

export_python_type_annotations = True
require_type_annotated_api_methods = True

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/crm/css/crm.css"
# app_include_js = "/assets/crm/js/crm.js"

# include js, css files in header of web template
# web_include_css = "/assets/crm/css/crm.css"
# web_include_js = "/assets/crm/js/crm.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "crm/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
doctype_js = {
	"CRM Lead": "public/js/domain_enrichment.js",
	"CRM Organization": "public/js/domain_enrichment.js",
	"CRM Deal": "public/js/domain_enrichment.js",
}
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
# "Role": "home_page"
# }

# Shipped website content: the privacy policy and terms of service the Meta
# apps point at. They are records, not templates, so they can be corrected from
# the Website UI — but a `bench migrate` re-imports them, so a lasting edit has
# to come back into this file.
fixtures = [
	{"dt": "Web Page", "filters": [["name", "in", ["privacy", "terms"]]]},
]

# the SPA's shells before the framework's web forms and dynamic Web Pages, whose
# cached lists answer None now and then while they are filled again (pagine_dell_app)
page_renderer = ["crm.pagine_dell_app.PaginaDellApp"]

website_route_rules = [
	{"from_route": "/crm/<path:app_path>", "to_route": "crm"},
	{"from_route": "/crm-form/<route>", "to_route": "crm_form"},
	{"from_route": "/book/<route>", "to_route": "book"},
	{"from_route": "/book", "to_route": "book_index"},
	# service self-booking; /prenota is the www page itself, /booking is its English alias
	{"from_route": "/booking", "to_route": "prenota"},
	# path-style links: /prenota/<servizio>, /prenota/p/<professionista>, /prenota/c/<categoria>
	{"from_route": "/prenota/<path:prenota_path>", "to_route": "prenota"},
	# hub-hosted WhatsApp Embedded Signup (one whitelisted domain for every site)
	{"from_route": "/whatsapp-connect", "to_route": "whatsapp_connect"},
	# forms to fill and sign at home, or on the desk's tablet: /modulo/<link>
	{"from_route": "/modulo/<token>", "to_route": "modulo"},
	# a document put online, opened with the code the centre gave: /documento/<link>;
	# the links sent when it was a report still open it
	{"from_route": "/documento/<token>", "to_route": "documento"},
	{"from_route": "/referto/<token>", "to_route": "documento"},
	# the client area: one page, its own app routes inside
	{"from_route": "/area/<path:app_path>", "to_route": "area"},
	# a place offered from a waiting list, confirmed or declined: /lista-attesa/<link>
	{"from_route": "/lista-attesa/<token>", "to_route": "lista_attesa"},
]

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# Jinja
# ----------

# add methods and filters to jinja environment
#
# These are what makes a CRM block work inside a Builder page: Builder passes every
# rendered page through `render_template`, so a block whose markup says
# `{{ crm_form_html(props.form) }}` gets a real, inline CRM form — same document, no
# iframe. Names are prefixed because the Jinja namespace is shared with every app.
jinja = {
	"methods": [
		"crm.api.site_render.crm_form_html",
		"crm.api.site_render.crm_booking_html",
		"crm.api.site_render.crm_contact_html",
		"crm.api.site_render.crm_site_head",
		# what every email wears: the brand and the centre's mark (templates/emails)
		"crm.posta.aspetto.contesto_email",
	],
}

# Setup wizard
# setup_wizard_requires = "assets/crm/js/setup_wizard.js"
# setup_wizard_stages = "crm.setup.setup_wizard.setup_wizard.get_setup_stages"
setup_wizard_complete = [
	# DottorCloud's own words in the language and country the wizard chose
	# (`crm.lingue`): the consents', the libraries' (the clinic's foods hooked on here)
	"crm.moduli.consensi.dopo_la_configurazione",
	"crm.piani.librerie.dopo_la_configurazione",
	# the qualifications' notes and points to check, both halves of the register
	"crm.invoicing.install.qualifiche_nella_lingua",
	"crm.tessera_sanitaria.install.qualifiche_nella_lingua",
	"crm.clinica.librerie.dopo_la_configurazione",
	# the clinic's ready sheets, drafts in the centre's language
	"crm.clinica.schede_pronte.in_seguito",
	"crm.demo.api.create_demo_data",
]
# The centre chose another language (Settings > The centre > General > Language &
# time): DottorCloud's own words follow it, in the background (`crm.lingue`) - the
# same as after the setup wizard, the demo aside
crm_lingua_del_centro = [
	"crm.lingue.euro_come_si_scrive",
	"crm.moduli.consensi.dopo_la_configurazione",
	"crm.piani.librerie.dopo_la_configurazione",
	"crm.invoicing.install.qualifiche_nella_lingua",
	"crm.tessera_sanitaria.install.qualifiche_nella_lingua",
	"crm.clinica.librerie.dopo_la_configurazione",
	"crm.clinica.schede_pronte.in_seguito",
]
# setup_wizard_test = "crm.setup.setup_wizard.test_setup_wizard.run_setup_wizard_test"

# Installation
# ------------

before_install = "crm.install.before_install"
after_install = [
	"crm.install.after_install",
	# Rome's clock, Italy's formats and the week from Monday from the first page,
	# not from the first migrate
	"crm.lingue.italia_dove_nessuno_ha_scelto",
	# Italian and English on, the framework's other languages off: a phone set in
	# Italian reads the public pages in Italian (the framework ships it off), one
	# set in German reads English or the centre's, never half in German
	"crm.lingue.solo_italiano_e_inglese",
	"crm.lingue.euro_come_si_scrive",
	# the foods DottorCloud ships, with their names in Italian: the clinic's, hooked on here
	"crm.clinica.librerie.carica_libreria",
	# the clinic's ready sheets, drafts of the centre's where the clinic is on
	"crm.clinica.schede_pronte.carica_schede",
	# nothing about the centre's use leaves for Frappe's servers
	"crm.telemetria.spegni",
]

# a migrate syncs the modules of this release, whatever map a worker left in the cache
before_migrate = [
	"crm.migrazione.mappa_dei_moduli",
	# the words this release writes into the site come from its own catalogue
	"crm.migrazione.il_catalogo_del_rilascio",
]

# Uninstallation
# ------------

before_uninstall = "crm.uninstall.before_uninstall"
# after_uninstall = "crm.uninstall.after_uninstall"

# Integration Setup
# ------------------
# To set up dependencies/integrations with other apps
# Name of the app being installed is passed as an argument

# before_app_install = "crm.utils.before_app_install"
# after_app_install = "crm.utils.after_app_install"

# Integration Cleanup
# -------------------
# To clean up dependencies/integrations with other apps
# Name of the app being uninstalled is passed as an argument

# before_app_uninstall = "crm.utils.before_app_uninstall"
# after_app_uninstall = "crm.utils.after_app_uninstall"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "crm.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# a link's search in words: a professional's qualification by its name, not its code
standard_queries = {
	"CRM Service Provider": "crm.invoicing.ricerche.professionisti",
}

permission_query_conditions = {
	"CRM Lead": "crm.permissions.org_hierarchy.get_lead_permission_query_conditions",
	"CRM Deal": "crm.permissions.org_hierarchy.get_deal_permission_query_conditions",
	# calls, notes and tasks follow the lead or deal they are about
	"CRM Call Log": "crm.permissions.org_hierarchy.get_call_log_permission_query_conditions",
	"FCRM Note": "crm.permissions.org_hierarchy.get_note_permission_query_conditions",
	"CRM Task": "crm.permissions.org_hierarchy.get_task_permission_query_conditions",
	"CRM Notification": "crm.fcrm.doctype.crm_notification.crm_notification.get_permission_query_conditions",
	"CRM Dashboard": "crm.fcrm.doctype.crm_dashboard.crm_dashboard.get_permission_query_conditions",
	# the practitioner reads the invoices of their own services
	"CRM Invoice": "crm.invoicing.permessi.get_permission_query_conditions",
	# a person's billing details follow the person
	"CRM Billing Profile": "crm.invoicing.permessi.get_profile_permission_query_conditions",
	# and so do their consents
	"CRM Consent": "crm.moduli.consensi.get_permission_query_conditions",
	"CRM Form": "crm.moduli.compilazioni.get_permission_query_conditions",
	"CRM Form Request": "crm.moduli.richieste.get_permission_query_conditions",
	# and the people they are linked to, from either side
	"CRM Related Person": "crm.persone.collegate.get_permission_query_conditions",
	# and what they paid online
	"CRM Online Payment": "crm.pagamenti.pagamenti.get_permission_query_conditions",
	"CRM Stripe Customer": "crm.pagamenti.pagamenti.get_customer_permission_query_conditions",
	# and the funds and conventions that cover them
	"CRM Convention Cover": "crm.convenzioni.api.get_cover_permission_query_conditions",
	# the clinical record: its author, the medical director, the dossier
	"Clinic Record": "crm.clinica.cartella.get_permission_query_conditions",
	"Clinic Summary Value": "crm.clinica.sintesi.get_permission_query_conditions",
	"Clinic Dental Chart": "crm.clinica.cure.get_chart_permission_query_conditions",
	# plans and programmes: their author, whoever reads the person's plans; with
	# health data, the dossier
	"CRM Personal Plan": "crm.piani.api.get_permission_query_conditions",
	# a person's documents: whom it is for, who added it, who reads their documents;
	# with health data, the dossier
	"CRM Document": "crm.documenti.api.get_permission_query_conditions",
	# quotes: their author; proposed, who reads the person's quotes and who handles
	# them; with health data, the dossier
	"CRM Quote": "crm.preventivi.api.get_permission_query_conditions",
	"CRM Programme": "crm.piani.programmi.get_permission_query_conditions",
	# the agenda, the messages, the tracking and the old bookings follow the person
	"CRM Appointment": "crm.permissions.seguono.get_appointment_permission_query_conditions",
	"CRM Session Cycle": "crm.permissions.seguono.get_cycle_permission_query_conditions",
	"CRM Waiting List Entry": "crm.permissions.seguono.get_waiting_permission_query_conditions",
	"CRM Subscription": "crm.permissions.seguono.get_subscription_permission_query_conditions",
	"WhatsApp Message": "crm.permissions.seguono.get_whatsapp_permission_query_conditions",
	"CRM SMS Message": "crm.permissions.seguono.get_sms_permission_query_conditions",
	"CRM Visitor": "crm.permissions.seguono.get_visitor_permission_query_conditions",
	"CRM Tracking Event": "crm.permissions.seguono.get_tracking_event_permission_query_conditions",
	"CRM Booking": "crm.permissions.seguono.get_booking_permission_query_conditions",
	# emails to whoever converses; the address book not to whoever sees people masked
	"Communication": "crm.permissions.seguono.get_communication_permission_query_conditions",
	"Contact": "crm.permissions.seguono.get_contact_permission_query_conditions",
}

has_permission = {
	"CRM Lead": "crm.permissions.org_hierarchy.has_lead_permission",
	"CRM Deal": "crm.permissions.org_hierarchy.has_deal_permission",
	"CRM Organization": "crm.permissions.org_hierarchy.has_organization_permission",
	"CRM Call Log": "crm.permissions.org_hierarchy.has_call_log_permission",
	"FCRM Note": "crm.permissions.org_hierarchy.has_note_permission",
	"CRM Task": "crm.permissions.org_hierarchy.has_task_permission",
	"CRM Notification": "crm.fcrm.doctype.crm_notification.crm_notification.has_permission",
	"CRM Dashboard": "crm.fcrm.doctype.crm_dashboard.crm_dashboard.has_permission",
	"CRM Invoice": "crm.invoicing.permessi.has_permission",
	"CRM Billing Profile": "crm.invoicing.permessi.has_profile_permission",
	"CRM Consent": "crm.moduli.consensi.has_permission",
	"CRM Form": "crm.moduli.compilazioni.has_permission",
	"CRM Form Request": "crm.moduli.richieste.has_permission",
	"CRM Related Person": "crm.persone.collegate.has_permission",
	"CRM Online Payment": "crm.pagamenti.pagamenti.has_permission",
	"CRM Stripe Customer": "crm.pagamenti.pagamenti.has_permission",
	"CRM Convention Cover": "crm.convenzioni.api.has_cover_permission",
	"Clinic Record": "crm.clinica.cartella.has_permission",
	"Clinic Summary Value": "crm.clinica.sintesi.has_permission",
	"CRM Personal Plan": "crm.piani.api.has_permission",
	"CRM Document": "crm.documenti.api.has_permission",
	"CRM Quote": "crm.preventivi.api.has_permission",
	"CRM Programme": "crm.piani.programmi.has_permission",
	"Clinic Dental Chart": "crm.clinica.cure.has_chart_permission",
	"CRM Appointment": "crm.permissions.seguono.has_appointment_permission",
	"CRM Session Cycle": "crm.permissions.seguono.has_cycle_permission",
	"CRM Waiting List Entry": "crm.permissions.seguono.has_waiting_permission",
	"CRM Subscription": "crm.permissions.seguono.has_subscription_permission",
	"WhatsApp Message": "crm.permissions.seguono.has_whatsapp_permission",
	"CRM SMS Message": "crm.permissions.seguono.has_sms_permission",
	"CRM Visitor": "crm.permissions.seguono.has_visitor_permission",
	"CRM Tracking Event": "crm.permissions.seguono.has_tracking_event_permission",
	"CRM Booking": "crm.permissions.seguono.has_booking_permission",
	"Communication": "crm.permissions.seguono.has_communication_permission",
	"Contact": "crm.permissions.seguono.has_contact_permission",
	# Read only takes every write away, whatever the document
	"*": "crm.permissions.documenti.sola_lettura",
	# what the screens keep for the manager is written with a capability, not a role
	"CRM Service": "crm.permissions.documenti.has_permission",
	"CRM Service Price": "crm.permissions.documenti.has_permission",
	"CRM Price List": "crm.permissions.documenti.has_permission",
	"CRM Scheduling Settings": "crm.permissions.documenti.has_permission",
	"CRM Waiting List Settings": "crm.permissions.documenti.has_permission",
	"CRM Reminder Settings": "crm.permissions.documenti.has_permission",
	"CRM Subscription Type": "crm.permissions.documenti.has_permission",
	"CRM Convention": "crm.permissions.documenti.has_permission",
	"CRM Holiday List": "crm.permissions.documenti.has_permission",
	"CRM Staff Schedule": "crm.permissions.documenti.has_permission",
	"CRM Resource": "crm.permissions.documenti.has_permission",
	"CRM Location": "crm.permissions.documenti.has_permission",
	"CRM Booking Calendar": "crm.permissions.documenti.has_permission",
	"CRM Lead Status": "crm.permissions.documenti.has_permission",
	"CRM Deal Status": "crm.permissions.documenti.has_permission",
	"CRM Communication Status": "crm.permissions.documenti.has_permission",
	"CRM Client Settings": "crm.permissions.documenti.has_permission",
	"CRM Quote Settings": "crm.permissions.documenti.has_permission",
	"CRM Review Settings": "crm.permissions.documenti.has_permission",
	"CRM View Settings": "crm.permissions.documenti.has_permission",
	"WhatsApp Templates": "crm.permissions.documenti.has_permission",
	"WhatsApp Settings": "crm.permissions.documenti.has_permission",
	"CRM Telephony Agent": "crm.permissions.documenti.has_permission",
	"CRM Caller ID": "crm.permissions.documenti.has_permission",
	"CRM Phone Number Request": "crm.permissions.documenti.has_permission",
	"CRM Sales Hierarchy": "crm.permissions.documenti.has_permission",
	"CRM Service Level Agreement": "crm.permissions.documenti.has_permission",
	"Email Template": "crm.permissions.documenti.has_permission",
	"Assignment Rule": "crm.permissions.documenti.has_permission",
	"Data Import": "crm.permissions.documenti.has_permission",
}

# DocType Class
# ---------------
# Override standard doctype classes

# nosemgrep: override-doctype-class — each override subclasses the framework's class and calls super(): list data, a mailbox's mails, the demo's guard, an archived file brought back before it is read
override_doctype_class = {
	"Contact": "crm.overrides.contact.CustomContact",
	"Email Template": "crm.overrides.email_template.CustomEmailTemplate",
	# somebody's own mailbox brings only the centre's emails (crm.posta.personale)
	"Email Account": "crm.overrides.email_account.CasellaDiDottorCloud",
	# a person of the demo data is never written to (crm.demo.guardie); only where
	# the WhatsApp app is, as the doctype is
	"WhatsApp Message": "crm.demo.whatsapp.MessaggioWhatsApp",
	# a private file on the agency's archive is brought back before it is read (crm.archivio)
	"File": "crm.overrides.file.FileDiDottorCloud",
}

# Document Events
# ---------------
# Hook on document methods and events

doc_events = {
	# Read only writes nothing, not even what is shared with it for writing
	"*": {
		"validate": ["crm.permissions.documenti.sola_lettura_al_salvataggio"],
		# while the demo data are made, every record is written down (crm.demo)
		"after_insert": ["crm.demo.registro.annota"],
	},
	# an email to a person of the demo data is never sent (crm.demo.guardie)
	"Email Queue": {
		"before_insert": ["crm.demo.guardie.posta_in_coda"],
	},
	# conditions written in Python are the agency's: the server writes the others
	# from the guided conditions, before anything evaluates them
	"Assignment Rule": {
		"before_validate": "crm.permissions.documenti.scrivi_condizioni",
	},
	"CRM Service Level Agreement": {
		"before_validate": "crm.permissions.documenti.scrivi_condizioni",
	},
	# The healthcare rules on a qualification belong to the module that can explain
	# them, not to a DocType that also serves lawyers and engineers.
	"CRM Professional Qualification": {
		"validate": "crm.tessera_sanitaria.qualifica.valida",
	},
	"CRM Billable Service": {
		"validate": "crm.tessera_sanitaria.qualifica.valida_servizio",
	},
	"CRM Invoicing Company": {
		"validate": "crm.tessera_sanitaria.qualifica.valida_azienda",
	},
	"Contact": {
		"validate": [
			"crm.api.contact.validate",
			"crm.permissions.org_hierarchy.scrittura_per_capacita",
		],
		# created by a webhook, a form, a booking: nobody was logged in, and
		# «Guest created this contact» reads like somebody got in from outside
		"before_insert": ["crm.utils.ownership.credit_the_system"],
	},
	"Notification Log": {
		"before_insert": ["crm.extends.notification_log.before_insert"],
	},
	"ToDo": {
		"validate": ["crm.api.todo.validate"],
		"after_insert": ["crm.api.todo.after_insert"],
		"on_update": ["crm.api.todo.on_update"],
	},
	"Communication": {
		"after_insert": [
			"crm.utils.on_communication_insert",
			"crm.automation.engine.on_communication_insert",
			"crm.booking_platforms.sync.on_communication",
			"crm.api.conversations.on_communication",
		],
		"on_update": [
			"crm.utils.on_communication_update",
			"crm.automation.engine.on_communication_update",
			# an email is linked to its record after it is written, so the
			# conversation only knows whose it is on the update
			"crm.api.conversations.on_communication",
		],
	},
	"Tag Link": {
		"after_insert": ["crm.automation.engine.on_tag_added"],
		"on_trash": ["crm.automation.engine.on_tag_removed"],
	},
	"CRM Call Log": {
		"on_update": ["crm.telephony.transcription.on_call_log_update"],
	},
	"CRM Task": {
		"on_update": ["crm.automation.engine.on_task_updated"],
	},
	"FCRM Note": {
		"validate": ["crm.permissions.org_hierarchy.scrittura_per_capacita"],
		"after_insert": ["crm.automation.engine.on_note_created"],
	},
	"Comment": {
		"after_insert": ["crm.utils.on_comment_insert"],
		"on_update": ["crm.api.comment.on_update"],
	},
	# A number is taken out of the CRM from Settings, which switches it off and
	# keeps its chat history. Deleting the row is the other way, and it is closed.
	"WhatsApp Account": {
		"on_trash": ["crm.integrations.whatsapp.api.refuse_account_deletion"],
	},
	"WhatsApp Message": {
		"validate": ["crm.api.whatsapp.validate"],
		"on_update": ["crm.api.whatsapp.on_update"],
		"after_insert": [
			"crm.automation.engine.on_whatsapp_received",
			"crm.api.conversations.on_message",
			# a reminder's button tapped: confirmed, cannot come, would like to move it
			"crm.scheduling.promemoria.alla_risposta_whatsapp",
		],
	},
	"CRM SMS Message": {
		"after_insert": ["crm.api.conversations.on_message"],
	},
	"CRM Lead": {
		# a person or a deal is shared with its owner for writing: the save asks
		# for the capability all the same
		"validate": ["crm.permissions.org_hierarchy.scrittura_per_capacita"],
		"before_insert": [
			"crm.api.tracking.stamp_manual_source",
			"crm.utils.ownership.credit_the_system",
		],
		"after_insert": [
			"crm.api.tracking.bind_visitor",
			"crm.automation.engine.on_lead_created",
			"crm.integrations.meta.conversions.on_lead_created",
		],
		"on_update": [
			"crm.api.mirror.on_lead_updated",
			"crm.integrations.meta.conversions.on_lead_updated",
		],
		"on_trash": [
			# a patient's record is kept: said before anything else is removed
			"crm.clinica.eventi.persona_in_cancellazione",
			"crm.integrations.meta.leads.forget_person",
			# billing details, consents and links are part of the person, not linked to it
			"crm.invoicing.anagrafica.cancella_con_il_titolare",
			"crm.moduli.consensi.cancella_con_la_persona",
			"crm.persone.collegate.cancella_con_la_persona",
			# and the conventions that cover them
			"crm.convenzioni.convenzioni.cancella_con_la_persona",
			# and what they waited for
			"crm.scheduling.attese.cancella_con_la_persona",
			# and their way through the automations
			"crm.automation.engine.cancella_con_il_riferimento",
			# and the review requests they were sent
			"crm.recensioni.chiedi.cancella_con_la_persona",
			# and what they paid online
			"crm.pagamenti.pagamenti.cancella_con_la_persona",
		],
	},
	"CRM Organization": {
		"validate": ["crm.permissions.org_hierarchy.scrittura_per_capacita"],
		"on_update": ["crm.api.mirror.on_organization_updated"],
		"on_trash": ["crm.invoicing.anagrafica.cancella_con_il_titolare"],
	},
	"CRM Deal": {
		"validate": ["crm.permissions.org_hierarchy.scrittura_per_capacita"],
		"before_insert": [
			"crm.api.tracking.stamp_manual_source",
			"crm.utils.ownership.credit_the_system",
		],
		"on_update": [
			"crm.automation.engine.on_deal_updated",
			"crm.integrations.meta.conversions.on_deal_updated",
		],
		"after_insert": ["crm.api.tracking.bind_visitor", "crm.automation.engine.on_deal_created"],
		"on_trash": ["crm.automation.engine.cancella_con_il_riferimento"],
	},
	"CRM Booking": {
		"after_insert": ["crm.automation.engine.on_booking_created"],
		"on_update": ["crm.automation.engine.on_booking_updated"],
	},
	"CRM Appointment": {
		# a service of an accepted quote: taken, at the price agreed
		"validate": [
			"crm.preventivi.appuntamenti.in_validazione",
			# under a convention, the person's share and the fund's of the final price
			"crm.convenzioni.convenzioni.quote_dell_appuntamento",
		],
		"after_insert": [
			"crm.automation.engine.on_appointment_created",
			# a booking moves the new clients deal
			"crm.clienti.eventi.appuntamento_creato",
			# and sends the link to the forms the person owes for it
			"crm.moduli.dovuti.appuntamento_prenotato",
			"crm.preventivi.appuntamenti.creato",
		],
		"on_update": [
			"crm.automation.engine.on_appointment_updated",
			"crm.booking_platforms.sync.on_appointment_change",
			# who came becomes a client; where the clinic is on, a patient
			"crm.clienti.eventi.appuntamento_aggiornato",
			"crm.clinica.eventi.appuntamento_aggiornato",
			# and the service of their quote is done
			"crm.preventivi.appuntamenti.aggiornato",
			# cancelled, moved, a seat freed: offered to who waits
			"crm.scheduling.attese.appuntamento_aggiornato",
			# cancelled in time: the deposit paid online goes back
			"crm.pagamenti.pagamenti.alla_disdetta",
		],
		"on_trash": [
			"crm.booking_platforms.sync.on_appointment_change",
			"crm.preventivi.appuntamenti.eliminato",
			# the waiting lists let go of it, and its time goes to who waits once it is gone
			"crm.scheduling.attese.appuntamento_in_eliminazione",
		],
		"after_delete": ["crm.scheduling.attese.appuntamento_eliminato"],
	},
	# a new shift, a service or a room changed: the waiting lists are looked at again
	"CRM Staff Schedule": {
		"on_update": [
			"crm.scheduling.attese.orari_cambiati",
			# shifts given a location: the appointments ahead that named none are there (doc 62)
			"crm.scheduling.sedi.turni_aggiornati",
		]
	},
	"CRM Service": {"on_update": ["crm.scheduling.attese.orari_cambiati"]},
	"CRM Resource": {
		"on_update": [
			"crm.scheduling.attese.orari_cambiati",
			# a room given a location: its appointments that named none are there (doc 62)
			"crm.scheduling.sedi.stanza_aggiornata",
		]
	},
	"CRM Scheduling Settings": {"on_update": ["crm.scheduling.attese.orari_cambiati"]},
	# new clients and the clinic listen to invoicing; invoicing hears of neither
	"CRM Invoice": {
		# a fund's invoice thrown away or cancelled: its pratiche are to bill again
		# and a quote's instalments it was for are to pay again (crm.preventivi.rate)
		"on_trash": ["crm.convenzioni.convenzioni.fattura_tolta", "crm.preventivi.rate.allinea"],
		"on_cancel": ["crm.convenzioni.convenzioni.fattura_tolta", "crm.preventivi.rate.allinea"],
		"on_submit": [
			# a quote's instalments it is for are invoiced
			"crm.preventivi.rate.allinea",
			# issued from an appointment: the person came
			"crm.scheduling.esiti.fattura_emessa",
			"crm.clienti.eventi.fattura_confermata",
			"crm.clinica.eventi.fattura_confermata",
			# where the centre wants it, the person hears of it with a link to the area
			"crm.area.collegamento.fattura_emessa",
		],
	},
	"CRM Plan": {
		"on_update": [
			# a vertical switched on or off changes the brand of the framework's pages
			"crm.marchio.piano_aggiornato",
			"crm.clinica.eventi.piano_aggiornato",
		],
	},
	# rule 1 of becoming a patient: a signed form with health data
	"CRM Form": {
		"on_submit": ["crm.clinica.eventi.modulo_firmato"],
	},
	# and a message about the care on the board of the area
	"CRM Area Message": {
		"after_insert": ["crm.clinica.eventi.messaggio_scritto"],
		"on_trash": ["crm.clinica.eventi.messaggio_eliminato"],
	},
	# and what carries health data among a person's plans, programmes and documents:
	# a diet, exercises at home, a test result
	"CRM Personal Plan": {
		"after_insert": ["crm.clinica.eventi.sanitario_scritto"],
		"on_trash": ["crm.clinica.eventi.sanitario_eliminato"],
	},
	"CRM Programme": {
		"after_insert": ["crm.clinica.eventi.sanitario_scritto"],
		"on_trash": ["crm.clinica.eventi.sanitario_eliminato"],
	},
	"CRM Document": {
		"validate": ["crm.clinica.documenti.valida"],
		"after_insert": ["crm.clinica.eventi.sanitario_scritto"],
		"on_trash": ["crm.clinica.eventi.sanitario_eliminato"],
	},
	"CRM Quote": {
		"after_insert": ["crm.clinica.eventi.sanitario_scritto"],
		"on_trash": ["crm.clinica.eventi.sanitario_eliminato"],
	},
	"Log Settings": {
		"validate": ["crm.clinica.cartella.valida_impostazioni_log"],
	},
	# a file attached to the clinical record or to a person's document is private,
	# whatever the upload asked
	"File": {
		"before_insert": ["crm.clinica.cartella.allegato_privato", "crm.documenti.api.allegato_privato"],
		# the last File of an address gone, its object leaves the archive (crm.archivio)
		"on_trash": ["crm.archivio.archivio.al_cestino"],
	},
	"User": {
		"before_validate": ["crm.api.live_demo.validate_user"],
		# outside the levels, the roles imply one: it sees email and phone like it
		"validate": ["crm.permissions.utenti.recapiti_fuori_dai_livelli"],
		"validate_reset_password": ["crm.api.live_demo.validate_reset_password"],
	},
	# Frappe checks that two pages don't share a route, but knows nothing about /crm,
	# /book or /crm-form. Without this a page could be published straight over the app.
	"Builder Page": {
		"validate": [
			"crm.api.site_routes.guard_builder_route",
			"crm.api.site_routes.guard_home_page",
		],
		"on_trash": ["crm.api.site_routes.guard_home_page"],
	},
}

# Scheduled Tasks
# ---------------

# a notification older than six months goes, read or not (Log Settings, crm.notifiche)
default_log_clearing_doctypes = {"CRM Notification": 180}

# the framework's emails for an assignment, a mention, a document shared: they named
# doctypes and IDs and opened the Desk. DottorCloud's notifications go by email in
# its words instead (crm.notifiche.posta)
notification_skip_email_types = ["Assignment", "Mention", "Share"]

# an email leaving through the agency's sending service comes from the centre, and its
# answers go to the centre (crm.posta.servizio)
make_email_body_message = ["crm.posta.servizio.intestazioni"]

scheduler_events = {
	"all": ["crm.api.event.trigger_offset_event_notifications"],
	"hourly": [
		"crm.api.event.trigger_hourly_event_notifications",
		"crm.integrations.meta.conversions.flush",
		# a conversation parked until this morning has to come back on its own,
		# or «rimanda a domani» would be «nascondi per sempre»
		"crm.api.conversations.wake_the_snoozed",
		# once the day's last appointment ended: "did they come?"
		"crm.scheduling.esiti.fine_giornata",
		# the agency's sending service, as its configuration says now
		"crm.posta.servizio.assicura",
		# DottorCloud's space in the centre's Twilio account: the app and the numbers
		# as somebody may have changed them in the console
		"crm.telephony.collegamento.assicura",
		# what Twilio decided of the documents of a new number
		"crm.telephony.numeri.aggiorna_le_richieste",
		# the exercises' pictures on this server, the missing ones fetched by themselves
		"crm.piani.immagini.assicura",
		# a centre that invoices with Fatture in Cloud: its access renewed before it ends
		"crm.invoicing.fic.collegamento.rinnova_i_token",
	],
	"daily": [
		"crm.integrations.meta.leads.check_token_health",
		"crm.integrations.meta.insights.sync_ad_spend",
		"crm.api.event.trigger_daily_event_notifications",
		"crm.fcrm.doctype.crm_invitation.crm_invitation.expire_invitations",
		# the centre's archive holds everything: it goes after a week
		"crm.esportazione.esporta.togli_le_vecchie",
		"crm.fcrm.doctype.crm_view_settings.crm_view_settings.clear_old_versions",
		"crm.api.tracking.purge_old_data",
		"crm.telephony.transcription.expire_transcripts",
		# Invoicing fails quietly and annually: an expired Sistema TS certificate,
		# a button nobody pressed. The sweep looks for absence, not for errors.
		"crm.invoicing.monitoraggio.giornaliero",
		"crm.tessera_sanitaria.monitoraggio.giornaliero",
		# a programme's stage whose day has come opens, and its plan with it
		"crm.piani.programmi.apri_del_giorno",
		# subscriptions: how each stands, the instalments due, the end, the renewals
		"crm.scheduling.abbonamenti.ogni_giorno",
		# the quotes' instalments due get their invoices
		"crm.preventivi.rate.ogni_giorno",
		# where the centre switched them on, the reminders of what a person still owes
		"crm.invoicing.solleciti.ogni_giorno",
	],
	"weekly": ["crm.api.event.trigger_weekly_event_notifications"],
	"hourly_long": [
		"crm.integrations.meta.leads.reconcile_synced_pages",
		# the private files written a while ago, to the agency's archive (crm.archivio)
		"crm.archivio.archivio.sposta",
	],
	"daily_long": [
		# what a deletion by the database left in the archive
		"crm.archivio.archivio.orfani",
		# where the centre switched it on, the night's reports to the Sistema TS: one
		# synchronous call per expense, so the long queue
		"crm.tessera_sanitaria.automatico.ogni_notte",
	],
	"cron": {
		"* * * * *": ["crm.automation.engine.process_due_enrollments"],
		"*/10 * * * *": [
			# while the webhook is silent (an app in Development mode never gets one)
			# this is the only way a lead reaches anybody, and an hour of waiting is
			# most of a lead's value. It stands down on its own once Meta calls.
			"crm.integrations.meta.leads.catch_up_recent_leads",
			# an offer nobody answered goes to the next one waiting; the whole list hourly
			"crm.scheduling.attese.ogni_dieci_minuti",
			# the SdI's outcomes from Itala: one account for every centre has no
			# webhook to call each site, so each site asks, and only when it waits
			"crm.invoicing.monitoraggio.riconcilia_provider",
			# the same, for the invoices that left from Fatture in Cloud
			"crm.invoicing.fic.emissione.riconcilia",
			# an online payment's link nobody paid in time: a deposit's place freed
			"crm.pagamenti.pagamenti.ogni_dieci_minuti",
		],
		"*/2 * * * *": ["crm.social.publisher.process_due_posts"],
		# what is still unread in the panel after a few minutes, by email to who wants it
		"*/5 * * * *": ["crm.notifiche.posta.manda_le_email"],
		# bookings taken on MioDottore, SimplyBook, Cal.com… and calendar feeds
		"*/15 * * * *": [
			"crm.booking_platforms.sync.sync_all",
			# the reminders of the appointments, the day before (docs/crm/59)
			"crm.scheduling.promemoria.ogni_quarto_d_ora",
		],
	},
}

# Testing
# -------

before_tests = "crm.tests.before_tests"

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
# "frappe.desk.doctype.event.event.get_events": "crm.event.get_events"
# }
# Assigning a person or a deal asks for the capability (doc 30)
override_whitelisted_methods = {
	"frappe.desk.form.assign_to.add": "crm.permissions.documenti.assegna",
	"frappe.desk.form.assign_to.add_multiple": "crm.permissions.documenti.assegna_a_molti",
	"frappe.desk.form.assign_to.remove": "crm.permissions.documenti.togli_assegnazione",
	"frappe.desk.form.assign_to.remove_multiple": "crm.permissions.documenti.togli_assegnazioni",
}
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# "Task": "crm.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Ignore links to specified DocTypes when deleting documents
# -----------------------------------------------------------

# the audit log outlives what it records: a document taken away keeps its events
ignore_links_on_delete = [
	"Failed Lead Sync Log",
	"CRM Audit Log",
	"CRM Review Request",
	# a payment stays in the register when its appointment is deleted
	"CRM Online Payment",
	"CRM Stripe Event",
]

# Request Events
# ----------------
# before_request = ["crm.utils.before_request"]
# after_request = ["crm.utils.after_request"]

# Job Events
# ----------
# before_job = ["crm.utils.before_job"]
# after_job = ["crm.utils.after_job"]

# User Data Protection
# --------------------

# user_data_fields = [
# {
# "doctype": "{doctype_1}",
# "filter_by": "{filter_by}",
# "redact_fields": ["{field_1}", "{field_2}"],
# "partial": 1,
# },
# {
# "doctype": "{doctype_2}",
# "filter_by": "{filter_by}",
# "partial": 1,
# },
# {
# "doctype": "{doctype_3}",
# "strict": False,
# },
# {
# "doctype": "{doctype_4}"
# }
# ]

# Authentication and authorization
# --------------------------------

# auth_hooks = [
# "crm.auth.validate"
# ]

after_migrate = [
	"crm.fcrm.doctype.fcrm_settings.fcrm_settings.after_migrate",
	# nothing about the centre's use leaves for Frappe's servers, whatever a host turned on
	"crm.telemetria.spegni",
	# the levels' Role Profiles follow the registry, which is code
	"crm.permissions.utenti.sincronizza",
	"crm.api.whatsapp.add_roles",
	"crm.domain_enrichment.install.seed_default_rules_and_mappings",
	"crm.install.add_default_scripts",
	"crm.install.add_builder_page_custom_fields",
	# the kinds of consent the modules registered, never overwriting the centre's text
	"crm.moduli.consensi.assicura_tipi",
	# the shipped qualifications' words follow the centre's language, its own stay
	"crm.invoicing.install.qualifiche_nella_lingua",
	"crm.tessera_sanitaria.install.qualifiche_nella_lingua",
	# the access logs of the clinical record are kept two years at least
	"crm.clinica.cartella.proteggi_registro_accessi",
	# the core documents the Manager's pages write: templates, rules, imports
	"crm.permissions.documenti.concedi_documenti_del_core",
	# the exercise and food libraries DottorCloud ships, when their file is a new one
	"crm.piani.librerie.carica_libreria",
	"crm.clinica.librerie.carica_libreria",
	# the clinic's ready sheets, when their file or the centre's language is a new one
	"crm.clinica.schede_pronte.carica_schede",
	# whose own mailbox an account is (doc 51)
	"crm.install.add_email_account_custom_field",
	# DottorCloud's own emails leave through the agency's sending service
	"crm.posta.servizio.assicura",
	# a site nobody set up reads as a centre in Italy: Rome's clock, its formats
	"crm.lingue.italia_dove_nessuno_ha_scelto",
	# Italian and English on, the framework's other languages off, the centre's
	# read by whoever has not chosen their own
	"crm.lingue.solo_italiano_e_inglese",
	# the euro after the amount in Italian («60,00 €»), before it in English
	"crm.lingue.euro_come_si_scrive",
]

# Rows other modules add to a record's history (`crm.api.activities`)
crm_timeline_gatherers = [
	# a padlock for each visit, for who may know of it
	"crm.clinica.cartella.visite_su",
]

# The people a practitioner looks after beyond their appointments
# (`crm.permissions.org_hierarchy`): a subquery of leads, or None
crm_people_in_care = [
	# the patients they wrote a clinical record for
	"crm.clinica.cartella.persone_in_cura",
	# the people they opened out of their care, writing why, for a day
	"crm.clinica.dossier.aperti_con_motivo",
]

standard_dropdown_items = [
	{
		"name1": "app_selector",
		"label": "Apps",
		"type": "Route",
		"route": "#",
		"is_standard": 1,
	},
	{
		"name1": "settings",
		"label": "Settings",
		"type": "Route",
		"icon": "settings",
		"route": "#",
		"is_standard": 1,
	},
	{
		"name1": "about",
		"label": "About",
		"type": "Route",
		"icon": "info",
		"route": "#",
		"is_standard": 1,
	},
	{
		"name1": "separator",
		"label": "",
		"type": "Separator",
		"is_standard": 1,
	},
	{
		"name1": "logout",
		"label": "Log out",
		"type": "Route",
		"icon": "log-out",
		"route": "#",
		"is_standard": 1,
	},
]


# ---------------------------------------------------------------------------
# Which modules this installation has.
#
# `crm.invoicing` issues, calculates, formats and transmits documents for any
# sector, and knows nothing about healthcare. `crm.tessera_sanitaria` adds the
# healthcare half and plugs itself in through `crm.invoicing.estensioni`. Every
# module adds its roles, levels and capabilities to `crm.permissions.livelli`.
#
# The wiring lives in `crm.registrazione`, in the app, because deciding which
# modules an installation has is the app's job - not something either module gets
# to assume about the other. It runs here, when the hooks load, and before every
# request and job: outside developer mode Frappe serves hooks from its cache, and a
# worker that finds them there never imports this file.
# Itala pushes its updates with `Authorization: Bearer`: taken away from that one
# address before Frappe authenticates the request (crm/invoicing/sdi/webhook.py)
# an archived private file is opened from the agency's archive, after the framework's
# own check (crm/archivio/archivio.py)
before_request = [
	"crm.registrazione.carica",
	"crm.invoicing.sdi.webhook.prima_della_richiesta",
	"crm.archivio.archivio.prima_della_richiesta",
]
before_job = ["crm.registrazione.carica"]

# signed in, the staff land in DottorCloud, not on the framework's apps screen
on_session_creation = ["crm.api.dopo_l_accesso"]

from crm.registrazione import carica as _carica_moduli

_carica_moduli()
