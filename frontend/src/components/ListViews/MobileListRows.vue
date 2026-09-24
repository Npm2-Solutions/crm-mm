<template>
  <div ref="scrollContainer" class="mx-3 h-full overflow-y-auto">
    <template v-for="group in groups" :key="group.group ?? '__ungrouped__'">
      <ListGroupHeader v-if="group.group !== undefined" :group="group">
        <div
          class="my-2 flex items-center gap-2 text-base-medium text-ink-gray-8"
        >
          <div>{{ __(group.label) }} -</div>
          <div class="flex items-center gap-1">
            <component :is="group.icon" v-if="group.icon" />
            <div v-if="group.group == ' '" class="text-ink-gray-4">
              {{ __('Empty') }}
            </div>
            <div v-else>{{ group.group }}</div>
          </div>
        </div>
      </ListGroupHeader>

      <template v-if="!group.collapsed">
        <component
          :is="routeFor(row) ? 'router-link' : 'div'"
          v-for="row in group.rows"
          :key="row[rowKey]"
          v-bind="routeFor(row) ? { to: routeFor(row) } : {}"
          class="flex gap-3 border-b border-outline-gray-1 py-3 last:border-b-0 active:bg-surface-gray-2"
          :class="{
            'opacity-50 pointer-events-none': row.disabled,
            'cursor-pointer': isTappable,
          }"
          @click="onRowClick(row, $event)"
        >
          <!-- A <button> cannot be nested inside the row's <a>.
               `@click.stop.prevent` on a plain wrapper is how frappe-ui's own
               ListRow keeps the checkbox from following the link. -->
          <div
            v-if="selectable"
            class="flex pt-0.5"
            @click.stop.prevent="toggle(row)"
          >
            <Checkbox
              :modelValue="isSelected(row)"
              :disabled="row.disabled"
              class="cursor-pointer"
            />
          </div>

          <div class="min-w-0 flex-1">
            <div class="flex items-start justify-between gap-3">
              <div
                v-if="titleColumn"
                class="min-w-0 flex-1 text-base-medium text-ink-gray-9"
              >
                <slot
                  v-bind="{
                    idx: titleColumn._idx,
                    column: titleColumn,
                    item: row[titleColumn.key],
                    row,
                  }"
                />
              </div>
              <div
                v-if="trailingColumn"
                class="shrink-0 text-sm text-ink-gray-5"
              >
                <slot
                  v-bind="{
                    idx: trailingColumn._idx,
                    column: trailingColumn,
                    item: row[trailingColumn.key],
                    row,
                  }"
                />
              </div>
            </div>

            <!-- Two labelled columns rather than one long strip: a bare value
                 like "12" or a date says nothing on its own once it is off the
                 table header it used to sit under. -->
            <dl
              v-if="detailColumns.length"
              class="mt-2 grid grid-cols-2 gap-x-3 gap-y-2"
            >
              <div v-for="column in detailColumns" :key="column.key">
                <dt class="truncate text-xs text-ink-gray-5">
                  {{ __(column.label) }}
                </dt>
                <dd class="mt-0.5 min-w-0 text-ink-gray-8">
                  <slot
                    v-bind="{
                      idx: column._idx,
                      column,
                      item: row[column.key],
                      row,
                    }"
                  />
                </dd>
              </div>
            </dl>
          </div>
        </component>
      </template>
    </template>
  </div>
</template>

<script setup>
/**
 * The phone-sized rendering of a list.
 *
 * The desktop list is a CSS grid whose columns carry fixed rem widths — the
 * default People list adds up to about 71rem, so on a 390px screen it is a
 * 1100px-wide table you have to drag sideways to read. This renders the same
 * rows as stacked cards instead.
 *
 * It takes the same props and exposes the same `{ idx, column, item, row }`
 * scoped slot as `ListRows.vue`, so each *ListView keeps one copy of its cell
 * renderers and only swaps which component lays them out.
 */
import { splitColumnsForCard } from '@/utils/mobileList'
import { useStorage } from '@vueuse/core'
import { Checkbox, ListGroupHeader } from 'frappe-ui'
import { ref, computed, watch, inject, onBeforeUnmount } from 'vue'

const props = defineProps({
  rows: { type: Array, required: true },
  doctype: { type: String, default: 'CRM Lead' },
})

const list = inject('list')

const rowKey = computed(() => list.value.rowKey)
const selectable = computed(() => list.value.options.selectable)

const cardColumns = computed(() => splitColumnsForCard(list.value.columns))

const titleColumn = computed(() => cardColumns.value.title)
const trailingColumn = computed(() => cardColumns.value.trailing)
const detailColumns = computed(() => cardColumns.value.details)

const isGrouped = computed(
  () =>
    props.rows.length > 0 &&
    props.rows.every((row) => row.group && Array.isArray(row.rows)),
)

// One shape for both cases, so the template does not branch.
const groups = computed(() =>
  isGrouped.value ? props.rows : [{ rows: props.rows }],
)

const isTappable = computed(
  () => !!(list.value.options.getRowRoute || list.value.options.onRowClick),
)

function routeFor(row) {
  const getRowRoute = list.value.options.getRowRoute
  if (!getRowRoute || row.disabled) return null
  return getRowRoute(row)
}

// Tasks and Call Logs open a modal rather than a page, so the card has to honour
// `onRowClick` the way frappe-ui's own row does.
function onRowClick(row, event) {
  if (row.disabled) return
  list.value.options.onRowClick?.(row, event)
}

function isSelected(row) {
  return list.value.selections.has(row[rowKey.value])
}

function toggle(row) {
  if (row.disabled) return
  list.value.toggleRow(row[rowKey.value])
}

const scrollPosition = useStorage(`scrollPosition${props.doctype}`, 0)
const scrollContainer = ref(null)

const handleScroll = (e) => {
  scrollPosition.value = e.target.scrollTop
}

let activeScrollEl = null

watch(
  scrollContainer,
  (el) => {
    if (el === activeScrollEl) return
    if (activeScrollEl) {
      activeScrollEl.removeEventListener('scroll', handleScroll)
    }
    activeScrollEl = el
    if (activeScrollEl) {
      activeScrollEl.addEventListener('scroll', handleScroll)
      activeScrollEl.scrollTop = scrollPosition.value
    }
  },
  { immediate: true, flush: 'post' },
)

onBeforeUnmount(() => {
  if (activeScrollEl) {
    activeScrollEl.removeEventListener('scroll', handleScroll)
  }
})
</script>
