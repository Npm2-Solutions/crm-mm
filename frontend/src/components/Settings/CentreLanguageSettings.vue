<!--
  Copyright (c) 2026, NPM2 Solutions Srl and contributors
  For license information, please see license.txt

  The centre's language and clock (crm/lingue.py): the language DottorCloud
  writes in for the centre - the emails and pages its clients read, the
  documents, the screens of whoever has not chosen their own - Italian or
  English, and the time zone of its agenda, one of Europe's. DottorCloud's own
  words (consents, libraries) follow a new language by themselves.
-->
<template>
  <SettingsLayoutBase
    :title="__('Language & time')"
    :description="
      __(
        'The language {brand} writes in for the centre - the emails and pages your clients read, the documents, the screens of whoever has not chosen their own - and the clock of its agenda.',
      )
    "
  >
    <template #header-actions>
      <AzioneImpostazioni
        v-if="cambiato"
        :loading="salva.loading"
        @click="salvare"
      />
    </template>
    <template #content>
      <div
        v-if="!stato.data"
        class="flex flex-1 items-center justify-center py-10 text-ink-gray-5"
      >
        <LoadingIndicator class="size-5" />
      </div>
      <div v-else class="flex flex-col divide-y divide-outline-gray-1">
        <SettingsRow
          :label="__('The centre’s language')"
          :description="
            __(
              'Italian or English. Each person can read {brand} in their own, from Your account › Preferences.',
            )
          "
        >
          <FormControl
            v-model="scelte.language"
            type="select"
            class="w-48 max-md:w-full"
            :options="stato.data.languages"
          />
        </SettingsRow>
        <SettingsRow
          :label="__('The centre’s time zone')"
          :description="
            __('The hours of the agenda, the reminders and the booking page.')
          "
        >
          <FormControl
            v-model="scelte.time_zone"
            type="select"
            class="w-80 max-md:w-full"
            :options="fusi"
          />
        </SettingsRow>
      </div>
    </template>
  </SettingsLayoutBase>
</template>

<script setup>
import AzioneImpostazioni from '@/components/Settings/AzioneImpostazioni.vue'
import SettingsLayoutBase from '@/components/Layouts/SettingsLayoutBase.vue'
import SettingsRow from '@/components/Settings/SettingsRow.vue'
import { fusiOrari } from '@/utils/fusiOrari'
import { appLocale } from '@/utils/locale'
import { FormControl, LoadingIndicator, createResource, toast } from 'frappe-ui'
import { computed, reactive } from 'vue'

const scelte = reactive({ language: '', time_zone: '' })

const stato = createResource({
  url: 'crm.lingue.get_centre_language',
  auto: true,
  onSuccess: (dati) =>
    Object.assign(scelte, {
      language: dati.language,
      time_zone: dati.time_zone,
    }),
})

// Europe's zones by their names in the reader's language, the centre's and
// the device's first
const fusi = computed(() =>
  fusiOrari({
    zone: stato.data?.time_zones || [],
    scelto: scelte.time_zone,
    dispositivo: Intl.DateTimeFormat().resolvedOptions().timeZone,
    lingua: appLocale() || 'it',
  }),
)

const cambiato = computed(
  () =>
    Boolean(stato.data) &&
    (scelte.language !== stato.data.language ||
      scelte.time_zone !== stato.data.time_zone),
)

const salva = createResource({
  url: 'crm.lingue.save_centre_language',
  onSuccess: () => {
    toast.success(__('Saved'))
    // every screen reads the new language and clock from the page's start
    window.location.reload()
  },
  onError: (error) =>
    toast.error(error.messages?.join(' ') || __('The choice was not saved')),
})

function salvare() {
  salva.submit({ language: scelte.language, time_zone: scelte.time_zone })
}
</script>
