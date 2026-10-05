<!--
  An exercise of the library, to read and to switch off or on: DottorCloud's,
  never changed by the centre. One of the centre's own, written here: its name,
  the body part, the equipment, how it is done, its video, on or off. The
  library's pictures are shown with whose they are.
-->
<template>
  <Dialog v-model="show" :options="{ title, size: 'xl' }">
    <template #body-content>
      <!-- the library's: what it is, and whether the plans offer it -->
      <div v-if="exercise && !own" class="flex flex-col gap-4">
        <div
          class="flex items-start gap-4 max-md:flex-col max-md:items-stretch"
        >
          <figure
            v-if="(exercise.animation || exercise.picture) && !nonCaricata"
            class="flex shrink-0 flex-col gap-1 max-md:items-center"
          >
            <img
              :src="exercise.animation || exercise.picture"
              alt=""
              class="size-36 rounded-md object-cover"
              @error="nonCaricata = true"
            />
            <figcaption
              v-if="exercise.media_attribution"
              class="max-w-36 text-p-xs text-ink-gray-5"
            >
              {{ exercise.media_attribution }}
            </figcaption>
          </figure>
          <dl
            v-if="facts.length"
            class="grid min-w-0 flex-1 grid-cols-[minmax(min-content,auto)_1fr] gap-x-4 gap-y-2 text-base"
          >
            <template v-for="fact in facts" :key="fact.label">
              <dt class="text-ink-gray-5">{{ fact.label }}</dt>
              <dd class="min-w-0 break-words text-ink-gray-8">
                {{ fact.value }}
              </dd>
            </template>
          </dl>
        </div>
        <div v-if="exercise.instructions" class="flex flex-col gap-1">
          <span class="text-sm font-medium text-ink-gray-7">
            {{ __('How it is done') }}
          </span>
          <p class="whitespace-pre-line text-p-base text-ink-gray-8">
            {{ exercise.instructions }}
          </p>
        </div>
        <SettingsRow
          class="!px-0"
          :label="__('Offered in the plans')"
          :description="
            __(
              'Switched off, it is no longer offered; the plans that have it keep it.',
            )
          "
        >
          <Switch
            :model-value="acceso"
            :disabled="switching"
            @update:model-value="switchIt"
          />
        </SettingsRow>
        <p class="text-p-sm text-ink-gray-5">
          {{ __('From the {brand} library') }}
          <template
            v-if="
              exercise.name_in_source &&
              exercise.name_in_source !== exercise.exercise_name
            "
          >
            · {{ __('originally “{0}”', [exercise.name_in_source]) }}
          </template>
        </p>
        <ErrorMessage :message="error" />
      </div>

      <!-- the centre's own: written here -->
      <div v-else-if="form" class="flex flex-col gap-3">
        <FormControl v-model="form.exercise_name" :label="__('Name')" />
        <div class="grid grid-cols-2 gap-3 max-md:grid-cols-1">
          <FormControl
            v-model="form.body_part"
            type="select"
            :label="__('Body part')"
            :options="partOptions"
          />
          <FormControl v-model="form.equipment" :label="__('Equipment')" />
        </div>
        <FormControl
          v-model="form.instructions"
          type="textarea"
          :rows="6"
          :label="__('How it is done')"
        />
        <div class="grid grid-cols-2 gap-3 max-md:grid-cols-1">
          <FormControl
            v-model="form.primary_muscles"
            :label="__('Main muscles')"
          />
          <FormControl
            v-model="form.secondary_muscles"
            :label="__('Other muscles')"
          />
        </div>
        <FormControl
          v-model="form.video_url"
          type="url"
          :label="__('Video (YouTube or Vimeo)')"
          placeholder="https://"
        />
        <SettingsRow
          class="!px-0"
          :label="__('Offered in the plans')"
          :description="
            __(
              'Switched off, it is no longer offered; the plans that have it keep it.',
            )
          "
        >
          <Switch v-model="form.enabled" />
        </SettingsRow>
        <ErrorMessage :message="error" />
      </div>
    </template>
    <template #actions>
      <div v-if="exercise && !own" class="dialog-footer flex justify-end gap-2">
        <Button :label="__('Close')" @click="show = false" />
      </div>
      <div v-else class="dialog-footer flex justify-end gap-2">
        <Button :label="__('Cancel')" @click="show = false" />
        <Button
          variant="solid"
          :label="__('Save')"
          :loading="saving"
          :disabled="!form?.exercise_name?.trim()"
          @click="save"
        />
      </div>
    </template>
  </Dialog>
</template>

<script setup>
import SettingsRow from '@/components/Settings/SettingsRow.vue'
import { PARTI } from '@/utils/piani'
import {
  Button,
  Dialog,
  ErrorMessage,
  FormControl,
  Switch,
  call,
  toast,
} from 'frappe-ui'
import { computed, ref, watch } from 'vue'

const props = defineProps({ exercise: { type: Object, default: null } })
// saved: a new one, the list is read again; changed: one row, in its place
const emit = defineEmits(['saved', 'changed'])
const show = defineModel({ type: Boolean })

const form = ref(null)
const saving = ref(false)
const switching = ref(false)
// the library's: offered or not, as the last switch left it
const acceso = ref(false)
// the library's picture did not load: no broken one in its place
const nonCaricata = ref(false)
const error = ref('')
const partOptions = PARTI.map((p) => ({
  label: __(p, null, 'Body part'),
  value: p,
}))

const own = computed(() => (props.exercise?.source || 'Centre') === 'Centre')
const title = computed(() => {
  if (!props.exercise) return __('New exercise')
  return own.value ? __('Exercise') : props.exercise.exercise_name
})

// what the library says of it, only what it says
const facts = computed(() => {
  const e = props.exercise || {}
  return [
    [__('Body part'), e.body_part ? __(e.body_part, null, 'Body part') : ''],
    [__('Equipment'), e.equipment],
    [__('Main muscles'), e.primary_muscles],
    [__('Other muscles'), e.secondary_muscles],
  ]
    .filter(([, value]) => value)
    .map(([label, value]) => ({ label, value }))
})

const CAMPI = [
  'exercise_name',
  'body_part',
  'equipment',
  'instructions',
  'primary_muscles',
  'secondary_muscles',
  'video_url',
]

// one of the centre's to put right, or none: a new one, switched on
watch(show, (open) => {
  if (!open) return
  const esercizio = props.exercise || { enabled: 1 }
  error.value = ''
  nonCaricata.value = false
  acceso.value = Boolean(esercizio.enabled)
  form.value = {
    ...Object.fromEntries(CAMPI.map((c) => [c, esercizio[c] || ''])),
    enabled: Boolean(esercizio.enabled),
  }
})

// the library's, switched off or on from here as from its row
async function switchIt(si) {
  switching.value = true
  error.value = ''
  try {
    const fatto = await call('crm.piani.librerie.switch_exercise', {
      name: props.exercise.name,
      enabled: si ? 1 : 0,
    })
    acceso.value = Boolean(fatto.enabled)
    emit('changed', fatto)
  } catch (e) {
    error.value = e.messages?.join(' ') || e.message
  } finally {
    switching.value = false
  }
}

async function save() {
  saving.value = true
  error.value = ''
  try {
    const riga = await call('crm.piani.librerie.save_exercise', {
      name: props.exercise?.name || null,
      data: JSON.stringify({
        ...form.value,
        enabled: form.value.enabled ? 1 : 0,
      }),
    })
    toast.success(__('Saved'))
    if (props.exercise?.name) emit('changed', riga)
    else emit('saved')
    show.value = false
  } catch (e) {
    error.value = e.messages?.join(' ') || e.message
  } finally {
    saving.value = false
  }
}
</script>
