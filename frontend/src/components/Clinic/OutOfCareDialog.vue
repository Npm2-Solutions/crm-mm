<!--
  Opening the record of somebody not in your care: found by name and surname as
  written, or by tax code - a handful of exact matches, never a browse of the
  centre - and opened only writing why. For a day the person is yours (the
  dossier's rules still apply); the access log keeps who, when and why, for the
  manager and the medical director.
-->
<template>
  <Dialog
    v-model="show"
    :options="{ title: __('Open a record out of your care'), size: 'lg' }"
  >
    <template #body-content>
      <div class="flex flex-col gap-4">
        <p class="text-p-sm text-ink-gray-6">
          {{
            __(
              'For somebody who is not your patient, when you need their record. It stays open for a day; the access log keeps who, when and why, and the manager and the medical director see it.',
            )
          }}
        </p>
        <div class="flex items-end gap-2 max-md:flex-col max-md:items-stretch">
          <FormControl
            v-model="query"
            class="min-w-0 flex-1"
            :label="__('Name and surname, or tax code')"
            :placeholder="__('As they are written')"
            @keydown.enter="search"
          />
          <Button
            class="shrink-0"
            :label="__('Find')"
            :loading="searching"
            :disabled="query.trim().length < 5"
            @click="search"
          />
        </div>
        <div v-if="searched" class="flex flex-col">
          <p v-if="!found.length" class="text-p-sm text-ink-gray-5">
            {{
              __(
                'Nobody with exactly that name or tax code. Write them in full, as they are registered.',
              )
            }}
          </p>
          <button
            v-for="person in found"
            :key="person.name"
            class="flex items-center justify-between gap-3 rounded-md px-3 py-2 text-left text-base hover:bg-surface-gray-2"
            :class="
              chosen?.name === person.name ? 'bg-surface-gray-2' : undefined
            "
            @click="chosen = person"
          >
            <span class="min-w-0 truncate text-ink-gray-8">
              {{ person.lead_name }}
            </span>
            <Badge
              v-if="person.in_care"
              size="sm"
              theme="green"
              class="shrink-0"
              :label="__('In your care')"
            />
          </button>
        </div>
        <FormControl
          v-if="chosen && !chosen.in_care"
          v-model="reason"
          type="textarea"
          :rows="2"
          :label="__('Why you open it')"
          :placeholder="__('What happened, and why their practitioner cannot')"
        />
        <ErrorMessage :message="error" />
      </div>
    </template>
    <template #actions>
      <div class="dialog-footer flex justify-end gap-2">
        <Button :label="__('Cancel')" @click="show = false" />
        <Button
          v-if="chosen?.in_care"
          variant="solid"
          :label="__('Open', null, 'Action')"
          @click="go(chosen.name)"
        />
        <Button
          v-else
          variant="solid"
          :label="__('Open the record')"
          :disabled="!chosen || reason.trim().length < 10"
          :loading="opening"
          @click="open"
        />
      </div>
    </template>
  </Dialog>
</template>

<script setup>
import {
  Badge,
  Button,
  Dialog,
  ErrorMessage,
  FormControl,
  call,
} from 'frappe-ui'
import { ref, watch } from 'vue'
import { useRouter } from 'vue-router'

const show = defineModel({ type: Boolean })
const router = useRouter()

const query = ref('')
const found = ref([])
const searched = ref(false)
const searching = ref(false)
const chosen = ref(null)
const reason = ref('')
const error = ref('')
const opening = ref(false)

watch(show, (isOpen) => {
  if (!isOpen) return
  query.value = ''
  found.value = []
  searched.value = false
  chosen.value = null
  reason.value = ''
  error.value = ''
})

async function search() {
  if (query.value.trim().length < 5) return
  searching.value = true
  error.value = ''
  chosen.value = null
  try {
    found.value = await call('crm.clinica.dossier.find_out_of_care', {
      query: query.value,
    })
    searched.value = true
  } catch (e) {
    error.value = e.messages?.join(' ') || e.message
  } finally {
    searching.value = false
  }
}

async function open() {
  opening.value = true
  error.value = ''
  try {
    await call('crm.clinica.dossier.open_out_of_care', {
      lead: chosen.value.name,
      reason: reason.value,
    })
    go(chosen.value.name)
  } catch (e) {
    error.value = e.messages?.join(' ') || e.message
  } finally {
    opening.value = false
  }
}

function go(lead) {
  show.value = false
  router.push({ name: 'Lead', params: { leadId: lead } })
}
</script>
