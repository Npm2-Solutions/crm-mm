<!--
  Modifications copyright (c) 2026, NPM2 Solutions Srl

  What a new message does to the person or the deal; the fields wait for the
  settings, as a page opened from a link draws before they come.
-->
<template>
  <div
    class="flex h-full flex-col gap-6 py-8 px-6 text-ink-gray-8 max-md:px-3 max-md:py-5"
  >
    <div class="flex flex-col gap-1 px-2">
      <h2
        class="flex gap-2 text-2xl-semibold leading-tight md:h-5 md:leading-none"
      >
        {{ __('Conversations') }}
      </h2>
      <p class="text-p-base text-ink-gray-6">
        {{
          __(
            'What a new message does to the person or the deal it is about, and how their activity reads.',
          )
        }}
      </p>
    </div>

    <!-- once the settings have come: the first draw read them from nothing -->
    <div v-if="settings.doc" class="flex-1 flex flex-col overflow-y-auto">
      <div class="flex items-center justify-between gap-4 py-3 px-2">
        <div class="flex min-w-0 flex-col">
          <div class="text-p-base-medium text-ink-gray-7">
            {{ __('Update timestamp on new communication') }}
          </div>
          <div class="text-p-sm text-ink-gray-5">
            {{
              __(
                'Update the modified timestamp on new email communication & comments for leads & deals',
              )
            }}
          </div>
        </div>
        <div>
          <Switch
            v-model="settings.doc.update_timestamp_on_new_communication"
            size="sm"
            @click.stop="toggle('update_timestamp_on_new_communication')"
          />
        </div>
      </div>
      <div class="h-px border-t mx-2 border-outline-elevation-2" />
      <div class="flex gap-4 items-center justify-between py-3 px-2">
        <div class="flex min-w-0 flex-col">
          <div class="text-p-base-medium text-ink-gray-7">
            {{ __('Mark lead/deal as replied on response') }}
          </div>
          <div class="text-p-sm text-ink-gray-5">
            {{
              __(
                'Automatically sets communication status to “Replied” for the lead or deal when a response is received. Applies only when SLA is enabled',
              )
            }}
          </div>
        </div>
        <div>
          <Switch
            v-model="settings.doc.auto_mark_replied_on_response"
            size="sm"
            @click.stop="toggle('auto_mark_replied_on_response')"
          />
        </div>
      </div>
      <div class="h-px border-t mx-2 border-outline-elevation-2" />
      <div class="flex gap-4 items-center justify-between py-3 px-2">
        <div class="flex min-w-0 flex-col">
          <div class="text-p-base-medium text-ink-gray-7">
            {{ __('Reopen lead/deal on new communication') }}
          </div>
          <div class="text-p-sm text-ink-gray-5">
            {{
              __(
                'Automatically sets communication status to “Open” for the lead or deal when a new communication is created. Applies only when SLA is enabled',
              )
            }}
          </div>
        </div>
        <div>
          <Switch
            v-model="settings.doc.auto_reopen_on_new_communication"
            size="sm"
            @click.stop="toggle('auto_reopen_on_new_communication')"
          />
        </div>
      </div>
      <div class="h-px border-t mx-2 border-outline-elevation-2" />
      <div class="flex gap-4 items-center justify-between py-3 px-2">
        <div class="flex min-w-0 flex-col">
          <div class="text-p-base font-medium text-ink-gray-7">
            {{ __('Timeline timestamp format') }}
          </div>
          <div class="text-p-sm text-ink-gray-5">
            {{
              __(
                'Show timestamps in the activity timeline as relative time (5 mins ago) or an exact date & time',
              )
            }}
          </div>
        </div>
        <div>
          <FormControl
            v-model="settings.doc.crm_timeline_timestamp_format"
            type="select"
            class="w-40"
            :options="timestampFormatOptions"
            :placeholder="__('Relative')"
            @update:modelValue="save()"
          />
        </div>
      </div>
      <div class="h-px border-t mx-2 border-outline-elevation-2" />
      <div class="flex gap-4 items-center justify-between py-3 px-2">
        <div class="flex min-w-0 flex-col">
          <div class="text-p-base font-medium text-ink-gray-7">
            {{ __('Timeline sort order') }}
          </div>
          <div class="text-p-sm text-ink-gray-5">
            {{
              __(
                'Order of activities, emails, comments and calls in the timeline',
              )
            }}
          </div>
        </div>
        <div>
          <FormControl
            v-model="settings.doc.crm_timeline_sort_order"
            type="select"
            class="w-40"
            :options="sortOrderOptions"
            :placeholder="__('Oldest First')"
            @update:modelValue="save()"
          />
        </div>
      </div>
      <div class="h-px border-t mx-2 border-outline-elevation-2" />
      <div class="flex gap-4 items-center justify-between py-3 px-2">
        <div class="flex min-w-0 flex-col">
          <div class="text-p-base font-medium text-ink-gray-7">
            {{ __('Send WhatsApp read receipts') }}
          </div>
          <div class="text-p-sm text-ink-gray-5">
            {{
              __(
                'When somebody here marks a conversation read — with the button, by replying, or by marking it handled — tell WhatsApp, and the customer sees the blue ticks. Opening a chat never sends them.',
              )
            }}
          </div>
        </div>
        <div>
          <Switch
            v-model="settings.doc.whatsapp_read_receipts"
            @update:modelValue="save()"
          />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { getSettings } from '@/stores/settings'
import { FormControl, Switch, toast } from 'frappe-ui'

const { _settings: settings } = getSettings()

const timestampFormatOptions = [
  { label: __('Relative'), value: 'Relative' },
  { label: __('Exact'), value: 'Exact' },
]
const sortOrderOptions = [
  { label: __('Oldest First'), value: 'Oldest First' },
  { label: __('Newest First'), value: 'Newest First' },
]

function toggle(settingKey) {
  settings.save.submit(null, {
    onSuccess: () => {
      toast.success(
        settings.doc[settingKey]
          ? __('Setting enabled successfully')
          : __('Setting disabled successfully'),
      )
    },
  })
}

function save() {
  settings.save.submit(null, {
    onSuccess: () => toast.success(__('Setting updated successfully')),
  })
}
</script>
