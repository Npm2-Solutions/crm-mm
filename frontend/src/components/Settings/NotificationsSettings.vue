<!--
  Copyright (c) 2026, NPM2 Solutions Srl and contributors
  For license information, please see license.txt

  Your notifications by email too (crm/notifiche/posta.py): what is still unread
  in the panel a few minutes after it came reaches your email, in DottorCloud's
  words, by the kinds you choose here. Each switch saves itself.
-->
<template>
  <SettingsLayoutBase
    :title="__('Notifications')"
    :description="
      __(
        'What reaches your email too, when you have not read it in {brand} within {0} minutes. Several at once come in one email.',
        [preferenze.data?.minutes || 5],
      )
    "
  >
    <template #content>
      <div class="flex flex-col divide-y divide-outline-gray-1">
        <SettingsRow
          v-for="gruppo in gruppi"
          :key="gruppo.key"
          :label="__(TESTI[gruppo.key]?.label || gruppo.key)"
          :description="__(TESTI[gruppo.key]?.description || '')"
        >
          <Switch
            :model-value="gruppo.on"
            :disabled="salva.loading"
            :aria-label="__(TESTI[gruppo.key]?.label || gruppo.key)"
            @update:model-value="(valore) => cambia(gruppo.key, valore)"
          />
        </SettingsRow>
      </div>
    </template>
  </SettingsLayoutBase>
</template>

<script setup>
import SettingsLayoutBase from '@/components/Layouts/SettingsLayoutBase.vue'
import SettingsRow from '@/components/Settings/SettingsRow.vue'
import { Switch, createResource, toast } from 'frappe-ui'
import { computed } from 'vue'

// each group of the server's (regole.GRUPPI_EMAIL), in the words of the settings
const TESTI = {
  mentions: {
    label: 'Mentions',
    description: 'Who mentions you in a note or a comment.',
  },
  assignments: {
    label: 'Assignments and tasks',
    description: 'A person, a deal or a task given to you, or taken back.',
  },
  area: {
    label: 'Questions from the client area',
    description: 'What a person asks the centre from their area.',
  },
  messages: {
    label: 'WhatsApp, SMS, email and answering service',
    description:
      'The messages of the people you follow, those left on the answering service too: one email for each conversation.',
  },
  agenda: {
    label: 'Agenda',
    description: 'The appointments of the day still without an outcome.',
  },
  invoicing: {
    label: 'Invoicing',
    description: 'An invoice rejected or not delivered, a deadline.',
  },
  automations: {
    label: 'Automations',
    description: 'What an automation of the centre tells you.',
  },
  phone: {
    label: 'Phone numbers',
    description: "Twilio's answer on the documents of a new number.",
  },
}

const preferenze = createResource({
  url: 'crm.notifiche.posta.get_email_preferences',
  auto: true,
})
const gruppi = computed(() => preferenze.data?.groups || [])

const salva = createResource({
  url: 'crm.notifiche.posta.save_email_preferences',
  onSuccess: (data) => preferenze.setData(data),
  onError: (error) =>
    toast.error(error.messages?.[0] || __('The choice was not saved')),
})

function cambia(chiave, valore) {
  const scelte = Object.fromEntries(gruppi.value.map((g) => [g.key, g.on]))
  scelte[chiave] = valore
  // the switch moves at once; the server's answer puts it right
  preferenze.setData({
    ...preferenze.data,
    groups: gruppi.value.map((g) =>
      g.key === chiave ? { ...g, on: valore } : g,
    ),
  })
  salva.submit({ groups: scelte })
}
</script>
