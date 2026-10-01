<!--
  The centre's exercises, the library its plans are written with: its own, and
  exercises-dataset from its file or GitHub, its pictures from where the agency
  hosts them. Here a name becomes the centre's own, a body part is put right, an
  exercise is switched off; imported again, the dataset brings its pictures and
  muscles, never over the centre's words.
-->
<template>
  <LibraryPage
    ref="page"
    :library="library"
    @edit="(row) => Object.assign(editing, { show: true, row })"
    @import="importing = true"
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
              'Where the agency hosts the images/ and videos/ folders of exercises-dataset: one copy per server or a CDN, not one per site. Empty: no pictures.',
            )
          }}
        </span>
      </div>
    </template>
    <template #after="{ data }">
      <p v-if="data?.has_media" class="px-2 text-p-xs text-ink-gray-5">
        {{
          __(
            'Animations and pictures of exercises-dataset © Gym visual — https://gymvisual.com/',
          )
        }}
      </p>
    </template>
    <template #dialogs="{ reload, data }">
      <ExerciseEditDialog
        v-model="editing.show"
        :exercise="editing.row"
        @saved="reload"
      />
      <ExerciseImportDialog
        v-model="importing"
        :has-media="Boolean(data?.has_media)"
        @imported="reload"
      />
    </template>
  </LibraryPage>
</template>

<script setup>
import ExerciseEditDialog from '@/components/Settings/Plans/ExerciseEditDialog.vue'
import ExerciseImportDialog from '@/components/Settings/Plans/ExerciseImportDialog.vue'
import LibraryPage from '@/components/Settings/Plans/LibraryPage.vue'
import { PARTI } from '@/utils/piani'
import { Button, FormControl, call, toast } from 'frappe-ui'
import { reactive, ref, watch } from 'vue'

const page = ref(null)
const editing = reactive({ show: false, row: null })
const importing = ref(false)

const library = {
  title: __('Exercises'),
  description: __(
    'The exercises plans are written with: the centre’s own, and exercises-dataset. The names and body parts are the centre’s.',
  ),
  endpoint: 'crm.piani.librerie.get_exercises',
  nameField: 'exercise_name',
  groups: PARTI,
  everyGroup: __('Every body part'),
  groupLabel: __('Body part'),
  sources: ['exercises-dataset'],
  searchPlaceholder: __('Search an exercise'),
  importLabel: __('Import exercises'),
  empty: __(
    'No exercises yet: import exercises-dataset, or add them while writing a plan.',
  ),
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
