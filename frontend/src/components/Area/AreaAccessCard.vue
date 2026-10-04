<!--
  Copyright (c) 2026, NPM2 Solutions Srl and contributors
  For license information, please see license.txt

  The person's client area, from DottorCloud: who enters it and since when, and
  the invitation that opens it - to the person, or to a parent or somebody who
  follows them. The area itself is /area, with a code by email each time. The
  preview opens it as the person sees it, before the invitation or after, read
  only and with nothing sent (crm.area.anteprima).
-->
<template>
  <section
    v-if="accesses.data"
    class="flex flex-col gap-3 rounded-lg border border-outline-gray-2 p-4"
  >
    <div class="flex flex-wrap items-center justify-between gap-2">
      <h3 class="text-base-semibold text-ink-gray-8">
        {{ __('Who enters the area') }}
      </h3>
      <div class="flex shrink-0 flex-wrap gap-2">
        <Button
          icon-left="eye"
          :label="__('Preview')"
          :title="
            __('See the area as this person sees it: nothing reaches them')
          "
          :loading="previewing"
          @click="preview"
        />
        <Button
          icon-left="user-plus"
          :label="__('Open the area')"
          @click="openDialog"
        />
      </div>
    </div>
    <p v-if="!accesses.data.accesses.length" class="text-p-sm text-ink-gray-5">
      {{
        __(
          'Not open yet. Opened, the person sees their appointments, the documents given online and their invoices at {0}, entering with a code by email.',
          [accesses.data.url],
        )
      }}
    </p>
    <div
      v-for="access in accesses.data.accesses"
      :key="access.user"
      class="flex flex-wrap items-center justify-between gap-2 text-p-sm"
    >
      <span class="flex min-w-0 flex-col">
        <span class="truncate text-ink-gray-8">{{ access.user }}</span>
        <span class="text-p-xs text-ink-gray-5">
          {{ relationLabel(access.relation) }}
          <template v-if="access.last_seen_on">
            ·
            {{
              __('last in {0}', [formatDate(access.last_seen_on, 'D MMM YYYY')])
            }}
          </template>
        </span>
      </span>
      <Badge
        v-if="!access.enabled"
        theme="gray"
        size="sm"
        :label="__('Closed')"
      />
      <Button
        v-else
        size="sm"
        variant="ghost"
        theme="red"
        class="touch-target shrink-0"
        :label="__('Close access')"
        @click="askToRevoke(access)"
      />
    </div>
  </section>

  <Dialog
    v-model="dialog.show"
    :options="{ title: __('Open the area'), size: 'md' }"
  >
    <template #body-content>
      <div class="flex flex-col gap-3">
        <FormControl
          v-model="dialog.relation"
          type="select"
          :label="__('Who enters')"
          :options="relations"
        />
        <FormControl
          v-model="dialog.email"
          type="email"
          :label="__('Their email')"
          :placeholder="
            dialog.relation === 'Self'
              ? accesses.data?.email || ''
              : __('The email of who answers for them')
          "
        />
        <p class="text-p-xs text-ink-gray-5">
          {{
            __(
              'The email says only that the area is open. Each time they enter, a code arrives at this address.',
            )
          }}
        </p>
        <ErrorMessage :message="dialog.error" />
      </div>
    </template>
    <template #actions>
      <div class="dialog-footer flex justify-end gap-2">
        <Button :label="__('Cancel')" @click="dialog.show = false" />
        <Button
          variant="solid"
          :label="__('Send the invitation')"
          :loading="dialog.busy"
          @click="invite"
        />
      </div>
    </template>
  </Dialog>
</template>

<script setup>
import { globalStore } from '@/stores/global'
import { formatDate } from '@/utils'
import {
  Badge,
  Button,
  Dialog,
  ErrorMessage,
  FormControl,
  call,
  createResource,
  toast,
} from 'frappe-ui'
import { reactive, ref, watch } from 'vue'

const props = defineProps({ lead: { type: String, required: true } })
const { $dialog } = globalStore()

const relations = [
  { label: __('The person'), value: 'Self' },
  { label: __('A parent or guardian'), value: 'Parent or guardian' },
  { label: __('Somebody who follows them'), value: 'Follows them' },
]

function relationLabel(value) {
  return relations.find((r) => r.value === value)?.label || value
}

const accesses = createResource({
  url: 'crm.area.accesso.get_accesses',
  makeParams: () => ({ lead: props.lead }),
})
watch(
  () => props.lead,
  (lead) => lead && accesses.reload(),
  { immediate: true },
)

const dialog = reactive({
  show: false,
  relation: 'Self',
  email: '',
  busy: false,
  error: '',
})

function openDialog() {
  Object.assign(dialog, {
    show: true,
    relation: 'Self',
    email: '',
    busy: false,
    error: '',
  })
}

async function invite() {
  dialog.busy = true
  dialog.error = ''
  try {
    const done = await call('crm.area.accesso.invite', {
      lead: props.lead,
      relation: dialog.relation,
      email: dialog.email || null,
    })
    dialog.show = false
    toast.success(__('Invitation sent to {0}', [done.email]))
    accesses.reload()
  } catch (e) {
    dialog.error = e.messages?.join(' ') || e.message
  } finally {
    dialog.busy = false
  }
}

// the area as the person sees it, in a tab of its own: opened on the click, or
// the browser would block it once the call has answered
const previewing = ref(false)
async function preview() {
  previewing.value = true
  const tab = window.open('', '_blank')
  try {
    const done = await call('crm.area.anteprima.start', { lead: props.lead })
    if (tab) tab.location.href = done.url
    else window.location.href = done.url
  } catch (e) {
    tab?.close()
    toast.error(e.messages?.[0] || e.message)
  } finally {
    previewing.value = false
  }
}

// closing takes the person out at their next tap: asked first, and said how
// it opens again
function askToRevoke(access) {
  $dialog({
    title: __('Close access for {0}?', [access.user]),
    message: __(
      'From now on they cannot enter the area. Open it again whenever you want with “Open the area”: a new invitation reaches them.',
    ),
    actions: [
      {
        label: __('Close access'),
        variant: 'solid',
        theme: 'red',
        onClick: (closeDialog) => {
          closeDialog()
          revoke(access)
        },
      },
    ],
  })
}

async function revoke(access) {
  try {
    await call('crm.area.accesso.revoke', {
      lead: props.lead,
      user: access.user,
    })
    accesses.reload()
  } catch (e) {
    toast.error(e.messages?.[0] || e.message)
  }
}
</script>
