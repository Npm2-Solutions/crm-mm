<!--
  The exercises plans are written with: the library DottorCloud ships, all there
  on every site with its pictures (`crm.piani.librerie.carica_libreria`, the
  server's copy by `crm.piani.immagini`), and the centre's own. The centre
  switches off the ones it does not use and adds its own; it changes nothing of
  the library's, and never imports: NPM2 adds to the library in the code.
-->
<template>
  <LibraryPage
    :library="library"
    @edit="(row) => Object.assign(editing, { show: true, row })"
    @new="Object.assign(editing, { show: true, row: null })"
  >
    <template #after="{ data }">
      <p v-if="data?.has_media" class="px-2 text-p-xs text-ink-gray-5">
        {{
          __('Animations and pictures © Gym visual — https://gymvisual.com/')
        }}
      </p>
    </template>
    <template #dialogs="{ reload, aggiorna }">
      <ExerciseEditDialog
        v-model="editing.show"
        :exercise="editing.row"
        @saved="reload"
        @changed="aggiorna"
      />
    </template>
  </LibraryPage>
</template>

<script setup>
import ExerciseEditDialog from '@/components/Settings/Plans/ExerciseEditDialog.vue'
import LibraryPage from '@/components/Settings/Plans/LibraryPage.vue'
import { PARTI } from '@/utils/piani'
import { reactive } from 'vue'

const editing = reactive({ show: false, row: null })

const library = {
  title: __('Exercises'),
  description: __(
    'The exercises plans are written with: the {brand} library, all there already, and the ones the centre adds. Switch off the ones the centre does not use: they are no longer offered.',
  ),
  endpoint: 'crm.piani.librerie.get_exercises',
  switchEndpoint: 'crm.piani.librerie.switch_exercise',
  nameField: 'exercise_name',
  groups: PARTI,
  groupContext: 'Body part',
  everyGroup: __('Every body part'),
  groupLabel: __('Body part'),
  // the library DottorCloud ships keeps this name as its source, in the code only
  sources: [{ value: 'exercises-dataset', label: __('From the library') }],
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
</script>
