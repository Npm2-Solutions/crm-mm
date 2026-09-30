<!--
  An exercise of the library, put right: its name in the centre's words, the body
  part, the equipment, how it is done, the centre's own video, on or off. The
  library's pictures stay the library's, shown with whose they are.
-->
<template>
  <Dialog v-model="show" :options="{ title: __('Exercise'), size: 'xl' }">
    <template #body-content>
      <div v-if="form" class="flex flex-col gap-3">
        <div class="flex items-start gap-3 max-md:flex-col">
          <figure
            v-if="exercise.animation || exercise.picture"
            class="flex shrink-0 flex-col gap-1"
          >
            <img
              :src="exercise.animation || exercise.picture"
              alt=""
              class="size-36 rounded-md object-cover"
            />
            <figcaption
              v-if="exercise.media_attribution"
              class="max-w-36 text-p-xs text-ink-gray-5"
            >
              {{ exercise.media_attribution }}
            </figcaption>
          </figure>
          <div class="flex min-w-0 flex-1 flex-col gap-3">
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
          </div>
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
          :label="__('Video (YouTube or Vimeo)')"
          placeholder="https://"
        />
        <label class="flex items-center justify-between gap-3">
          <span class="flex min-w-0 flex-col">
            <span class="text-base text-ink-gray-8">
              {{ __('In the library') }}
            </span>
            <span class="text-p-sm text-ink-gray-5">
              {{
                __(
                  'Switched off, it is no longer offered; the plans that have it keep it.',
                )
              }}
            </span>
          </span>
          <Switch v-model="form.enabled" class="shrink-0" />
        </label>
        <p
          v-if="exercise.source && exercise.source !== 'Centre'"
          class="text-p-sm text-ink-gray-5"
        >
          {{ exercise.source }} · {{ exercise.name_in_source }}
          <template v-if="exercise.source_code">
            · {{ __('code {0}', [exercise.source_code]) }}
          </template>
        </p>
        <ErrorMessage :message="error" />
      </div>
    </template>
    <template #actions>
      <div class="dialog-footer flex justify-end gap-2">
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
import { ref, watch } from 'vue'

const props = defineProps({ exercise: { type: Object, default: null } })
const emit = defineEmits(['saved'])
const show = defineModel({ type: Boolean })

const form = ref(null)
const saving = ref(false)
const error = ref('')
const partOptions = PARTI.map((p) => ({ label: __(p), value: p }))

const CAMPI = [
  'exercise_name',
  'body_part',
  'equipment',
  'instructions',
  'primary_muscles',
  'secondary_muscles',
  'video_url',
]

watch(show, (open) => {
  if (!open || !props.exercise) return
  error.value = ''
  form.value = {
    ...Object.fromEntries(CAMPI.map((c) => [c, props.exercise[c] || ''])),
    enabled: Boolean(props.exercise.enabled),
  }
})

async function save() {
  saving.value = true
  error.value = ''
  try {
    await call('crm.clinica.librerie.save_exercise', {
      name: props.exercise.name,
      data: JSON.stringify({
        ...form.value,
        enabled: form.value.enabled ? 1 : 0,
      }),
    })
    toast.success(__('Saved'))
    emit('saved')
    show.value = false
  } catch (e) {
    error.value = e.messages?.join(' ') || e.message
  } finally {
    saving.value = false
  }
}
</script>
