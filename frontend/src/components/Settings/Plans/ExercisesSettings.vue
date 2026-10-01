<!--
  The exercises plans are written with: the library DottorCloud ships, ready on
  every site (`crm.piani.librerie.carica_libreria`), and the centre's own. Here a
  name becomes the centre's, a body part is put right, an exercise is switched
  off or added. The centre never imports: NPM2 adds to the library in the code.
  The library's pictures come from where the agency hosts them, always with
  whose they are.
-->
<template>
  <LibraryPage
    ref="page"
    :library="library"
    @edit="(row) => Object.assign(editing, { show: true, row })"
    @new="Object.assign(editing, { show: true, row: null })"
  >
    <template #before="{ data }">
      <div
        v-if="data?.can_set_media"
        class="flex flex-col gap-2 rounded-lg border border-outline-gray-2 p-3"
      >
        <div class="flex flex-wrap items-end gap-2">
          <div class="min-w-60 flex-1">
            <FormControl
              v-model="media"
              :label="__('Exercise pictures from')"
              placeholder="https://"
            />
          </div>
          <Button
            class="shrink-0"
            :label="__('Save')"
            :loading="savingMedia"
            :disabled="media === (data.media_url || '')"
            @click="saveMedia"
          />
        </div>
        <span class="text-p-sm text-ink-gray-5">
          {{
            __(
              'Where the agency hosts the library’s pictures, the images/ and videos/ folders: one copy per server or a CDN, not one per site. Empty: no pictures.',
            )
          }}
        </span>
      </div>
    </template>
    <template #after="{ data }">
      <p v-if="data?.has_media" class="px-2 text-p-xs text-ink-gray-5">
        {{
          __('Animations and pictures © Gym visual — https://gymvisual.com/')
        }}
      </p>
    </template>
    <template #dialogs="{ reload }">
      <ExerciseEditDialog
        v-model="editing.show"
        :exercise="editing.row"
        @saved="reload"
      />
    </template>
  </LibraryPage>
</template>

<script setup>
import ExerciseEditDialog from '@/components/Settings/Plans/ExerciseEditDialog.vue'
import LibraryPage from '@/components/Settings/Plans/LibraryPage.vue'
import { PARTI } from '@/utils/piani'
import { Button, FormControl, call, toast } from 'frappe-ui'
import { reactive, ref, watch } from 'vue'

const page = ref(null)
const editing = reactive({ show: false, row: null })

const library = {
  title: __('Exercises'),
  description: __(
    'The exercises plans are written with: the {brand} library, ready to use, and the centre’s own. Names and body parts can be put in the centre’s words.',
  ),
  endpoint: 'crm.piani.librerie.get_exercises',
  nameField: 'exercise_name',
  groups: PARTI,
  everyGroup: __('Every body part'),
  groupLabel: __('Body part'),
  // the library DottorCloud ships keeps this name as its source, in the code only
  sources: [{ value: 'exercises-dataset', label: __('Library') }],
  searchPlaceholder: __('Search an exercise'),
  newLabel: __('New exercise'),
  empty: __('No exercises yet: add the centre’s own with New exercise.'),
  describe: (row) =>
    [
      row.body_part ? __(row.body_part, null, 'Body part') : '',
      row.equipment || '',
    ]
      .filter(Boolean)
      .join(' · '),
  thumbnail: (row) => row.picture || row.animation || null,
}

// ------------------------------------------------------------ the agency's pictures

const media = ref('')
const savingMedia = ref(false)
watch(
  () => page.value?.data?.media_url,
  (url) => (media.value = url || ''),
)

async function saveMedia() {
  savingMedia.value = true
  try {
    await call('crm.piani.librerie.save_media_url', {
      url: media.value || null,
    })
    toast.success(__('Saved'))
    await page.value?.reload()
  } catch (e) {
    toast.error(e.messages?.join(' ') || e.message)
  } finally {
    savingMedia.value = false
  }
}
</script>
