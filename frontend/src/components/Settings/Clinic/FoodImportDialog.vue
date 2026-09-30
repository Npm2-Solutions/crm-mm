<!--
  A food table into the library, checked before it comes in: the file is read on
  the server, then the person importing sees which column is which, what group
  each category of the table becomes, and which foods come in - all of an Italian
  table, the ones the Italian tables lack from CIQUAL. CREA and BDA-IEO come in
  only with the centre's licence declared, and the import says who declared it.
-->
<template>
  <Dialog
    v-model="show"
    :options="{ title: __('Import a food table'), size: '4xl' }"
  >
    <template #body-content>
      <!-- the file -->
      <div v-if="step === 'file'" class="flex flex-col gap-3">
        <p class="text-p-base text-ink-gray-7">
          {{
            __(
              'An Excel sheet or a CSV with a row per food and its values for 100 g: CIQUAL as ANSES publishes it, BDA-IEO or CREA as the centre receives them with the licence, or any table in the same shape.',
            )
          }}
        </p>
        <FileUploader
          :file-types="['.xlsx', '.xls', '.csv', '.txt']"
          :upload-args="{ private: true }"
          @success="(file) => read(file.file_url)"
        >
          <template #default="{ openFileSelector, uploading, progress }">
            <div class="flex flex-wrap items-center gap-3">
              <Button
                icon-left="upload"
                :loading="uploading || busy"
                :label="
                  uploading
                    ? __('Uploading {0}%', [progress])
                    : busy
                      ? __('Reading the table…')
                      : __('Choose the file')
                "
                @click="openFileSelector()"
              />
            </div>
          </template>
        </FileUploader>
        <ErrorMessage :message="error" />
      </div>

      <!-- the check -->
      <div v-else-if="step === 'check' && preview" class="flex flex-col gap-4">
        <div class="grid grid-cols-2 gap-3 max-md:grid-cols-1">
          <FormControl
            v-model="source"
            type="select"
            :label="__('The table')"
            :options="sourceOptions"
          />
          <FormControl
            v-model="attribution"
            :label="__('Version and attribution')"
            :placeholder="__('What each food says of where it comes from')"
          />
        </div>
        <label
          v-if="preview.licence"
          class="flex items-start gap-2 rounded-md bg-surface-amber-1 px-3 py-2"
        >
          <Checkbox v-model="licence" class="touch-target mt-0.5 shrink-0" />
          <span class="text-p-sm text-ink-amber-8">
            {{ __(preview.licence) }}
          </span>
        </label>
        <p
          v-if="gapFiller"
          class="rounded-md bg-surface-gray-2 px-3 py-2 text-p-sm text-ink-gray-7"
        >
          {{
            __(
              'The names of this table are not in Italian: choose the foods the Italian tables lack, then rename them in the library.',
            )
          }}
        </p>

        <details class="rounded-md border border-outline-gray-2 px-3 py-2">
          <summary class="cursor-pointer text-base text-ink-gray-8">
            {{ __('Columns') }}
            <span class="text-p-sm text-ink-gray-5">
              · {{ recognisedLine }}
            </span>
          </summary>
          <div class="mt-3 grid grid-cols-3 gap-3 max-md:grid-cols-1">
            <FormControl
              v-for="field in CAMPI_TABELLA"
              :key="field.key"
              v-model="columns[field.key]"
              type="select"
              :label="__(field.label)"
              :options="columnOptions"
            />
          </div>
          <div class="mt-3 flex justify-end">
            <Button
              :label="__('Read again with these columns')"
              :loading="busy"
              @click="reread"
            />
          </div>
        </details>

        <details
          v-if="preview.categories.length"
          class="rounded-md border border-outline-gray-2 px-3 py-2"
        >
          <summary class="cursor-pointer text-base text-ink-gray-8">
            {{ __('Categories and groups') }}
            <span class="text-p-sm text-ink-gray-5">
              · {{ __('{0} categories', [preview.categories.length]) }}
            </span>
          </summary>
          <div class="mt-3 flex flex-col gap-2">
            <div
              v-for="category in preview.categories"
              :key="category.category"
              class="flex items-center justify-between gap-3"
            >
              <span class="min-w-0 text-p-sm text-ink-gray-8">
                {{ category.category || __('No category') }}
                <span class="text-ink-gray-5">· {{ category.count }}</span>
              </span>
              <div class="w-48 shrink-0">
                <FormControl
                  v-model="groups[category.category]"
                  type="select"
                  :options="groupOptions"
                  :aria-label="__('Group')"
                />
              </div>
            </div>
          </div>
        </details>

        <div class="flex flex-col gap-2">
          <div class="flex flex-wrap items-center gap-2">
            <div class="min-w-48 flex-1">
              <FormControl
                v-model="text"
                :placeholder="__('Search a food')"
                :aria-label="__('Search a food')"
              />
            </div>
            <Button
              :label="__('Choose all shown')"
              @click="chooseShown(true)"
            />
            <Button
              :label="__('Leave out all shown')"
              @click="chooseShown(false)"
            />
          </div>
          <div
            class="max-h-80 overflow-y-auto rounded-md border border-outline-gray-2"
          >
            <label
              v-for="food in shown"
              :key="food.key"
              class="flex items-center gap-3 border-b border-outline-gray-1 px-3 py-2 last:border-0"
            >
              <Checkbox
                :model-value="chosen.has(food.key)"
                class="touch-target shrink-0"
                @update:model-value="(on) => choose(food.key, on)"
              />
              <span class="flex min-w-0 flex-1 flex-col">
                <span class="truncate text-p-base text-ink-gray-8">
                  {{ food.name }}
                </span>
                <span class="truncate text-p-xs text-ink-gray-5">
                  {{ __(groupOf(food)) }} ·
                  {{ rigaValori(food, (s, a) => __(s, a)) || __('no values') }}
                  <template v-if="food.kcal_computed">
                    · {{ __('kcal computed') }}
                  </template>
                </span>
              </span>
              <Badge
                v-if="food.known"
                class="shrink-0"
                variant="subtle"
                theme="gray"
                :label="__('In the library')"
              />
            </label>
            <p
              v-if="!shown.length"
              class="px-3 py-4 text-center text-p-sm text-ink-gray-5"
            >
              {{ __('Nothing matches.') }}
            </p>
          </div>
          <span class="text-p-sm text-ink-gray-5">
            {{ __('{0} chosen of {1}', [chosen.size, preview.foods.length])
            }}<template v-if="matching.length > shown.length">
              ·
              {{
                __('showing {0} of {1}: search to narrow', [
                  shown.length,
                  matching.length,
                ])
              }}
            </template>
          </span>
        </div>

        <ul class="flex flex-col gap-0.5 text-p-sm text-ink-gray-6">
          <li v-if="preview.computed">
            {{
              __(
                '{0} foods have no energy in the table: it is computed from their nutrients.',
                [preview.computed],
              )
            }}
          </li>
          <li v-if="leftOut">
            {{
              __(
                '{0} rows are left out: without a name, without a single value, or repeated.',
                [leftOut],
              )
            }}
          </li>
          <li v-if="preview.dropped_values">
            {{
              __(
                '{0} values no food can have were dropped (more than 100 g in 100 g).',
                [preview.dropped_values],
              )
            }}
          </li>
          <li v-if="knownCount">
            {{
              __(
                '{0} chosen foods are in the library already: they get the table’s numbers again, their names stay the centre’s.',
                [knownCount],
              )
            }}
          </li>
        </ul>
        <ErrorMessage :message="error" />
      </div>

      <!-- done -->
      <div v-else-if="step === 'done' && result" class="flex flex-col gap-2">
        <p class="text-p-base text-ink-gray-8">
          {{
            __('{0} foods added, {1} updated.', [
              result.created,
              result.updated,
            ])
          }}
        </p>
        <p class="text-p-sm text-ink-gray-6">
          {{
            __(
              'They are in the library for every plan. Rename them or put a group right from the list.',
            )
          }}
        </p>
      </div>
    </template>
    <template #actions>
      <div class="dialog-footer flex justify-end gap-2">
        <Button
          v-if="step === 'check'"
          :label="__('Another file')"
          @click="restart"
        />
        <Button
          v-if="step === 'check'"
          variant="solid"
          :label="__('Import {0} foods', [chosen.size])"
          :loading="busy"
          :disabled="!chosen.size || !source || (preview?.licence && !licence)"
          @click="importFoods"
        />
        <Button
          v-else
          :label="step === 'done' ? __('Done') : __('Cancel')"
          @click="show = false"
        />
      </div>
    </template>
  </Dialog>
</template>

<script setup>
import {
  CAMPI_TABELLA,
  DA_SCEGLIERE,
  FONTI,
  filtra,
  mappaDalServer,
  mappaPerIlServer,
  rigaValori,
  sceltiAllInizio,
} from '@/utils/librerie'
import { GRUPPI } from '@/utils/piani'
import {
  Badge,
  Button,
  Checkbox,
  Dialog,
  ErrorMessage,
  FileUploader,
  FormControl,
  call,
} from 'frappe-ui'
import { computed, reactive, ref, watch } from 'vue'

const emit = defineEmits(['imported'])
const show = defineModel({ type: Boolean })

// how many foods the list draws at once: the rest is found by searching
const SHOWN = 200

const step = ref('file')
const busy = ref(false)
const error = ref('')
const fileUrl = ref('')
const preview = ref(null)
const source = ref('')
const attribution = ref('')
const licence = ref(false)
const columns = reactive({})
const groups = reactive({})
const chosen = ref(new Set())
const text = ref('')
const result = ref(null)

const sourceOptions = [
  { label: __('Choose the table'), value: '' },
  ...FONTI.map((s) => ({ label: s, value: s })),
]
const groupOptions = GRUPPI.map((g) => ({ label: __(g), value: g }))
const columnOptions = computed(() => [
  { label: __('None'), value: '' },
  ...(preview.value?.columns || []).map((name, i) => ({
    label: name || __('Column {0}', [i + 1]),
    value: String(i),
  })),
])

const gapFiller = computed(() => DA_SCEGLIERE.includes(source.value))
const matching = computed(() => filtra(preview.value?.foods, text.value))
const shown = computed(() => matching.value.slice(0, SHOWN))
const leftOut = computed(() =>
  preview.value
    ? preview.value.without_name +
      preview.value.without_values +
      preview.value.twice
    : 0,
)
const knownCount = computed(
  () =>
    (preview.value?.foods || []).filter(
      (f) => f.known && chosen.value.has(f.key),
    ).length,
)
const recognisedLine = computed(() =>
  CAMPI_TABELLA.filter((c) => columns[c.key] !== '')
    .map((c) => __(c.label))
    .join(', '),
)

watch(show, (open) => {
  if (open) restart()
})

function restart() {
  step.value = 'file'
  error.value = ''
  preview.value = null
  result.value = null
  fileUrl.value = ''
  text.value = ''
  licence.value = false
  source.value = ''
  for (const key of Object.keys(groups)) delete groups[key]
}

function fill(data, keepChoice = false) {
  preview.value = data
  Object.assign(columns, mappaDalServer(data.mapping))
  for (const category of data.categories)
    if (!(category.category in groups) || !keepChoice)
      groups[category.category] = category.group
  if (!keepChoice) {
    source.value = data.source || ''
    attribution.value = data.attribution || ''
    chosen.value = sceltiAllInizio(data.foods, data.source)
  }
}

async function read(url, mapping = null) {
  fileUrl.value = url
  busy.value = true
  error.value = ''
  try {
    const data = await call('crm.clinica.librerie.preview_foods', {
      file_url: url,
      source: source.value || null,
      mapping: mapping ? JSON.stringify(mapping) : null,
    })
    fill(data, Boolean(mapping) || step.value === 'check')
    step.value = 'check'
  } catch (e) {
    error.value = e.messages?.join(' ') || e.message
  } finally {
    busy.value = false
  }
}

function reread() {
  return read(fileUrl.value, mappaPerIlServer(columns, preview.value.mapping))
}

// another table: its attribution, its licence, which foods are known already
watch(source, async (value) => {
  if (!preview.value || !value || value === preview.value.source) return
  licence.value = false
  await read(fileUrl.value, mappaPerIlServer(columns, preview.value.mapping))
  attribution.value = preview.value.attribution || ''
  chosen.value = sceltiAllInizio(preview.value.foods, value)
})

function groupOf(food) {
  return groups[food.category || ''] || food.group
}

function choose(key, on) {
  const next = new Set(chosen.value)
  if (on) next.add(key)
  else next.delete(key)
  chosen.value = next
}

function chooseShown(on) {
  const next = new Set(chosen.value)
  for (const food of matching.value) {
    if (on) next.add(food.key)
    else next.delete(food.key)
  }
  chosen.value = next
}

async function importFoods() {
  busy.value = true
  error.value = ''
  try {
    const all = chosen.value.size === preview.value.foods.length
    result.value = await call('crm.clinica.librerie.import_foods', {
      file_url: fileUrl.value,
      source: source.value,
      attribution: attribution.value || null,
      mapping: JSON.stringify(mappaPerIlServer(columns, preview.value.mapping)),
      groups: JSON.stringify(groups),
      keys: all ? null : JSON.stringify([...chosen.value]),
      licence: licence.value ? 1 : 0,
    })
    step.value = 'done'
    emit('imported')
  } catch (e) {
    error.value = e.messages?.join(' ') || e.message
  } finally {
    busy.value = false
  }
}
</script>
