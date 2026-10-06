<!--
  Modifications copyright (c) 2026, NPM2 Solutions Srl
-->
<template>
  <Button
    :label="__('Kanban settings')"
    v-bind="$attrs"
    :iconLeft="KanbanIcon"
    @click="
      () => {
        carica()
        showDialog = true
      }
    "
  />
  <Dialog v-model:open="showDialog" :title="__('Kanban Settings')">
    <template #default>
      <div>
        <div class="text-base text-ink-gray-5 mb-2">
          {{ __('Column Field') }}
        </div>
        <Combobox
          v-if="columnFields"
          :model-value="null"
          :options="columnFields"
          @update:selected-option="(f) => (columnField = f)"
        >
          <template #trigger="{ open, setOpen }">
            <!-- a plain button did not look like something to pick from -->
            <Button
              class="w-full !justify-between"
              :label="columnField?.label"
              iconRight="chevron-down"
              @click="setOpen(!open)"
            />
          </template>
        </Combobox>
        <div class="text-base text-ink-gray-5 mb-2 mt-4">
          {{ __('Title Field') }}
        </div>
        <Combobox
          :model-value="null"
          :options="tutti"
          @update:selected-option="(f) => (titleField = f)"
        >
          <template #trigger="{ open, setOpen }">
            <!-- a plain button did not look like something to pick from -->
            <Button
              class="w-full !justify-between"
              :label="titleField?.label"
              iconRight="chevron-down"
              @click="setOpen(!open)"
            />
          </template>
        </Combobox>
      </div>
      <div class="mt-4">
        <div class="text-base text-ink-gray-5 mb-2">
          {{ __('Fields Order') }}
        </div>
        <!-- on a touch screen a row moves after a short press: a swipe
             scrolls the list -->
        <Draggable
          :list="allFields"
          :delay="200"
          :delay-on-touch-only="true"
          group="fields"
          item-key="name"
          class="flex flex-col gap-1"
          @end="reorder"
        >
          <template #item="{ element: field }">
            <div
              class="px-1 py-0.5 border border-outline-elevation-2 rounded text-base text-ink-gray-8 flex items-center justify-between gap-2"
            >
              <div class="flex items-center gap-2">
                <DragVerticalIcon class="h-3.5 cursor-grab" />
                <div>{{ field.label }}</div>
              </div>
              <div>
                <Button
                  :aria-label="__('Remove')"
                  variant="ghost"
                  icon="lucide-x"
                  @click="removeField(field)"
                />
              </div>
            </div>
          </template>
        </Draggable>
        <Combobox
          :model-value="null"
          :options="fields"
          @update:selected-option="(e) => addField(e)"
        >
          <template #trigger="{ open, setOpen }">
            <Button
              class="w-full mt-2"
              :label="__('Add Field')"
              iconLeft="plus"
              @click="setOpen(!open)"
            />
          </template>
        </Combobox>
      </div>
    </template>
    <template #actions>
      <Button
        class="w-full"
        variant="solid"
        :label="__('Apply')"
        :loading="campi.loading"
        @click="apply"
      />
    </template>
  </Dialog>
</template>
<script setup>
import DragVerticalIcon from '@/components/Icons/DragVerticalIcon.vue'
import KanbanIcon from '@/components/Icons/KanbanIcon.vue'
import { useCampiDellaLista } from '@/composables/campiDellaLista'
import { Combobox, Dialog } from 'frappe-ui'
import Draggable from 'vuedraggable'
import { ref, computed, nextTick } from 'vue'

const props = defineProps({
  doctype: {
    type: String,
    required: true,
  },
})

const emit = defineEmits(['update'])

const list = defineModel({ type: Object })
const showDialog = ref(false)

// what the list offers on a card, in the reader's words, each field once
const { campi, carica } = useCampiDellaLista(props.doctype)

const tutti = computed(() =>
  (campi.data || []).map((field) => ({
    label: field.label,
    value: field.fieldname,
    fieldname: field.fieldname,
    fieldtype: field.fieldtype,
  })),
)

const columnField = computed({
  get: () => {
    let fieldname = list.value?.data?.column_field
    if (!fieldname) return null

    return columnFields.value.find((field) => field.fieldname === fieldname)
  },
  set: (val) => {
    list.value.data.column_field = val.fieldname
  },
})

const titleField = computed({
  get: () => {
    let fieldname = list.value?.data?.title_field
    if (!fieldname) return null

    return tutti.value.find((field) => field.fieldname === fieldname)
  },
  set: (val) => {
    list.value.data.title_field = val.fieldname
  },
})

const columnFields = computed(() =>
  tutti.value.filter((field) => ['Link', 'Select'].includes(field.fieldtype)),
)

// the fields on the card, in their order
const allFields = computed({
  get: () => {
    let rows = list.value?.data?.kanban_fields
    if (!rows) return []

    if (typeof rows === 'string') {
      rows = JSON.parse(rows)
    }

    return rows
      .map((row) => tutti.value.find((field) => field.fieldname === row))
      .filter(Boolean)
  },
  set: (val) => {
    list.value.data.kanban_fields = val
  },
})

// the ones still to add: the card's own are not offered again
const fields = computed(() => {
  const sullaScheda = new Set(allFields.value.map((field) => field.fieldname))
  return tutti.value.filter((field) => !sullaScheda.has(field.fieldname))
})

function reorder() {
  allFields.value = allFields.value.map((row) => row.fieldname)
}

function addField(field) {
  if (!field) return
  let rows = allFields.value || []
  rows.push(field)
  allFields.value = rows.map((row) => row.fieldname)
}

function removeField(field) {
  let rows = allFields.value
  rows = rows.filter((row) => row.fieldname !== field.fieldname)
  allFields.value = rows.map((row) => row.fieldname)
}

function apply() {
  // until the list's fields arrive there is nothing to name
  if (!campi.data) return
  nextTick(() => {
    showDialog.value = false
    emit('update', {
      column_field: columnField.value?.fieldname,
      title_field: titleField.value?.fieldname,
      kanban_fields: allFields.value.map((row) => row.fieldname),
    })
  })
}
</script>
