<!--
  News in the patient area, told outside it: the email always says only that
  there is news; WhatsApp and SMS may say the same, to the person's own number
  that wrote to the centre, if they ask for it in their area. Here the centre
  chooses what it offers: the approved template, the number SMS leave from.
-->
<template>
  <SettingsLayoutBase>
    <template #title>
      <h2 class="text-2xl-semibold text-ink-gray-9">
        {{ __('News in the patient area') }}
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
                    'No approved WhatsApp template yet: create it in Settings > WhatsApp, then choose it here.',
                  )
            }}
          </span>
        </div>
        <div class="flex flex-col gap-1.5 px-2">
          <FormControl
            v-model="form.sms_number"
            :label="__('SMS from')"
            placeholder="+39…"
            :disabled="!settings.data.twilio"
          />
          <span class="text-p-sm text-ink-gray-5">
            {{
              settings.data.twilio
                ? __('The centre’s Twilio number. Empty: no SMS.')
                : __('Twilio is not connected: SMS are not offered.')
            }}
          </span>
        </div>
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

const form = reactive({ whatsapp_template: '', sms_number: '' })
const saved = reactive({ whatsapp_template: '', sms_number: '' })
const saving = ref(false)
const error = ref('')

function fill(data) {
  for (const target of [form, saved]) {
    target.whatsapp_template = data.whatsapp_template || ''
    target.sms_number = data.sms_number || ''
  }
}

const settings = createResource({
  url: 'crm.clinica.area.avvisi.get_notice_settings',
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

const dirty = computed(
  () =>
    form.whatsapp_template !== saved.whatsapp_template ||
    form.sms_number !== saved.sms_number,
)

async function save() {
  saving.value = true
  error.value = ''
  try {
    const data = await call('crm.clinica.area.avvisi.save_notice_settings', {
      whatsapp_template: form.whatsapp_template || null,
      sms_number: form.sms_number || null,
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
