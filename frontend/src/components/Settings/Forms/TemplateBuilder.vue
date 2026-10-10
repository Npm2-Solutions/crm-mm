<!--
  Copyright (c) 2026, NPM2 Solutions Srl and contributors
  For license information, please see license.txt
-->
<template>
  <div class="flex h-full flex-col text-ink-gray-8">
    <!-- header: back with the title, where it stands, preview, save, publish -->
    <div
      class="flex items-center justify-between gap-3 px-6 pb-3 pt-8 impostazioni-strette:flex-col impostazioni-strette:items-start max-md:px-3 max-md:pt-5"
    >
      <!-- where the page is narrow (a phone, a tablet held upright) the
           title takes the row and where it stands goes under it: beside a
           long title the badge ran off the screen -->
      <div
        class="flex min-w-0 items-center gap-2 impostazioni-strette:w-full impostazioni-strette:flex-wrap"
      >
        <Button
          variant="ghost"
          icon-left="lucide-chevron-left"
          :label="tpl.title || __('Untitled')"
          size="md"
          class="-ml-4 !max-w-96 !justify-start !pr-0 text-lg-semibold text-ink-gray-7 hover:bg-transparent hover:opacity-70 max-md:-ml-2 impostazioni-strette:!max-w-full"
          @click="goBack"
        />
        <Badge
          v-if="dirty"
          variant="subtle"
          theme="orange"
          size="sm"
          :label="__('Not Saved')"
        />
        <Badge
          v-else-if="meta.current_version_number"
          variant="subtle"
          :theme="meta.unpublished_changes ? 'orange' : 'green'"
          size="sm"
          :label="
            meta.unpublished_changes
              ? __('Changes not published')
              : __('Version {0}', [meta.current_version_number])
          "
        />
        <Badge
          v-else
          variant="subtle"
          theme="gray"
          size="sm"
          :label="__('Draft')"
        />
      </div>
      <div
        class="flex shrink-0 items-center gap-2 impostazioni-strette:w-full impostazioni-strette:flex-wrap"
      >
        <Button
          v-if="tab === 'build'"
          :label="mode === 'edit' ? __('Try it') : __('Edit')"
          @click="mode = mode === 'edit' ? 'preview' : 'edit'"
        >
          <template #prefix>
            <LucideEye v-if="mode === 'edit'" class="size-4" />
            <LucidePencil v-else class="size-4" />
          </template>
        </Button>
        <Button
          :disabled="!dirty"
          :label="__('Save')"
          :loading="saving"
          @click="save"
        />
        <Button
          variant="solid"
          :label="__('Publish')"
          :disabled="publishing || nothingToPublish"
          :tooltip="
            nothingToPublish ? __('Nothing changed since the last version') : ''
          "
          @click="openPublish"
        />
      </div>
    </div>

    <div class="px-6 max-md:px-3">
      <TabButtons v-model="tab" :buttons="tabs" />
    </div>

    <div
      v-if="loaded"
      class="flex-1 overflow-y-auto px-6 pb-8 pt-5 max-md:px-3"
    >
      <!-- BUILD -->
      <template v-if="tab === 'build' && mode === 'edit'">
        <div
          v-if="problems.length"
          class="mb-4 flex flex-col gap-1.5 rounded-lg bg-surface-amber-1 px-4 py-3 text-sm text-ink-amber-7"
        >
          <div class="flex items-center gap-2 font-medium">
            <LucideTriangleAlert class="size-4 shrink-0" />
            {{
              problems.length === 1
                ? __('One thing to fix before publishing')
                : __('{0} things to fix before publishing', [problems.length])
            }}
          </div>
          <button
            v-for="(problem, index) in problems.slice(0, 6)"
            :key="index"
            type="button"
            class="text-left underline-offset-2 hover:underline"
            @click="problem.field && (expanded = problem.field)"
          >
            {{ __(problem.message, problem.args) }}
          </button>
        </div>

        <div class="mb-5 flex flex-col gap-2">
          <input
            v-model="tpl.title"
            :placeholder="__('Form title')"
            class="w-full border-0 bg-transparent p-0 text-2xl font-semibold leading-tight text-ink-gray-9 placeholder:text-ink-gray-4 focus:outline-none focus:ring-0"
          />
          <textarea
            v-model="tpl.description"
            rows="1"
            :placeholder="__('What it is for, for the staff')"
            class="w-full resize-none border-0 bg-transparent p-0 text-base text-ink-gray-6 placeholder:text-ink-gray-4 focus:outline-none focus:ring-0"
          />
        </div>

        <Draggable
          :list="schema.sections"
          item-key="id"
          handle=".section-handle"
          class="flex flex-col gap-3"
          ghost-class="opacity-40"
          :animation="120"
        >
          <template #item="{ element: section }">
            <div class="flex flex-col gap-2 rounded-lg bg-surface-gray-2 p-2.5">
              <div class="flex items-center gap-2">
                <DragVerticalIcon
                  class="section-handle h-3.5 shrink-0 cursor-grab text-ink-gray-3"
                />
                <input
                  v-model="section.title"
                  :placeholder="__('Section title')"
                  class="min-w-0 flex-1 border-0 bg-transparent p-0 text-base-medium text-ink-gray-9 placeholder:font-normal placeholder:italic placeholder:text-ink-gray-4 focus:outline-none focus:ring-0"
                />
                <span
                  v-if="section.fields.length"
                  class="shrink-0 rounded bg-surface-gray-3 px-1.5 py-0.5 text-xs leading-none text-ink-gray-5"
                >
                  {{ section.fields.length }}
                </span>
                <Dropdown :options="sectionMenu(section)">
                  <Button
                    :aria-label="__('Options')"
                    class="touch-target"
                    variant="ghost"
                    icon="lucide-more-horizontal"
                  />
                </Dropdown>
              </div>
              <textarea
                v-if="section.description !== undefined"
                v-model="section.description"
                rows="1"
                :placeholder="__('A few words under the title')"
                class="w-full resize-none border-0 bg-transparent px-5 py-0 text-sm text-ink-gray-6 placeholder:text-ink-gray-4 focus:outline-none focus:ring-0"
              />
              <div v-if="section.show_if !== undefined" class="px-1">
                <TemplateConditions
                  v-model="section.show_if"
                  :label="__('Show the section only if')"
                  :fields="
                    conditionFields(
                      fieldsBefore(schema, { section: section.id }),
                    )
                  "
                />
              </div>

              <Draggable
                :list="section.fields"
                item-key="id"
                group="template-fields"
                handle=".drag-handle"
                class="flex min-h-[34px] flex-col gap-1.5"
                ghost-class="opacity-40"
                :animation="120"
              >
                <template #item="{ element: field }">
                  <TemplateFieldCard
                    :field="field"
                    :expanded="expanded === field.id"
                    :before="fieldsBefore(schema, { field: field.id })"
                    :all="allFields"
                    :consent-types="meta.consent_types"
                    :summary-keys="tpl.clinical ? meta.summary_keys : []"
                    :person-fields="onTheSite ? meta.person_fields : []"
                    :problems="problemsOf(field.id)"
                    @toggle="expanded = expanded === field.id ? null : field.id"
                    @remove="removeField(section, field)"
                    @duplicate="duplicateField(section, field)"
                    @rename="(key) => rename(field, key)"
                  />
                </template>
              </Draggable>

              <Dropdown :options="palette(section)">
                <Button
                  class="!h-8 w-full !bg-surface-elevation-2"
                  variant="outline"
                  icon-left="plus"
                  :label="__('Add a question')"
                />
              </Dropdown>
            </div>
          </template>
        </Draggable>

        <Button
          class="mt-3 !h-8 w-full"
          variant="subtle"
          icon-left="plus"
          :label="__('Add a section')"
          @click="addSection"
        />
      </template>

      <!-- TRY IT: the same rules the person will meet -->
      <div
        v-else-if="tab === 'build'"
        class="mx-auto flex max-w-2xl flex-col gap-5"
      >
        <div
          class="flex items-center justify-between gap-3 rounded-lg bg-surface-gray-1 px-4 py-2.5 text-sm text-ink-gray-6 max-md:flex-col max-md:items-start"
        >
          <span>
            {{
              __(
                'Answer as a person would: conditions, calculations and stops work as they will. Nothing is saved.',
              )
            }}
          </span>
          <div class="flex shrink-0 gap-2">
            <Button
              size="sm"
              :label="__('Check it')"
              @click="previewChecked = true"
            />
            <Button
              size="sm"
              :label="__('Clear the answers')"
              @click="(previewValues = {}), (previewChecked = false)"
            />
          </div>
        </div>
        <h2 class="text-xl font-semibold text-ink-gray-9">{{ tpl.title }}</h2>
        <FormRenderer
          v-model="previewValues"
          :schema="schema"
          :consent-texts="consentTexts"
          :show-missing="previewChecked"
        />
        <div
          v-if="previewChecked"
          class="rounded-lg px-4 py-3 text-sm"
          :class="
            previewState.missing.length
              ? 'bg-surface-amber-1 text-ink-amber-7'
              : 'bg-surface-green-1 text-ink-green-6'
          "
        >
          {{
            previewState.missing.length === 1
              ? __(
                  'One required answer is missing: the form would not be sent.',
                )
              : previewState.missing.length
                ? __(
                    '{0} required answers are missing: the form would not be sent.',
                    [previewState.missing.length],
                  )
                : __('Complete: the form would be sent.')
          }}
          <template v-if="previewState.stops.length && !onTheSite">
            {{
              previewState.stops.length === 1
                ? __('The operator is warned once.')
                : __('The operator is warned {0} times.', [
                    previewState.stops.length,
                  ])
            }}
          </template>
        </div>
      </div>

      <!-- SETTINGS -->
      <div v-else-if="tab === 'settings'" class="flex max-w-2xl flex-col gap-5">
        <FormControl
          v-if="meta.uses.length > 1"
          v-model="tpl.use"
          type="select"
          :label="__('Use')"
          :options="meta.uses"
          :description="useInfo.description"
        />
        <label
          v-if="
            (meta.clinical_available || tpl.clinical) &&
            !onTheSite &&
            !withoutCode
          "
          class="flex items-start gap-2 text-base text-ink-gray-7"
        >
          <Switch
            v-model="tpl.clinical"
            class="mt-0.5 shrink-0"
            size="sm"
            :disabled="meta.clinical_uses.includes(tpl.use)"
          />
          <span>
            {{ __('Health data') }}
            <span class="block text-sm text-ink-gray-5">
              {{
                forThePerson
                  ? __(
                      'Filling it records health data: only the care team reads it, and it makes the person a patient.',
                    )
                  : __(
                      'A sheet with health data is a clinical sheet: written in the clinical record, read by the care team.',
                    )
              }}
            </span>
          </span>
        </label>
        <FormControl
          v-if="
            tpl.clinical || (tpl.use !== 'Form' && !onTheSite && !withoutCode)
          "
          v-model="tpl.specialty"
          :label="__('Specialty')"
          :placeholder="__('Nutrition')"
        />
        <!-- asked of the person, and sent: a sheet is written at the desk -->
        <div
          v-if="sent && !withoutCode"
          class="grid grid-cols-2 gap-3 max-md:grid-cols-1"
        >
          <FormControl
            v-model="tpl.ask_on"
            type="select"
            :label="__('Asked')"
            :options="askOptions"
          />
          <FormControl
            v-model="tpl.validity"
            type="select"
            :label="__('A signed one counts')"
            :options="validityOptions"
          />
          <FormControl
            v-if="tpl.validity === 'Every few weeks'"
            v-model="tpl.validity_weeks"
            type="number"
            inputmode="numeric"
            min="1"
            max="104"
            :label="__('Asked again every how many weeks')"
            :description="
              __(
                'A questionnaire with a score is asked again, and its totals are followed over time on the person\'s page.',
              )
            "
          />
        </div>
        <label
          v-if="sent && !withoutCode && tpl.ask_on !== 'By hand'"
          class="flex items-start gap-2 text-base text-ink-gray-7"
        >
          <Switch v-model="tpl.send_before" class="mt-0.5 shrink-0" size="sm" />
          <span>
            {{ __('Send the link when an appointment is booked') }}
            <span class="block text-sm text-ink-gray-5">
              {{
                __(
                  'Whoever owes it gets it by email to fill before the visit; the message does not say which form.',
                )
              }}
            </span>
          </span>
        </label>
        <div
          v-if="sent && !withoutCode && tpl.ask_on === 'Services'"
          class="flex flex-col gap-1.5"
        >
          <span class="text-sm text-ink-gray-5">{{
            __('For these services')
          }}</span>
          <MultiSelectFilter
            v-model="tpl.services"
            class="self-start"
            icon="lucide-stethoscope"
            :label="__('Services')"
            :options="meta.service_options"
            :empty-text="__('No services yet')"
          />
        </div>
        <template v-if="onTheSite">
          <FormControl
            :model-value="tpl.route"
            type="text"
            :label="__('Address')"
            :placeholder="addressFrom(tpl.title)"
            :description="
              __('Lowercase letters, numbers and dashes: {0}', [pageUrl])
            "
            @update:model-value="(value) => (tpl.route = tidyAddress(value))"
          />
          <FormControl
            v-model="tpl.button_label"
            type="text"
            :label="__('The button')"
            :placeholder="__('Send')"
          />
          <FormControl
            v-model="tpl.success_message"
            type="textarea"
            :rows="3"
            :label="__('What it says once sent')"
            :placeholder="__('Thank you: the centre will be in touch soon.')"
          />
          <FormControl
            v-model="tpl.success_url"
            type="url"
            :label="__('Then it goes to')"
            placeholder="https://www.example.com/grazie"
            :description="
              __(
                'A page of the site to go to after the thanks. Empty, the thanks stay.',
              )
            "
          />
        </template>
        <label class="flex items-start gap-2 text-base text-ink-gray-7">
          <Switch v-model="tpl.enabled" class="mt-0.5 shrink-0" size="sm" />
          <span>
            {{ __('On') }}
            <span class="block text-sm text-ink-gray-5">
              {{
                onTheSite
                  ? __(
                      'Off, it is not on the website any more; what was sent stays.',
                    )
                  : withoutCode
                    ? __(
                        'Off, it is not sent any more; the answers given stay.',
                      )
                    : forThePerson
                      ? __(
                          'Off, it is not asked any more; what was signed on it stays.',
                        )
                      : __(
                          'Off, it is not offered any more; what was written on it stays.',
                        )
              }}
            </span>
          </span>
        </label>
      </div>

      <!-- SHARE: its page, in another site, in a page of the centre's site -->
      <div v-else-if="tab === 'share'" class="flex max-w-2xl flex-col gap-7">
        <p
          v-if="!meta.current_version"
          class="rounded-lg bg-surface-amber-1 px-4 py-3 text-sm text-ink-amber-7"
        >
          {{
            __(
              'Not published yet: the link and the frame show it once it is published. Until then you try it on its page.',
            )
          }}
        </p>
        <div class="flex flex-col gap-2">
          <span class="text-base font-medium text-ink-gray-8">
            {{ __('Its page') }}
          </span>
          <span class="text-p-sm text-ink-gray-6">
            {{
              __(
                "With the centre's logo: to link from an email, a post, a QR code.",
              )
            }}
          </span>
          <div
            class="flex items-center gap-2 max-md:flex-col max-md:items-stretch"
          >
            <TextInput class="min-w-0 flex-1" readonly :model-value="pageUrl" />
            <div class="flex shrink-0 gap-2">
              <Button
                :label="__('Copy')"
                icon-left="lucide-copy"
                @click="copyToClipboard(pageUrl)"
              />
              <Button
                :label="__('Open', null, 'Action')"
                icon-left="lucide-external-link"
                @click="openPage"
              />
            </div>
          </div>
        </div>
        <div class="flex flex-col gap-2">
          <span class="text-base font-medium text-ink-gray-8">
            {{ __('In another site') }}
          </span>
          <span class="text-p-sm text-ink-gray-6">
            {{
              __(
                'Paste this code where the form goes: it grows with the form, and the visit that led there comes along.',
              )
            }}
          </span>
          <div class="relative">
            <textarea
              readonly
              rows="4"
              :aria-label="__('In another site')"
              class="w-full resize-none rounded-md border border-outline-gray-2 bg-surface-gray-1 py-2 pl-3 pr-10 font-mono text-xs text-ink-gray-7 focus:border-outline-gray-4 focus:outline-none focus:ring-0"
              :value="snippet"
            />
            <Button
              :aria-label="__('Copy')"
              class="absolute right-2 top-2"
              size="sm"
              variant="ghost"
              icon="lucide-copy"
              :tooltip="__('Copy')"
              @click="copyToClipboard(snippet)"
            />
          </div>
          <FormControl
            v-model="tpl.allowed_embedding_domains"
            type="textarea"
            :rows="3"
            :label="__('The sites it may be shown in')"
            placeholder="https://www.example.com"
            :description="
              __(
                'One a line. A browser shows the form only in the sites listed here; with none, only on this site.',
              )
            "
          />
          <p v-if="domains.invalid.length" class="text-sm text-ink-red-6">
            {{
              __('Not a site, and left out: {0}', [domains.invalid.join(', ')])
            }}
          </p>
        </div>
        <div v-if="puo('sito.gestisci')" class="flex flex-col gap-1">
          <span class="text-base font-medium text-ink-gray-8">
            {{ __("In a page of the centre's site") }}
          </span>
          <span class="text-p-sm text-ink-gray-6">
            {{
              __(
                'In the Site, the "Form" block shows it inside the page, with the page\'s own look: give it the address {0}.',
                [tpl.route || addressFrom(tpl.title)],
              )
            }}
          </span>
        </div>
      </div>

      <!-- VERSIONS -->
      <div v-else class="flex max-w-3xl flex-col gap-3">
        <p class="text-p-base text-ink-gray-6">
          {{
            __(
              'Each version is kept as it was published, with its fingerprint: what was filled on it points at it, and shows the exact words.',
            )
          }}
        </p>
        <EmptyState
          v-if="!versions.length"
          :title="__('Not published yet')"
          :description="__('People fill a published version, never the draft.')"
        />
        <div
          v-for="version in versions"
          :key="version.name"
          class="flex flex-col gap-1 rounded-lg border border-outline-gray-2 px-4 py-3"
        >
          <div class="flex flex-wrap items-center gap-2">
            <span class="text-base font-medium text-ink-gray-8">
              {{ __('Version {0}', [version.version]) }}
            </span>
            <Badge
              v-if="version.name === meta.current_version"
              :label="__('Current')"
              theme="green"
              variant="subtle"
              size="sm"
            />
            <span class="text-sm text-ink-gray-5">
              {{ formatDate(version.published_on) }} ·
              {{
                getUser(version.published_by)?.full_name || version.published_by
              }}
            </span>
          </div>
          <p
            v-if="version.notes"
            class="whitespace-pre-line text-sm text-ink-gray-7"
          >
            {{ version.notes }}
          </p>
          <p v-if="version.asked_from" class="text-sm text-ink-gray-6">
            {{
              __('Asked again from {0}', [
                formatDate(version.asked_from, 'D MMM YYYY'),
              ])
            }}
          </p>
          <code
            class="truncate text-xs text-ink-gray-5"
            :title="version.schema_hash"
          >
            {{ __('Fingerprint') }} {{ version.schema_hash }}
          </code>
        </div>
      </div>
    </div>
    <div v-else class="flex flex-1 items-center justify-center">
      <LoadingIndicator class="w-4" />
    </div>
  </div>

  <Dialog
    v-model="showPublish"
    :options="{ title: __('Publish a new version') }"
  >
    <template #body-content>
      <div class="flex flex-col gap-4">
        <p class="text-p-base text-ink-gray-6">
          {{
            meta.current_version_number
              ? __(
                  'Version {0} will be filled from now on. What was signed on version {1} keeps its own words.',
                  [
                    meta.current_version_number + 1,
                    meta.current_version_number,
                  ],
                )
              : __(
                  'From now on people fill this version. It will not change: a change is a new version.',
                )
          }}
        </p>
        <FormControl
          v-model="publishDraft.notes"
          type="textarea"
          :rows="3"
          :label="__('What changed')"
          :placeholder="__('For whoever reads the versions later')"
        />
        <template v-if="meta.current_version_number">
          <label class="flex items-start gap-2 text-base text-ink-gray-7">
            <Checkbox v-model="publishDraft.askAgain" class="mt-0.5" />
            <span>
              {{ __('Ask again whoever signed an earlier version') }}
              <span class="block text-sm text-ink-gray-5">
                {{
                  __(
                    'For a change that matters to them, like a new consent text.',
                  )
                }}
              </span>
            </span>
          </label>
          <FormControl
            v-if="publishDraft.askAgain"
            v-model="publishDraft.askedFrom"
            type="date"
            :format="dateFormat()"
            :label="__('From')"
          />
        </template>
        <ErrorMessage :message="publishDraft.error" />
      </div>
    </template>
    <template #actions>
      <div class="dialog-footer flex justify-end gap-2">
        <Button :label="__('Cancel')" @click="showPublish = false" />
        <Button
          variant="solid"
          :label="__('Publish')"
          :loading="publishing"
          @click="publish"
        />
      </div>
    </template>
  </Dialog>
</template>

<script setup>
import TemplateFieldCard from './TemplateFieldCard.vue'
import TemplateConditions from './TemplateConditions.vue'
import FormRenderer from '@/components/Moduli/FormRenderer.vue'
import { componentIconName } from '@/components/Moduli/moduliIcons'
import MultiSelectFilter from '@/components/Calendar/MultiSelectFilter.vue'
import DragVerticalIcon from '@/components/Icons/DragVerticalIcon.vue'
import {
  componentList,
  conditionFields,
  evaluate,
  fieldsBefore,
  fieldsOf,
  newField,
  newSection,
  readyToPublish,
  renameKey,
  takenKeys,
  keyFromLabel,
  usesOf,
} from '@/utils/moduli'
import {
  addressFrom,
  embedSnippet,
  embeddingDomains,
  tidyAddress,
  useProblems,
} from '@/utils/moduliSito'
import { copyToClipboard, dateFormat, formatDate } from '@/utils'
import EmptyState from '@/components/ListViews/EmptyState.vue'
import { globalStore } from '@/stores/global'
import { usersStore } from '@/stores/users'
import LucideEye from '~icons/lucide/eye'
import LucidePencil from '~icons/lucide/pencil'
import LucideTriangleAlert from '~icons/lucide/triangle-alert'
import Draggable from 'vuedraggable'
import {
  Badge,
  Button,
  Checkbox,
  Dialog,
  Dropdown,
  ErrorMessage,
  FormControl,
  LoadingIndicator,
  Switch,
  TabButtons,
  TextInput,
  call,
  toast,
} from 'frappe-ui'
import { computed, nextTick, reactive, ref, watch } from 'vue'
import { oggiDelCentro } from '@/utils/scheduler'

const props = defineProps({ name: { type: String, required: true } })
const emit = defineEmits(['back'])

const { $dialog } = globalStore()
const { getUser, puo } = usersStore()

// a form of the website is shared: its page, a frame, a block of the site
const tabs = computed(() =>
  [
    { label: __('Build'), value: 'build' },
    { label: __('Settings'), value: 'settings' },
    onTheSite.value && { label: __('Share'), value: 'share' },
    { label: __('Versions'), value: 'versions' },
  ].filter(Boolean),
)
const askOptions = [
  { label: __('When somebody asks for it'), value: 'By hand' },
  { label: __('At the first appointment'), value: 'First appointment' },
  { label: __('For some services'), value: 'Services' },
]
const validityOptions = [
  { label: __('For ever'), value: 'Forever' },
  { label: __('For a year'), value: 'One year' },
  { label: __('For a few weeks'), value: 'Every few weeks' },
  { label: __('For one appointment'), value: 'Every appointment' },
]

const loaded = ref(false)
const saving = ref(false)
const publishing = ref(false)
const dirty = ref(false)
const tab = ref('build')
const mode = ref('edit')
const expanded = ref(null)
const previewValues = ref({})
const previewChecked = ref(false)
const previewState = computed(() => evaluate(schema.value, previewValues.value))

const tpl = reactive({})
const schema = ref({ sections: [] })
const versions = ref([])
const meta = reactive({
  uses: [],
  clinical_available: false,
  consent_types: [],
  summary_keys: [],
  clinical_uses: [],
  service_options: [],
  person_fields: [],
  current_version: null,
  current_version_number: 0,
  unpublished_changes: true,
})

const SETTINGS = [
  'title',
  'description',
  'use',
  'clinical',
  'specialty',
  'ask_on',
  'validity',
  'validity_weeks',
  'send_before',
  'enabled',
  'services',
  'route',
  'button_label',
  'success_message',
  'success_url',
  'allowed_embedding_domains',
]

function apply(data) {
  for (const key of SETTINGS) tpl[key] = data[key]
  tpl.clinical = Boolean(data.clinical)
  tpl.enabled = Boolean(data.enabled)
  tpl.send_before = Boolean(data.send_before)
  tpl.services = data.services || []
  schema.value = data.schema?.sections ? data.schema : { sections: [] }
  versions.value = data.versions || []
  for (const key of Object.keys(meta)) {
    if (key in data) meta[key] = data[key]
  }
}

async function load() {
  const data = await call('crm.moduli.modelli.get_template', {
    name: props.name,
  })
  apply(data)
  loaded.value = true
  await nextTick()
  dirty.value = false
}
load()

watch([schema, tpl], () => loaded.value && (dirty.value = true), { deep: true })
// a use that records health data, always
watch(
  () => tpl.use,
  (use) => meta.clinical_uses.includes(use) && (tpl.clinical = true),
)

// who fills it: the person (a form), or the operator at the desk (a sheet)
const useInfo = computed(
  () => meta.uses.find((use) => use.value === tpl.use) || {},
)
const forThePerson = computed(() => useInfo.value.for_the_person !== false)
// asked and sent: a form of the desk, not a sheet nor a form of the website
const sent = computed(() => useInfo.value.sent !== false)
// filled by anybody on the centre's website (crm/moduli/sito.py)
const onTheSite = computed(() => Boolean(useInfo.value.on_the_site))
// a survey: opened by its link alone, sent by an automation or by hand, never
// owed at a booking nor holding health data
const withoutCode = computed(() => Boolean(useInfo.value.without_code))
watch(onTheSite, (on) => !on && tab.value === 'share' && (tab.value = 'build'))

// what is wrong, as the server will say it: the same rules, live
const problems = computed(() => [
  ...readyToPublish(schema.value),
  ...useProblems(schema.value, {
    forThePerson: forThePerson.value,
    onTheSite: onTheSite.value,
    withoutCode: withoutCode.value,
    personFields: meta.person_fields,
  }),
])

const pageUrl = computed(
  () =>
    `${window.location.origin}/crm-form/${tpl.route || addressFrom(tpl.title)}`,
)
const snippet = computed(() =>
  embedSnippet(
    pageUrl.value,
    tpl.route || addressFrom(tpl.title),
    tpl.title || '',
  ),
)
const domains = computed(() => embeddingDomains(tpl.allowed_embedding_domains))

async function openPage() {
  // the page shows what is saved: a draft only to whoever builds it
  if (dirty.value && !(await save())) return
  window.open(pageUrl.value, '_blank')
}
const nothingToPublish = computed(
  () =>
    !dirty.value &&
    Boolean(meta.current_version_number) &&
    !meta.unpublished_changes,
)
function problemsOf(key) {
  return problems.value
    .filter((problem) => problem.field === key)
    .map((problem) => __(problem.message, problem.args))
}
const allFields = computed(() => fieldsOf(schema.value))
const consentTexts = computed(() =>
  Object.fromEntries(meta.consent_types.map((type) => [type.key, type.text])),
)

// --- editing ------------------------------------------------------------------

const GROUPS = ['Questions', 'Content', 'Signing']

function palette(section) {
  return GROUPS.map((group) => ({
    group: __(group),
    items: componentList()
      .filter((kind) => kind.group === group)
      .filter(
        (kind) =>
          !onTheSite.value || !['signature', 'attachment'].includes(kind.type),
      )
      .map((kind) => ({
        label: __(kind.label),
        icon: componentIconName(kind.type),
        onClick: () => addField(section, kind.type),
      })),
  }))
}

function addField(section, type) {
  const field = newField(type, schema.value)
  section.fields.push(field)
  expanded.value = field.id
}

function duplicateField(section, field) {
  const copy = JSON.parse(JSON.stringify(field))
  copy.id = keyFromLabel(field.label || field.id, takenKeys(schema.value))
  section.fields.splice(section.fields.indexOf(field) + 1, 0, copy)
  expanded.value = copy.id
}

function removeField(section, field) {
  const uses = usesOf(schema.value, field.id)
  const drop = () => {
    section.fields.splice(section.fields.indexOf(field), 1)
    if (expanded.value === field.id) expanded.value = null
  }
  if (!uses.length) return drop()
  $dialog({
    title: __('Remove the question?'),
    message: __(
      '{0} other parts of the form use its answer: their conditions or formulas will have to be fixed.',
      [uses.length],
    ),
    variant: 'danger',
    actions: [
      {
        label: __('Remove'),
        variant: 'solid',
        theme: 'red',
        onClick: (close) => {
          drop()
          close()
        },
      },
    ],
  })
}

function rename(field, key) {
  const from = field.id
  if (renameKey(schema.value, from, key)) {
    if (expanded.value === from) expanded.value = key
  } else {
    toast.error(
      __(
        'A key is lowercase letters, digits and _, starts with a letter, and is not taken',
      ),
    )
  }
}

function addSection() {
  schema.value.sections.push(newSection(schema.value))
}

function sectionMenu(section) {
  const index = schema.value.sections.indexOf(section)
  return [
    section.description === undefined && {
      label: __('Add a description'),
      icon: 'lucide-align-left',
      onClick: () => (section.description = ''),
    },
    section.show_if === undefined && {
      label: __('Show only if…'),
      icon: 'lucide-git-branch',
      onClick: () => (section.show_if = null),
    },
    {
      label: __('Remove the section'),
      icon: 'lucide-trash-2',
      theme: 'red',
      onClick: () => {
        if (!section.fields.length)
          return schema.value.sections.splice(index, 1)
        $dialog({
          title: __('Remove the section?'),
          message: __('Its {0} questions go with it.', [section.fields.length]),
          variant: 'danger',
          actions: [
            {
              label: __('Remove'),
              variant: 'solid',
              theme: 'red',
              onClick: (close) => {
                schema.value.sections.splice(index, 1)
                close()
              },
            },
          ],
        })
      },
    },
  ].filter(Boolean)
}

// --- saving and publishing ----------------------------------------------------

async function save() {
  saving.value = true
  try {
    const data = await call('crm.moduli.modelli.save_template', {
      name: props.name,
      ...Object.fromEntries(
        SETTINGS.filter((k) => k !== 'services').map((k) => [k, tpl[k]]),
      ),
      clinical: tpl.clinical ? 1 : 0,
      enabled: tpl.enabled ? 1 : 0,
      send_before: tpl.send_before ? 1 : 0,
      services: JSON.stringify(tpl.services || []),
      schema: JSON.stringify(schema.value),
    })
    loaded.value = false
    apply(data)
    await nextTick()
    loaded.value = true
    dirty.value = false
    toast.success(__('Saved'))
    return true
  } catch (error) {
    toast.error(error.messages?.[0] || error.message)
    return false
  } finally {
    saving.value = false
  }
}

const showPublish = ref(false)
const publishDraft = reactive({
  notes: '',
  askAgain: false,
  askedFrom: '',
  error: '',
})

async function openPublish() {
  if (problems.value.length) {
    tab.value = 'build'
    mode.value = 'edit'
    toast.error(__('Fix what is listed before publishing'))
    return
  }
  if (dirty.value && !(await save())) return
  Object.assign(publishDraft, {
    notes: '',
    askAgain: false,
    askedFrom: oggiDelCentro(),
    error: '',
  })
  showPublish.value = true
}

async function publish() {
  publishing.value = true
  publishDraft.error = ''
  try {
    const version = await call('crm.moduli.modelli.publish_template', {
      name: props.name,
      notes: publishDraft.notes || null,
      asked_from: publishDraft.askAgain ? publishDraft.askedFrom : null,
    })
    showPublish.value = false
    toast.success(__('Version {0} published', [version.version]))
    loaded.value = false
    await load()
  } catch (error) {
    publishDraft.error = error.messages?.join('\n') || error.message
  } finally {
    publishing.value = false
  }
}

function goBack() {
  if (!dirty.value) return emit('back')
  $dialog({
    title: __('Unsaved Changes'),
    message: __(
      'Are you sure you want to go back? Unsaved changes will be lost.',
    ),
    variant: 'solid',
    actions: [
      {
        label: __('Go Back'),
        variant: 'solid',
        onClick: (close) => {
          emit('back')
          close()
        },
      },
    ],
  })
}
</script>
