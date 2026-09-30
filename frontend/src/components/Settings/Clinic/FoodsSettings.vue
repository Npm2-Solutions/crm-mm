<!--
  The clinic's foods, the library its diets are written with. A food table comes
  in from a file (CIQUAL, BDA-IEO with the licence, CREA with the permission);
  here a name becomes the centre's own, a group is put right, a food is switched
  off. Imported again, a table brings its numbers, never over the centre's words.
  The page is the CRM's library page (Settings/Plans/LibraryPage.vue).
-->
<template>
  <LibraryPage
    :library="library"
    @edit="(row) => Object.assign(editing, { show: true, row })"
    @import="importing = true"
  >
    <template #dialogs="{ reload }">
      <FoodEditDialog
        v-model="editing.show"
        :food="editing.row"
        @saved="reload"
      />
      <FoodImportDialog v-model="importing" @imported="reload" />
    </template>
  </LibraryPage>
</template>

<script setup>
import FoodEditDialog from '@/components/Settings/Clinic/FoodEditDialog.vue'
import FoodImportDialog from '@/components/Settings/Clinic/FoodImportDialog.vue'
import LibraryPage from '@/components/Settings/Plans/LibraryPage.vue'
import { FONTI } from '@/utils/librerie'
import { GRUPPI } from '@/utils/piani'
import { reactive, ref } from 'vue'

const editing = reactive({ show: false, row: null })
const importing = ref(false)

const library = {
  title: __('Foods'),
  description: __(
    'The foods diets are written with. The numbers come from the tables; the names and groups are the centre’s.',
  ),
  endpoint: 'crm.clinica.librerie.get_foods',
  nameField: 'food_name',
  groups: GRUPPI,
  everyGroup: __('Every group'),
  groupLabel: __('Group'),
  sources: FONTI,
  searchPlaceholder: __('Search a food'),
  importLabel: __('Import a table'),
  empty: __('No foods yet: import a table, or add them while writing a plan.'),
  describe: (row) => {
    const parts = [__(row.food_group)]
    if (row.kcal !== null && row.kcal !== undefined)
      parts.push(__('{0} kcal/100 g', [row.kcal]))
    if (row.name_in_source && row.name_in_source !== row.food_name)
      parts.push(row.name_in_source)
    return parts.join(' · ')
  },
}
</script>
