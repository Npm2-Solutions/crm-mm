<!--
  Copyright (c) 2026, NPM2 Solutions Srl and contributors
  For license information, please see license.txt

  The centre's WhatsApp templates: what Meta lets a business send first. A
  template lives on a WhatsApp Business account, never on a number: the page
  shows one number at a time (`numbers`, from the server), with the templates
  it can send, and a new one is made on it.
-->
<template>
  <div
    class="flex h-full flex-col gap-6 py-8 px-6 text-ink-gray-8 max-md:px-3 max-md:py-5"
  >
    <div
      class="flex items-start justify-between gap-3 px-2 impostazioni-strette:flex-col impostazioni-strette:gap-3"
    >
      <div class="flex flex-col gap-1">
        <h2
          class="flex gap-2 text-2xl-semibold leading-tight md:h-5 md:leading-none"
        >
          {{ __('WhatsApp Templates') }}
        </h2>
        <p class="text-p-base text-ink-gray-6">
          {{
            __(
              'Outside 24 hours from the last customer message, WhatsApp only delivers approved templates.',
            )
          }}
        </p>
      </div>
      <div v-if="data.available" class="flex items-center gap-2">
        <!-- A template made in WhatsApp Manager, or `hello_world` that Meta
             creates by itself, exists there and not here — so it cannot be sent
             until it is brought in. Every number's, all of them. -->
        <Button
          :loading="syncing"
          :label="__('Sync from Meta')"
          @click="sync"
        />
        <Button
          variant="solid"
          iconLeft="plus"
          :label="__('New template')"
          :disabled="!numeroAttivo"
          @click="openTemplate()"
        />
      </div>
    </div>

    <div class="flex-1 overflow-y-auto px-2">
      <div
        v-if="templates.data && !data.available"
        class="rounded-lg border border-dashed border-outline-gray-2 p-6 text-center text-p-base text-ink-gray-5"
      >
        {{ __('The WhatsApp app is not installed on this site yet.') }}
      </div>

      <template v-else-if="templates.data">
        <!-- one number at a time, when there is more than one: each has the
             templates of its WhatsApp Business account -->
        <div v-if="numeri.length > 1" class="mb-4 flex flex-col gap-2">
          <div
            role="tablist"
            :aria-label="__('Numbers')"
            class="flex flex-wrap gap-2"
          >
            <button
              v-for="numero in numeri"
              :key="numero.name"
              type="button"
              role="tab"
              :aria-selected="numero.name === scelto"
              class="flex min-h-9 max-w-full items-center gap-1.5 rounded-full border px-3.5 py-1.5 text-base"
              :class="
                numero.name === scelto
                  ? 'border-outline-gray-4 bg-surface-gray-3 text-ink-gray-9'
                  : 'border-outline-gray-2 text-ink-gray-6 hover:bg-surface-gray-1'
              "
              @click="scelto = numero.name"
            >
              <span
                class="truncate"
                :class="{ 'line-through decoration-1': !numero.active }"
                >{{ numero.label }}</span
              >
              <span class="shrink-0 tabular-nums text-ink-gray-5">{{
                modelliDelNumero(data.templates, numero.name).length
              }}</span>
            </button>
          </div>
          <p class="text-p-sm text-ink-gray-6">
            {{ lineaDelNumero(numeroScelto, numeri, __) }}
          </p>
        </div>

        <div
          v-if="visibili.length"
          class="divide-y divide-outline-elevation-2 rounded-lg border border-outline-gray-2"
        >
          <div
            v-for="template in visibili"
            :key="template.name"
            class="relative flex items-center gap-3 px-3 py-2.5 hover:bg-surface-gray-1"
          >
            <!-- the whole row opens it; the bin stays above -->
            <button
              type="button"
              class="min-w-0 flex-1 text-left after:absolute after:inset-0"
              @click="openTemplate(template)"
            >
              <div class="truncate text-p-base text-ink-gray-8">
                {{ template.template_name || template.name }}
              </div>
              <div class="line-clamp-2 text-p-sm text-ink-gray-6">
                {{ template.template }}
              </div>
              <div
                class="mt-0.5 flex flex-wrap gap-x-1.5 text-p-sm text-ink-gray-5"
              >
                <span>{{ categoria(template.category, __).label }}</span>
                <span v-if="linguaDi(template)" aria-hidden="true">·</span>
                <span v-if="linguaDi(template)">{{ linguaDi(template) }}</span>
                <template v-if="template.buttons?.length">
                  <span aria-hidden="true">·</span>
                  <span class="min-w-0 truncate">{{
                    parolePulsanti(template.buttons)
                  }}</span>
                </template>
              </div>
            </button>
            <Badge
              v-if="template.status"
              class="relative shrink-0"
              :label="stato(template.status, __).label"
              :theme="stato(template.status, __).theme"
              size="sm"
            />
            <Button
              class="relative shrink-0"
              variant="ghost"
              icon="lucide-trash-2"
              :aria-label="__('Delete')"
              @click.stop="askToRemove(template)"
            />
          </div>
        </div>

        <EmptyState
          v-else
          :title="__('No templates yet')"
          :text="
            __(
              'WhatsApp lets a business write first, or after 24 hours of silence, only with a template Meta has approved: create one here, or bring the ones you already have on Meta.',
            )
          "
        />
      </template>
    </div>
  </div>

  <Dialog
    v-model="showTemplate"
    :options="{
      title: form.name ? __('Edit template') : __('New template'),
      size: 'xl',
    }"
  >
    <template #body-content>
      <div class="flex flex-col gap-3">
        <!-- a new one is made on a number in use; an existing one stays where
             Meta keeps it -->
        <FormControl
          v-if="!form.name && numeriAttivi.length > 1"
          v-model="form.number"
          type="select"
          :label="__('Number')"
          :options="
            numeriAttivi.map((numero) => ({
              label: numero.label,
              value: numero.name,
            }))
          "
          :description="
            __(
              'Every number of the same WhatsApp Business account can send it.',
            )
          "
        />
        <FormControl
          v-if="!form.name"
          v-model="form.template_name"
          type="text"
          :label="__('Name')"
          :description="
            __(
              'Lowercase letters, digits and underscores. It cannot be changed later.',
            )
          "
        />
        <div
          v-if="!form.name"
          class="grid grid-cols-2 items-start gap-3 max-md:grid-cols-1"
        >
          <FormControl
            v-model="form.category"
            type="select"
            :label="__('Category')"
            :options="categorie(data.categories || [], __)"
            :description="categoria(form.category, __).description"
          />
          <FormControl
            v-model="form.language"
            type="select"
            :label="__('Language')"
            :options="data.languages || []"
          />
        </div>
        <!-- Meta changes a template's words, never its kind or language -->
        <p v-else class="text-p-sm text-ink-gray-6">
          {{
            [categoria(form.category, __).label, linguaDi(form)]
              .filter(Boolean)
              .join(' · ')
          }}
        </p>
        <FormControl
          v-model="form.header"
          type="text"
          :label="__('Header (optional)')"
        />
        <FormControl
          v-model="form.template"
          type="textarea"
          :rows="5"
          :label="__('Message')"
          :placeholder="bodyPlaceholder"
          :description="placeholderHint"
        />
        <!-- Meta wants an example for every {{n}} at creation time, and rejects
             the template the moment it is submitted when one is missing. -->
        <FormControl
          v-if="placeholderCount"
          v-model="form.sample_values"
          type="text"
          :label="__('Example values')"
          :placeholder="samplePlaceholder"
          :description="
            __(
              'One per variable, separated by commas, in order. Meta needs them to review the template — this body has {0}.',
              [placeholderCount],
            )
          "
        />
        <FormControl
          v-model="form.footer"
          type="text"
          :label="__('Footer (optional)')"
        />

        <!-- what the person can tap: a reply in one tap, a link, a call -->
        <div class="flex flex-col gap-2">
          <div class="flex flex-col gap-0.5">
            <span class="text-p-base-medium text-ink-gray-8">
              {{ __('Buttons (optional)') }}
            </span>
            <span class="text-p-sm text-ink-gray-6">
              {{
                __(
                  'A quick reply comes back in the chat with its words. The quick replies come first, then the links and the call.',
                )
              }}
            </span>
          </div>
          <div
            v-for="(pulsante, indice) in form.buttons"
            :key="indice"
            class="flex flex-col gap-2 rounded-lg border border-outline-gray-2 p-2.5"
          >
            <!-- what it does and the ×, then its words as wide as the card:
                 side by side on a phone the words were cut to «Parole sul
                 puls…» -->
            <div class="flex items-center gap-2">
              <FormControl
                v-model="pulsante.type"
                class="min-w-0 flex-1"
                type="select"
                :aria-label="__('What it does')"
                :options="tipiDiPulsante(__)"
              />
              <Button
                class="shrink-0"
                variant="ghost"
                icon="lucide-x"
                :aria-label="__('Remove the button')"
                @click="form.buttons.splice(indice, 1)"
              />
            </div>
            <FormControl
              v-model="pulsante.text"
              type="text"
              :aria-label="__('Words on the button')"
              :placeholder="__('Words on the button')"
              :maxlength="25"
            />
            <FormControl
              v-if="pulsante.type === 'URL'"
              v-model="pulsante.url"
              type="url"
              :disabled="pulsante.dynamic"
              :aria-label="__('Link')"
              placeholder="https://"
              v-bind="tastiera('url')"
            />
            <FormControl
              v-else-if="pulsante.type === 'PHONE_NUMBER'"
              v-model="pulsante.phone"
              type="tel"
              :aria-label="__('Number to call')"
              placeholder="+39 02 1234567"
              v-bind="tastiera('telefono')"
            />
          </div>
          <Button
            class="self-start"
            iconLeft="plus"
            :label="__('Add a button')"
            :disabled="form.buttons.length >= 10"
            @click="aggiungiPulsante"
          />
        </div>

        <div class="rounded-md bg-surface-gray-1 p-3 text-p-sm text-ink-gray-6">
          {{
            __(
              'Saving submits the template to Meta for review. It can be used once the status turns Approved, usually within a few hours.',
            )
          }}
        </div>
      </div>
    </template>
    <template #actions>
      <Button
        class="w-full"
        variant="solid"
        :loading="saving"
        :label="form.name ? __('Save changes') : __('Submit for approval')"
        @click="save"
      />
    </template>
  </Dialog>

  <!-- a template approved by Meta takes hours to approve again: asked first -->
  <Dialog
    v-model="confirmingRemove"
    :options="{
      title: __('Delete {0}?', [removing?.template_name || removing?.name]),
      actions: [
        {
          label: __('Delete'),
          theme: 'red',
          variant: 'solid',
          loading: deleting,
          onClick: remove,
        },
      ],
    }"
  >
    <template #body-content>
      <p class="text-p-base text-ink-gray-6">
        {{
          __(
            'It can no longer be sent. Making it again means submitting it to Meta for review again.',
          )
        }}
      </p>
    </template>
  </Dialog>
</template>

<script setup>
import EmptyState from '@/components/Espresso/EmptyState.vue'
import { createResource, Dialog, FormControl, toast } from 'frappe-ui'
import {
  categoria,
  categorie,
  lineaDelNumero,
  modelliDelNumero,
  numeroIniziale,
  parolePulsanti,
  stato,
  tipiDiPulsante,
} from '@/utils/modelliWhatsApp'
import { tastiera } from '@/utils/tastiera'
import { ref, reactive, computed, watch } from 'vue'

// a literal {{1}} cannot live in the template markup: Vue would parse it
const bodyPlaceholder = __(
  'Hi {0}, we look forward to seeing you tomorrow at {1}.',
  ['{{1}}', '{{2}}'],
)
const placeholderHint = __(
  'Use {0} for the first variable, {1} for the second, and so on.',
  ['{{1}}', '{{2}}'],
)

const saving = ref(false)
const showTemplate = ref(false)

const templates = createResource({
  url: 'crm.integrations.whatsapp.templates.get_templates',
  auto: true,
})

const data = computed(() => templates.data || {})

// the numbers, the one that sends first; the page opens on it
const numeri = computed(() => data.value.numbers || [])
const numeriAttivi = computed(() =>
  numeri.value.filter((numero) => numero.active),
)
const scelto = ref(null)
watch(
  numeri,
  (tutti) => {
    if (!tutti.some((numero) => numero.name === scelto.value))
      scelto.value = numeroIniziale(tutti)
  },
  { immediate: true },
)
const numeroScelto = computed(() =>
  numeri.value.find((numero) => numero.name === scelto.value),
)
// a new template goes on the number shown, when it is in use
const numeroAttivo = computed(() =>
  numeroScelto.value?.active
    ? numeroScelto.value.name
    : numeriAttivi.value[0]?.name || (numeri.value.length ? null : 'default'),
)

const visibili = computed(() =>
  numeri.value.length > 1
    ? modelliDelNumero(data.value.templates, scelto.value)
    : data.value.templates || [],
)

// a language by its name; one Meta has and the site does not, by its code
function linguaDi(modello) {
  const lingua = (data.value.languages || []).find(
    (voce) => voce.value === modello.language,
  )
  return lingua?.label || modello.language_code || ''
}

const form = reactive({
  name: null,
  number: null,
  template_name: '',
  category: 'MARKETING',
  language: 'it',
  language_code: '',
  header: '',
  template: '',
  footer: '',
  sample_values: '',
  buttons: [],
})

// {{1}}, {{2}}… — how many distinct ones the body uses
const placeholderCount = computed(
  () => new Set(form.template?.match(/\{\{\s*\d+\s*\}\}/g) || []).size,
)

const samplePlaceholder = computed(() =>
  Array.from({ length: placeholderCount.value }, (_, i) =>
    i === 0 ? __('Marco') : __('value {0}', [i + 1]),
  ).join(', '),
)

function openTemplate(template = null) {
  form.name = template?.name || null
  form.number = numeroAttivo.value === 'default' ? null : numeroAttivo.value
  form.template_name = template?.template_name || ''
  form.category =
    template?.category || data.value.categories?.[0] || 'MARKETING'
  // the centre's language, not the first of the list (Afrikaans)
  form.language = template?.language || data.value.language || 'it'
  form.language_code = template?.language_code || ''
  form.header = template?.header || ''
  form.template = template?.template || ''
  form.footer = template?.footer || ''
  form.sample_values = template?.sample_values || ''
  form.buttons = (template?.buttons || []).map((pulsante) => ({ ...pulsante }))
  showTemplate.value = true
}

function aggiungiPulsante() {
  form.buttons.push({ type: 'QUICK_REPLY', text: '', url: '', phone: '' })
}

const syncing = ref(false)

function sync() {
  syncing.value = true
  createResource({
    url: 'crm.integrations.whatsapp.templates.sync_templates',
    auto: true,
    onSuccess: (fresh) => {
      syncing.value = false
      templates.data = fresh
      // a number that could not bring its templates in says so, by its name;
      // the others came in all the same
      const problemi = fresh.problems || []
      if (problemi.length)
        problemi.forEach((problema) =>
          toast.error(`${problema.number}: ${problema.error}`),
        )
      else toast.success(__('Templates brought in from Meta'))
    },
    onError: (e) => {
      syncing.value = false
      toast.error(
        e.messages?.[0] || __('Could not read the templates from Meta'),
      )
    },
  })
}

function save() {
  saving.value = true
  const { name, number, ...template } = form
  createResource({
    url: 'crm.integrations.whatsapp.templates.save_template',
    params: { name, number, template },
    auto: true,
    onSuccess: () => {
      saving.value = false
      showTemplate.value = false
      toast.success(__('Template saved'))
      templates.reload()
    },
    onError: (e) => {
      saving.value = false
      toast.error(e.messages?.[0] || __('Failed to save the template'))
    },
  })
}

const confirmingRemove = ref(false)
const removing = ref(null)
const deleting = ref(false)

function askToRemove(template) {
  removing.value = template
  confirmingRemove.value = true
}

function remove() {
  deleting.value = true
  createResource({
    url: 'crm.integrations.whatsapp.templates.delete_template',
    params: { name: removing.value.name },
    auto: true,
    onSuccess: () => {
      deleting.value = false
      confirmingRemove.value = false
      templates.reload()
    },
    onError: (e) => {
      deleting.value = false
      toast.error(e.messages?.[0] || __('Failed to delete'))
    },
  })
}
</script>
