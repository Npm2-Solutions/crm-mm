<!--
  Modifications copyright (c) 2026, NPM2 Solutions Srl
-->
<template>
  <ListView
    ref="listViewRef"
    :class="$attrs.class"
    :columns="columns"
    :rows="rows"
    :options="{
      selectable: true,
      showTooltip: true,
      resizeColumn: true,
    }"
    row-key="reference_docname"
    @update:selections="(selections) => emit('selectionsChanged', selections)"
  >
    <ListHeader @columnWidthUpdated="emit('columnWidthUpdated')">
      <ListHeaderItem
        v-for="column in columns"
        :key="column.key"
        :item="column"
        @columnWidthUpdated="(e) => onColumnWidthUpdated(e, column)"
      >
      </ListHeaderItem>
    </ListHeader>
    <div class="*:mx-0 *:sm:mx-0">
      <ListRows v-slot="{ column, item, row }" :rows="rows">
        <ListRowItem
          :item="item"
          class="!w-full"
          @click="listViewRef.toggleRow(row['reference_docname'])"
        >
          <template #default="{ label }">
            <div
              v-if="column.key === 'title'"
              class="truncate text-base flex gap-2 w-full"
            >
              <span class="min-w-0 max-w-[90%]">
                <span class="block truncate">{{ label }}</span>
                <!-- on a phone the kind has no column of its own: under the name -->
                <span
                  v-if="isMobileView"
                  class="block truncate text-sm text-ink-gray-6"
                >
                  {{ __(row.reference_doctype) }}
                </span>
              </span>
              <!-- only where it has a page of its own (utils/collegati.js) -->
              <button
                v-if="indirizzoDelCollegato(row)"
                type="button"
                class="touch-target shrink-0 rounded text-ink-gray-6 hover:text-ink-gray-8"
                :aria-label="__('Open {0} in a new tab', [label])"
                @click.stop="viewLinkedDoc(row)"
              >
                <span
                  class="lucide-external-link block h-4 w-4"
                  aria-hidden="true"
                />
              </button>
            </div>
            <!-- what it is, in the reader's language: «Trattativa», not «Deal» -->
            <span
              v-if="column.key === 'reference_doctype'"
              class="truncate text-base flex gap-2"
            >
              {{ __(row.reference_doctype) }}
            </span>
          </template>
        </ListRowItem>
      </ListRows>
    </div>
  </ListView>
</template>

<script setup>
import ListRows from '@/components/ListViews/ListRows.vue'
import { isMobileView } from '@/composables/settings'
import { indirizzoDelCollegato } from '@/utils/collegati'
import { ListView, ListHeader, ListHeaderItem, ListRowItem } from 'frappe-ui'
import { ref } from 'vue'

defineProps({
  rows: { type: Array, required: true },
  columns: { type: Array, required: true },
  linkedDocsResource: { type: Object, required: true },
  unlinkLinkedDoc: { type: Function, required: true },
  options: {
    type: Object,
    default: () => ({
      selectable: true,
      showTooltip: true,
      resizeColumn: false,
      totalCount: 0,
      rowCount: 0,
    }),
  },
})
const emit = defineEmits([
  'loadMore',
  'updatePageCount',
  'columnWidthUpdated',
  'applyFilter',
  'applyLikeFilter',
  'likeDoc',
  'selectionsChanged',
])

const listViewRef = ref(null)

function onColumnWidthUpdated({ width, save }, column) {
  column.width = width
  if (save) emit('columnWidthUpdated', column)
}

const viewLinkedDoc = (doc) => {
  const indirizzo = indirizzoDelCollegato(doc)
  if (indirizzo) window.open(indirizzo)
}
</script>
