<!--
  Copyright (c) 2026, NPM2 Solutions Srl and contributors
  For license information, please see license.txt

  What the editor holds, kept as a template (crm.piani.modelli.save_template):
  its title, and whether the whole centre may start from it. No person goes
  with it.
-->
<template>
  <Dialog
    v-model="show"
    :options="{ title: __('Save as a template'), size: 'md' }"
  >
    <template #body-content>
      <div class="flex flex-col gap-3">
        <p class="text-p-sm text-ink-gray-6">
          {{
            __(
              'The moments and what is in them, to start the next plans from. Nothing about the person goes with it.',
            )
          }}
        </p>
        <FormControl v-model="title" :label="__('Title')" />
        <!-- one's own template of the same title is written again, not doubled -->
        <p v-if="esistente" class="text-p-sm text-ink-gray-7">
          {{ __('It replaces your template «{0}».', [esistente.title]) }}
        </p>
        <label class="flex items-center gap-2">
          <Checkbox v-model="shared" class="touch-target shrink-0" />
          <span class="text-base text-ink-gray-8">
            {{ __('For the whole centre') }}
          </span>
        </label>
        <ErrorMessage :message="error" />
      </div>
    </template>
    <template #actions>
      <div class="dialog-footer flex justify-end gap-2">
        <Button :label="__('Cancel')" @click="show = false" />
        <Button
          variant="solid"
          :label="__('Save the template')"
          :disabled="!title.trim()"
          :loading="busy"
          @click="save"
        />
      </div>
    </template>
  </Dialog>
</template>

<script setup>
import {
  Button,
  Checkbox,
  Dialog,
  ErrorMessage,
  FormControl,
  call,
  toast,
} from 'frappe-ui'
import { computed, ref, watch } from 'vue'

const props = defineProps({
  // the editor's content, as save_plan takes it
  data: { type: String, required: true },
  suggestedTitle: { type: String, default: '' },
})
const emit = defineEmits(['saved'])
const show = defineModel({ type: Boolean })

const title = ref('')
const shared = ref(false)
const busy = ref(false)
const error = ref('')

// one's own templates of this kind: the same title writes one of them again
const miei = ref([])
const esistente = computed(() =>
  miei.value.find((m) => m.title === title.value.trim()),
)
// a template written again keeps whether the centre shares it, unless changed
watch(esistente, (m) => {
  if (m) shared.value = Boolean(m.shared)
})

// filled at every opening, the first one too: the dialog is mounted open
watch(
  show,
  async (aperto) => {
    if (!aperto) return
    title.value = props.suggestedTitle
    shared.value = false
    error.value = ''
    miei.value = []
    let tipo
    try {
      tipo = JSON.parse(props.data).plan_type
    } catch {
      return
    }
    try {
      const modelli = await call('crm.piani.modelli.get_templates', {
        plan_type: tipo,
      })
      miei.value = (modelli || []).filter((m) => m.mine)
    } catch {
      miei.value = []
    }
  },
  { immediate: true },
)

async function save() {
  busy.value = true
  error.value = ''
  try {
    await call('crm.piani.modelli.save_template', {
      data: props.data,
      title: title.value,
      shared: shared.value ? 1 : 0,
    })
    toast.success(__('Template saved'))
    emit('saved')
    show.value = false
  } catch (e) {
    error.value = e.messages?.join(' ') || e.message
  } finally {
    busy.value = false
  }
}
</script>
