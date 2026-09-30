<!--
  The person's patient area, from the CRM: who enters it and since when, and
  the invitation that opens it - to the person, or to a parent or somebody who
  follows them. The area itself is /area, with a code by email each time.
-->
<template>
  <section
    v-if="accesses.data"
    class="flex flex-col gap-3 rounded-lg border border-outline-gray-2 p-4"
  >
    <div class="flex flex-wrap items-center justify-between gap-2">
      <h3 class="text-base-semibold text-ink-gray-8">
        {{ __('Patient area') }}
      </h3>
      <Button
        class="shrink-0"
        icon-left="user-plus"
        :label="__('Open the area')"
        @click="openDialog"
      />
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
        :label="__('Close')"
        @click="revoke(access)"
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
import { reactive, watch } from 'vue'

const props = defineProps({ lead: { type: String, required: true } })

const relations = [
  { label: __('The person'), value: 'Self' },
  { label: __('A parent or guardian'), value: 'Parent or guardian' },
  { label: __('Somebody who follows them'), value: 'Follows them' },
]

function relationLabel(value) {
  return relations.find((r) => r.value === value)?.label || value
}

const accesses = createResource({
  url: 'crm.clinica.area.accesso.get_accesses',
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
    const done = await call('crm.clinica.area.accesso.invite', {
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

async function revoke(access) {
  try {
    await call('crm.clinica.area.accesso.revoke', {
      lead: props.lead,
      user: access.user,
    })
    accesses.reload()
  } catch (e) {
    toast.error(e.messages?.[0] || e.message)
  }
}
</script>
