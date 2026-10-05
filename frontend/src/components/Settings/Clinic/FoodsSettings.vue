<!--
  Copyright (c) 2026, NPM2 Solutions Srl and contributors
  For license information, please see license.txt

  The clinic's foods, the library its diets are written with: the library
  DottorCloud ships, all there on every site with its names in Italian
  (`crm.clinica.librerie.carica_libreria`), and the centre's own. The centre
  switches off the foods it does not use and adds its own; it changes nothing of
  the library's, and never imports a table: NPM2 adds to the library in the
  code. The page is the CRM's library page (Settings/Plans/LibraryPage.vue).
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
    <template #dialogs="{ reload, aggiorna }">
      <FoodEditDialog
        v-model="editing.show"
        :food="editing.row"
        @saved="reload"
        @changed="aggiorna"
      />
    </template>
  </LibraryPage>
</template>

<script setup>
import FoodEditDialog from '@/components/Settings/Clinic/FoodEditDialog.vue'
import LibraryPage from '@/components/Settings/Plans/LibraryPage.vue'
import { FONTI, numeroDelCibo } from '@/utils/librerie'
import { appLocale } from '@/utils/locale'
import { GRUPPI } from '@/utils/piani'
import { reactive } from 'vue'

const editing = reactive({ show: false, row: null })
const lingua = appLocale() || 'it'

const library = {
  title: __('Foods'),
  description: __(
    'The foods diets are written with: the {brand} library, all there already with its values for 100 g, and the ones the centre adds. Switch off the ones the centre does not use: they are no longer offered.',
  ),
  endpoint: 'crm.clinica.librerie.get_foods',
  switchEndpoint: 'crm.clinica.librerie.switch_food',
  nameField: 'food_name',
  groups: GRUPPI,
  everyGroup: __('Every group'),
  groupLabel: __('Group'),
  sources: FONTI.map((fonte) =>
    fonte === 'CIQUAL'
      ? { value: fonte, label: __('From the library') }
      : fonte,
  ),
  searchPlaceholder: __('Search a food'),
  newLabel: __('New food'),
  empty: __('No foods yet: add the centre’s own with New food.'),
  // its group and energy, in the reader's numbers; the table's own name (in
  // CIQUAL's English) is in the food's window, not in the row
  describe: (row) => {
    const parts = [__(row.food_group)]
    if (row.kcal !== null && row.kcal !== undefined)
      parts.push(__('{0} kcal/100 g', [numeroDelCibo(row.kcal, lingua)]))
    return parts.join(' · ')
  },
}
</script>
