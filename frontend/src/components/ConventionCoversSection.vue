<!--
  Copyright (c) 2026, NPM2 Solutions Srl and contributors
  For license information, please see license.txt

  A person's funds, insurances and company conventions (crm/convenzioni, doc 61):
  each with its card or policy number, whose it is (themselves or a linked
  person: a child on the parent's fund), until when. The appointment's panel
  offers the person's own first; read with the person, written by whoever
  writes people.
-->
<template>
  <div v-if="coperture.data" class="flex flex-col">
    <div class="h-px w-full border-t" />
    <div class="p-1 sm:p-3">
      <CollapsibleSection
        labelClass="px-2 font-semibold"
        headerClass="h-8"
        :label="__('Funds and conventions')"
        :count="coperture.data.covers.length || ''"
      >
        <template #actions>
          <Button
            v-if="coperture.data.can_edit && coperture.data.conventions.length"
            variant="ghost"
            class="touch-target"
            icon="plus"
            :aria-label="__('Add a cover')"
            :title="__('Add a cover')"
            @click="apri(null)"
          />
        </template>
        <div class="flex flex-col gap-0.5 pb-1 pt-2">
          <div
            v-for="c in coperture.data.covers"
            :key="c.name"
            class="flex items-start gap-2 rounded px-3 py-1.5"
          >
            <span
              class="lucide-shield-check mt-0.5 size-4 shrink-0"
              :class="c.valid ? 'text-ink-green-7' : 'text-ink-gray-5'"
              aria-hidden="true"
            />
            <div class="flex min-w-0 flex-1 flex-col">
              <span class="flex flex-wrap items-center gap-x-2 gap-y-0.5">
                <span class="max-w-full truncate text-base text-ink-gray-8">
                  {{ c.convention_name }}
                </span>
                <Badge
                  v-if="!c.valid"
                  size="sm"
                  variant="subtle"
                  theme="gray"
                  :label="__('Not valid today')"
                />
              </span>
              <span class="text-p-sm text-ink-gray-5">
                {{ nomeDelTipo(c.kind, t) }}
              </span>
              <span
                v-if="rigaDellaCopertura(c, t, giorno)"
                class="text-p-sm text-ink-gray-6 [overflow-wrap:anywhere]"
              >
                {{ rigaDellaCopertura(c, t, giorno) }}
              </span>
            </div>
            <Button
              v-if="coperture.data.can_edit"
              size="sm"
              variant="ghost"
              class="touch-target shrink-0"
              :label="__('Edit')"
              @click="apri(c)"
            />
          </div>
          <div
            v-if="!coperture.data.covers.length"
            class="px-3 py-1 text-p-sm text-ink-gray-5"
          >
            {{
              coperture.data.conventions.length
                ? __('No fund nor convention: they pay as everybody does.')
                : __(
                    'The centre has no convention yet: Settings > Invoicing > Conventions and funds.',
                  )
            }}
          </div>
        </div>
      </CollapsibleSection>
    </div>
  </div>

  <Dialog
    v-model="dialogo.show"
    :options="{
      title: dialogo.name ? __('Change the cover') : __('Add a cover'),
      size: 'md',
    }"
  >
    <template #body-content>
      <div class="flex flex-col gap-4">
        <FormControl
          v-model="dialogo.convention"
          type="select"
          :label="__('Convention')"
          :options="opzioni"
        />
        <FormControl
          v-model="dialogo.card_number"
          :label="__('Policy or card number')"
          :placeholder="__('As on the card')"
          v-bind="tastiera('codice')"
        />
        <Link
          class="w-full"
          doctype="CRM Lead"
          variant="outline"
          :label="__('Holder, when it is somebody else')"
          :filters="{ name: ['!=', lead] }"
          :modelValue="dialogo.holder"
          :placeholder="__('The person themselves')"
          @update:modelValue="(v) => (dialogo.holder = v)"
        />
        <div class="grid grid-cols-2 gap-3 max-md:grid-cols-1">
          <FormControl
            v-model="dialogo.valid_from"
            type="date"
            :label="__('Valid from')"
          />
          <FormControl
            v-model="dialogo.valid_upto"
            type="date"
            :label="__('Valid until')"
          />
        </div>
        <FormControl
          v-model="dialogo.notes"
          type="textarea"
          :label="__('Note')"
          :rows="2"
        />
        <ErrorMessage :message="dialogo.error" />
      </div>
    </template>
    <template #actions>
      <div class="flex flex-wrap items-center justify-between gap-2">
        <Button
          v-if="dialogo.name"
          variant="ghost"
          theme="red"
          :label="__('Remove')"
          :loading="dialogo.saving === 'remove'"
          @click="togli"
        />
        <span v-else />
        <Button
          variant="solid"
          :label="__('Save')"
          :loading="dialogo.saving === 'save'"
          @click="salva"
        />
      </div>
    </template>
  </Dialog>
</template>

<script setup>
import CollapsibleSection from '@/components/CollapsibleSection.vue'
import Link from '@/components/Controls/Link.vue'
import { usersStore } from '@/stores/users'
import { formatDate } from '@/utils'
import { nomeDelTipo, rigaDellaCopertura } from '@/utils/convenzioni'
import { tastiera } from '@/utils/tastiera'
import {
  Badge,
  Dialog,
  ErrorMessage,
  FormControl,
  call,
  createResource,
  toast,
} from 'frappe-ui'
import { computed, reactive, watch } from 'vue'

const props = defineProps({
  lead: { type: String, required: true },
})

const { puo } = usersStore()
const t = (text, args, context) => __(text, args, context)
const giorno = (g) => formatDate(g, 'D MMM YYYY')

const coperture = createResource({
  url: 'crm.convenzioni.api.get_covers',
  makeParams: () => ({ lead: props.lead }),
  onError: () => coperture.setData(null),
})

watch(
  () => props.lead,
  (lead) => lead && puo('persone.vedi') && coperture.reload(),
  { immediate: true },
)

const opzioni = computed(() => [
  ...(dialogo.convention ? [] : [{ label: __('Choose…'), value: '' }]),
  ...(coperture.data?.conventions || []).map((c) => ({
    label: c.convention_name,
    value: c.name,
  })),
])

const dialogo = reactive({
  show: false,
  name: null,
  convention: '',
  card_number: '',
  holder: '',
  valid_from: '',
  valid_upto: '',
  notes: '',
  error: '',
  saving: '',
})

function apri(c) {
  Object.assign(dialogo, {
    show: true,
    name: c?.name || null,
    convention:
      c?.convention ||
      (coperture.data?.conventions.length === 1
        ? coperture.data.conventions[0].name
        : ''),
    card_number: c?.card_number || '',
    holder: c?.holder || '',
    valid_from: c?.valid_from || '',
    valid_upto: c?.valid_upto || '',
    notes: c?.notes || '',
    error: '',
    saving: '',
  })
}

async function salva() {
  dialogo.error = ''
  if (!dialogo.convention) {
    dialogo.error = __('Choose the convention')
    return
  }
  dialogo.saving = 'save'
  try {
    const dati = await call('crm.convenzioni.api.save_cover', {
      lead: props.lead,
      name: dialogo.name,
      data: JSON.stringify({
        convention: dialogo.convention,
        card_number: dialogo.card_number,
        holder: dialogo.holder || null,
        valid_from: dialogo.valid_from || null,
        valid_upto: dialogo.valid_upto || null,
        notes: dialogo.notes || null,
      }),
    })
    coperture.setData(dati)
    dialogo.show = false
    toast.success(__('Saved'))
  } catch (e) {
    dialogo.error = e.messages?.[0] || e.message
  } finally {
    dialogo.saving = ''
  }
}

async function togli() {
  dialogo.saving = 'remove'
  try {
    const dati = await call('crm.convenzioni.api.remove_cover', {
      lead: props.lead,
      name: dialogo.name,
    })
    coperture.setData(dati)
    dialogo.show = false
    toast.success(__('Cover removed'))
  } catch (e) {
    dialogo.error = e.messages?.[0] || e.message
  } finally {
    dialogo.saving = ''
  }
}
</script>
