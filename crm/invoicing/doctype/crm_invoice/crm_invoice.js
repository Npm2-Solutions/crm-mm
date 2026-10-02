// Copyright (c) 2026, NPM2 Solutions Srl and contributors
// For license information, please see license.txt

/**
 * The form asks only what it cannot work out.
 *
 * Whoever performed a service decides the VAT regime, the fund and - where the
 * healthcare module is installed - whether the SdI may carry the document at
 * all. In a centre that makes it the most important field on the line. For
 * somebody working alone it is the same name every time, on a field with exactly
 * one possible value, and asking is pure friction sixty times a day.
 *
 * So the shape of the practice is derived from how many providers are enabled,
 * never configured. The day a second one is added the field comes back on its
 * own, and nobody has to remember a setting.
 */

frappe.ui.form.on("CRM Invoice", {
  onload(frm) {
    frappe.call({
      method: "crm.invoicing.api.practice_shape",
      args: { company: frm.doc.company || "" },
      callback: ({ message }) => {
        frm._forma = message || {};
        applica_forma(frm);
      },
    });
  },

  refresh(frm) {
    scelte_in_parole(frm);
    // the states stay the Agenzia's words, what a portal receipt says - but as
    // words: «Da inviare», not `da_inviare`
    ["sdi_status", "ts_status"].forEach((campo) =>
      frm.set_df_property(campo, "formatter", (valore) =>
        frappe.utils.escape_html(stato_in_parole(valore)),
      ),
    );
  },

  company(frm) {
    // A second company can have a different shape: ask again rather than
    // carrying the first one's answer into it. Its category decides the
    // expense types too.
    frm.trigger("onload");
    scelte_in_parole(frm);
  },
});

frappe.ui.form.on("CRM Invoice Item", {
  items_add(frm, cdt, cdn) {
    const forma = frm._forma || {};
    if (forma.solo && forma.provider) {
      frappe.model.set_value(cdt, cdn, "service_provider", forma.provider);
    }
  },
});

function applica_forma(frm) {
  const forma = frm._forma || {};
  const griglia = frm.fields_dict.items && frm.fields_dict.items.grid;
  if (!griglia) return;

  // Hidden rather than read-only: a locked field still takes a column and still
  // invites a click. What cannot vary should not be on screen.
  griglia.update_docfield_property(
    "service_provider",
    "hidden",
    forma.solo ? 1 : 0,
  );
  griglia.update_docfield_property(
    "service_provider",
    "reqd",
    forma.solo ? 0 : 1,
  );
  griglia.update_docfield_property(
    "service_provider",
    "in_list_view",
    forma.solo ? 0 : 1,
  );

  if (forma.solo && forma.provider) {
    (frm.doc.items || []).forEach((riga) => {
      if (!riga.service_provider) {
        frappe.model.set_value(
          riga.doctype,
          riga.name,
          "service_provider",
          forma.provider,
        );
      }
    });
  }
  griglia.refresh();
}

/**
 * Codes in words. Every select that holds a code offers its choices by name,
 * only the ones the practice meets (crm.invoicing.scelte: with the clinic on,
 * the healthcare ones), and a stored code reads as its name: "Card or app",
 * not MP08. The values already on the document stay offered, whatever the
 * profile, so nothing chosen before disappears from its own field.
 */
function scelte_in_parole(frm) {
  frappe.call({
    method: "crm.invoicing.scelte.get_options",
    args: { doctype: frm.doctype, doc: frm.doc },
    callback: ({ message }) => {
      const scelte = message || {};
      Object.entries(scelte.fields || {}).forEach(([campo, opzioni]) => {
        frm.set_df_property(campo, "options", opzioni);
        frm.set_df_property(campo, "formatter", nome_da(opzioni));
      });
      Object.entries(scelte.tables || {}).forEach(([tabella, campi]) => {
        const griglia = frm.fields_dict[tabella] && frm.fields_dict[tabella].grid;
        if (!griglia || !griglia.grid_rows) return;
        Object.entries(campi).forEach(([campo, opzioni]) => {
          griglia.update_docfield_property(campo, "options", opzioni);
          griglia.update_docfield_property(campo, "formatter", nome_da(opzioni));
        });
        griglia.refresh();
      });
    },
  });
}

/** What a read-only field or a grid row shows: the name of its code. */
function nome_da(opzioni) {
  const nomi = {};
  opzioni.forEach((opzione) => {
    nomi[opzione.value] = opzione.label;
  });
  return (valore) =>
    frappe.utils.escape_html(
      valore && nomi[valore] ? nomi[valore] : valore || "",
    );
}

/** The same as the console's `statusLabel` (frontend/src/utils/invoicing.js). */
function stato_in_parole(stato) {
  const parole = String(stato || "")
    .replace(/_/g, " ")
    .trim();
  return parole.charAt(0).toUpperCase() + parole.slice(1);
}
