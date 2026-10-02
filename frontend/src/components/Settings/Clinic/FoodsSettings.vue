<!--
  The clinic's foods, the library its diets are written with: the library
  DottorCloud ships, ready on every site with its names in Italian
  (`crm.clinica.librerie.carica_libreria`), and the centre's own. Here a name
  becomes the centre's, a group is put right, a food is switched off or added.
  The centre never imports a table: NPM2 adds to the library in the code.
  The page is the CRM's library page (Settings/Plans/LibraryPage.vue).
-->
<template>
  <LibraryPage
    :library="library"
    @edit="(row) => Object.assign(editing, { show: true, row })"
    @new="Object.assign(editing, { show: true, row: null })"
  >
    <template #after="{ data }">
      <p v-if="data?.sources?.CIQUAL" class="px-2 text-p-xs text-ink-gray-5">
        {{
          __(
            'Values of the library: Anses. 2025. Ciqual French food composition table.',
          )
        }}
      </p>
    </template>
    <template #dialogs="{ reload }">
      <FoodEditDialog
        v-model="editing.show"
        :food="editing.row"
        @saved="reload"
      />
    </template>
  </LibraryPage>
</template>

<script setup>
import FoodEditDialog from '@/components/Settings/Clinic/FoodEditDialog.vue'
import LibraryPage from '@/components/Settings/Plans/LibraryPage.vue'
import { FONTI } from '@/utils/librerie'
import { GRUPPI } from '@/utils/piani'
import { reactive } from 'vue'

const editing = reactive({ show: false, row: null })

const library = {
  title: __('Foods'),
  description: __(
    'The foods diets are written with: the {brand} library, ready to use with its values for 100 g, and the centre’s own. Names and groups can be put in the centre’s words.',
  ),
  endpoint: 'crm.clinica.librerie.get_foods',
  nameField: 'food_name',
  groups: GRUPPI,
  everyGroup: __('Every group'),
  groupLabel: __('Group'),
  sources: FONTI.map((fonte) =>
    fonte === 'CIQUAL' ? { value: fonte, label: __('Library') } : fonte,
  ),
  searchPlaceholder: __('Search a food'),
  newLabel: __('New food'),
  empty: __('No foods yet: add the centre’s own with New food.'),
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
