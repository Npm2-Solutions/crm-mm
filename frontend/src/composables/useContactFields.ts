// The address side-panel field for Contact.vue (desktop), MobileContact.vue and
// the person's own page.
//
// Email and mobile used to render as `Dropdown` fields here, with "add another",
// "set as primary" and "delete": the machinery of a person with several numbers.
// One person now has one number and one email, so they are plain fields again —
// typed where they are read, with nothing to choose and nothing to reconcile.

interface ContactDoc {
  name: string
  email_id?: string
  mobile_no?: string
}

interface ContactDocument {
  doc: ContactDoc
  reload: () => Promise<unknown>
}

type SidePanelField = Record<string, unknown> & { fieldname?: string }

export function useContactFields(
  _contact: ContactDocument,
  _options: { emailFieldname?: string } = {},
) {
  return function transformField(
    field: SidePanelField,
    {
      showAddressModal,
    }: { showAddressModal?: (address?: string) => void } = {},
  ): SidePanelField {
    if (field.fieldname === 'address') {
      return {
        ...field,
        create: (_value: unknown, close?: () => void) => {
          showAddressModal?.()
          close?.()
        },
        edit: (address: string) => showAddressModal?.(address),
      }
    }
    return field
  }
}
