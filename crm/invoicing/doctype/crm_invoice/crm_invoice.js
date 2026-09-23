// Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
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

  company(frm) {
    // A second company can have a different shape: ask again rather than
    // carrying the first one's answer into it.
    frm.trigger("onload");
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
