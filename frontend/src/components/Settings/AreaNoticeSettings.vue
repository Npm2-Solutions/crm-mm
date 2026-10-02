<!--
  Copyright (c) 2026, NPM2 Solutions Srl and contributors
  For license information, please see license.txt

  News in the client area, told outside it: the email always says only that
  there is news; WhatsApp and SMS may say the same, to the person's own number
  that wrote to the centre, if they ask for it in their area. Here the centre
  chooses what it offers: the approved template; the SMS leave from the centre's
  one sender, set on Twilio's page.
-->
<template>
  <SettingsLayoutBase>
    <template #title>
      <h2 class="text-2xl-semibold text-ink-gray-9">
        {{ __('News in the client area') }}
      </h2>
    </template>
    <template #header-actions>
      <Button
        variant="solid"
        :label="__('Update')"
        :loading="saving"
        :disabled="!dirty"
        @click="save"
      />
    </template>
    <template #content>
      <div v-if="settings.data" class="flex flex-col gap-4 pb-6">
        <p
          class="rounded-md bg-surface-gray-2 px-3 py-2 text-p-sm text-ink-gray-7"
        >
          {{
            __(
              'The email always says only that there is news in the area, and the link. WhatsApp and SMS say the same, to the person’s own number, if it wrote to the centre at least once on that channel and the person asks for it in their area.',
            )
          }}
        </p>
        <div class="flex flex-col gap-1.5 px-2">
          <FormControl
            v-model="form.whatsapp_template"
            type="select"
            :label="__('WhatsApp template')"
            :options="templateOptions"
          />
          <span class="text-p-sm text-ink-gray-5">
            {{
              settings.data.templates.length
                ? __(
                    'An approved template that says only that there is news; its one variable, if any, is the centre’s name.',
                  )
                : __(
                    'No approved WhatsApp template yet: create it in Settings > WhatsApp > Templates, then choose it here.',
                  )
            }}
          </span>
        </div>
        <SmsSenderLine
          :sender="settings.data.sms_sender || ''"
          :twilio="settings.data.twilio"
        />
        <ErrorMessage :message="error" />
      </div>
      <div v-else class="mt-[35%] flex items-center justify-center">
        <LoadingIndicator class="size-6" />
      </div>
    </template>
  </SettingsLayoutBase>
</template>

<script setup>
import SettingsLayoutBase from '@/components/Layouts/SettingsLayoutBase.vue'
import SmsSenderLine from '@/components/Settings/SmsSenderLine.vue'
import {
  Button,
  ErrorMessage,
  FormControl,
  LoadingIndicator,
  call,
  createResource,
  toast,
} from 'frappe-ui'
import { computed, reactive, ref } from 'vue'

const form = reactive({ whatsapp_template: '' })
const saved = reactive({ whatsapp_template: '' })
const saving = ref(false)
const error = ref('')

function fill(data) {
  for (const target of [form, saved]) {
    target.whatsapp_template = data.whatsapp_template || ''
  }
}

const settings = createResource({
  url: 'crm.area.avvisi.get_notice_settings',
  auto: true,
  onSuccess: fill,
})

const templateOptions = computed(() => [
  { label: __('None: no WhatsApp'), value: '' },
  ...(settings.data?.templates || []).map((t) => ({
    label: t.template_name || t.name,
    value: t.name,
  })),
])

const dirty = computed(() => form.whatsapp_template !== saved.whatsapp_template)

async function save() {
  saving.value = true
  error.value = ''
  try {
    const data = await call('crm.area.avvisi.save_notice_settings', {
      whatsapp_template: form.whatsapp_template || null,
    })
    settings.data = data
    fill(data)
    toast.success(__('Saved'))
  } catch (e) {
    error.value = e.messages?.join(' ') || e.message
  } finally {
    saving.value = false
  }
}
</script>
