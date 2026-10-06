<!--
  Modifications copyright (c) 2026, NPM2 Solutions Srl

  On a phone the open tasks come by when they are due, done with one tap
  (components/Mobile/ElencoCose.vue).
-->
<template>
  <LayoutHeader>
    <template #left-header>
      <ViewBreadcrumbs v-model="viewControls" routeName="Tasks" />
    </template>
    <template #right-header>
      <CustomActions
        v-if="tasksListView?.customListActions"
        :actions="tasksListView.customListActions"
      />
      <Button
        v-if="!isMobileView && !solaLettura()"
        variant="solid"
        :label="__('Create')"
        iconLeft="plus"
        @click="createTask"
      />
    </template>
  </LayoutHeader>
  <!-- on a phone: what is left, by when it is due, done with one tap -->
  <template v-if="isMobileView">
    <ElencoCose ref="elencoCose" @apri="showTask" />
    <PulsanteAggiungi
      v-if="!solaLettura()"
      :label="__('New task')"
      @click="createTask()"
    />
  </template>
  <ViewControls
    v-if="!isMobileView"
    ref="viewControls"
    v-model="tasks"
    v-model:loadMore="loadMore"
    v-model:resizeColumn="triggerResize"
    v-model:updatedPageCount="updatedPageCount"
    doctype="CRM Task"
    :options="{
      allowedViews: ['list', 'kanban'],
    }"
  />
  <KanbanView
    v-if="!isMobileView && $route.params.viewType == 'kanban' && rows.length"
    v-model="tasks"
    :options="{
      onClick: (row) => showTask(row.name),
      onNewClick: (column) => createTask(column),
    }"
    @update="(data) => viewControls.updateKanbanSettings(data)"
    @loadMore="(columnName) => viewControls.loadMoreKanban(columnName)"
  >
    <template #title="{ titleField, itemName }">
      <div class="flex items-center gap-2">
        <div v-if="titleField === 'status'">
          <TaskStatusIcon :status="getRow(itemName, titleField).label" />
        </div>
        <div v-else-if="titleField === 'priority'">
          <TaskPriorityIcon :priority="getRow(itemName, titleField).label" />
        </div>
        <div v-else-if="titleField === 'assigned_to'">
          <Avatar
            v-if="getRow(itemName, titleField).full_name"
            class="flex items-center"
            :image="getRow(itemName, titleField).user_image"
            :label="getRow(itemName, titleField).full_name"
            size="sm"
          />
        </div>
        <div
          v-if="['modified', 'creation'].includes(titleField)"
          class="truncate text-base"
        >
          <Tooltip :text="getRow(itemName, titleField).label">
            <div>{{ getRow(itemName, titleField).timeAgo }}</div>
          </Tooltip>
        </div>
        <div
          v-else-if="getRow(itemName, titleField).label"
          class="truncate text-base"
        >
          {{
            ['status', 'priority'].includes(titleField)
              ? __(getRow(itemName, titleField).label)
              : getRow(itemName, titleField).label
          }}
        </div>
        <div v-else class="text-ink-gray-5">{{ __('No Title') }}</div>
      </div>
    </template>
    <template #fields="{ fieldName, itemName }">
      <div
        v-if="getRow(itemName, fieldName).label"
        class="truncate flex items-center gap-2"
      >
        <div v-if="fieldName === 'status'">
          <TaskStatusIcon
            class="size-3"
            :status="getRow(itemName, fieldName).label"
          />
        </div>
        <div v-else-if="fieldName === 'priority'">
          <TaskPriorityIcon :priority="getRow(itemName, fieldName).label" />
        </div>
        <div v-else-if="fieldName === 'assigned_to'">
          <Avatar
            v-if="getRow(itemName, fieldName).full_name"
            class="flex items-center"
            :image="getRow(itemName, fieldName).user_image"
            :label="getRow(itemName, fieldName).full_name"
            size="sm"
          />
        </div>
        <div
          v-if="['modified', 'creation'].includes(fieldName)"
          class="truncate text-base"
        >
          <Tooltip :text="getRow(itemName, fieldName).label">
            <div>{{ getRow(itemName, fieldName).timeAgo }}</div>
          </Tooltip>
        </div>
        <!-- two lines and an ellipsis. The card holds every field in a
             `truncate` row, so the description inherited `nowrap` and ran on
             one line past the card's edge, cut mid-word: it wraps again here,
             and the clamp sits on this box, not on the prose (which is a
             `flow-root` block a clamp does not reach) -->
        <div
          v-else-if="fieldName == 'description'"
          class="line-clamp-2 min-w-0 whitespace-normal break-words text-base"
        >
          <!-- content is passed through sanitizeHTML() (DOMPurify) before rendering, so v-html is safe here -->
          <!-- eslint-disable vue/no-v-html -->
          <div
            v-if="getRow(itemName, fieldName).label"
            class="prose-f prose-sm max-w-none [&_p]:my-0"
            v-html="sanitizeHTML(getRow(itemName, fieldName).label)"
          />
          <!-- eslint-enable vue/no-v-html -->
        </div>
        <!-- a status or a priority is a value of a list: in the user's words -->
        <div v-else class="truncate text-base">
          {{
            ['status', 'priority'].includes(fieldName)
              ? __(getRow(itemName, fieldName).label)
              : getRow(itemName, fieldName).label
          }}
        </div>
      </div>
    </template>
    <template #actions="{ itemName }">
      <div class="flex gap-2 items-center justify-between">
        <div>
          <Button
            v-if="getRow(itemName, 'reference_docname').label"
            class="-ml-2"
            variant="ghost"
            size="sm"
            :label="
              getRow(itemName, 'reference_doctype').label == 'CRM Deal'
                ? __('Deal')
                : __('Lead')
            "
            :iconRight="ArrowUpRightIcon"
            @click.stop="
              redirect(
                getRow(itemName, 'reference_doctype').label,
                getRow(itemName, 'reference_docname').label,
              )
            "
          />
        </div>
        <Dropdown
          class="flex items-center gap-2"
          :options="actions(itemName)"
          variant="ghost"
        >
          <Button
            :aria-label="__('Options')"
            icon="lucide-more-horizontal"
            variant="ghost"
            @click.stop.prevent
          />
        </Dropdown>
      </div>
    </template>
  </KanbanView>
  <TasksListView
    v-else-if="!isMobileView && tasks.data && rows.length"
    ref="tasksListView"
    v-model="tasks.data.page_length_count"
    v-model:list="tasks"
    :rows="rows"
    :columns="columns"
    :options="{
      showTooltip: false,
      resizeColumn: true,
      rowCount: tasks.data.row_count,
      totalCount: tasks.data.total_count,
    }"
    @loadMore="() => loadMore++"
    @columnWidthUpdated="() => triggerResize++"
    @updatePageCount="(count) => (updatedPageCount = count)"
    @showTask="showTask"
    @applyFilter="(data) => viewControls.applyFilter(data)"
    @applyLikeFilter="(data) => viewControls.applyLikeFilter(data)"
    @likeDoc="(data) => viewControls.likeDoc(data)"
    @selectionsChanged="
      (selections) => viewControls.updateSelections(selections)
    "
  />
  <EmptyState
    v-else-if="!isMobileView && tasks.data && !rows.length"
    name="Tasks"
    :icon="Email2Icon"
  />
  <DeleteLinkedDocModal
    v-if="showDeleteTaskModal"
    v-model="showDeleteTaskModal"
    name="Tasks"
    doctype="CRM Task"
    :docname="taskToDelete"
    :reload="ricaricaLeCose"
  />
</template>

<script setup>
import ViewBreadcrumbs from '@/components/ViewBreadcrumbs.vue'
import CustomActions from '@/components/CustomActions.vue'
import ArrowUpRightIcon from '@/components/Icons/ArrowUpRightIcon.vue'
import TaskStatusIcon from '@/components/Icons/TaskStatusIcon.vue'
import TaskPriorityIcon from '@/components/Icons/TaskPriorityIcon.vue'
import Email2Icon from '@/components/Icons/Email2Icon.vue'
import LayoutHeader from '@/components/LayoutHeader.vue'
import ViewControls from '@/components/ViewControls.vue'
import TasksListView from '@/components/ListViews/TasksListView.vue'
import EmptyState from '@/components/ListViews/EmptyState.vue'
import KanbanView from '@/components/Kanban/KanbanView.vue'
import DeleteLinkedDocModal from '@/components/DeleteLinkedDocModal.vue'
import ElencoCose from '@/components/Mobile/ElencoCose.vue'
import PulsanteAggiungi from '@/components/Mobile/PulsanteAggiungi.vue'
import { isMobileView } from '@/composables/breakpoints'
import { useDoctypeModal } from '@/composables/doctypeModal'
import { getMeta } from '@/stores/meta'
import { usersStore } from '@/stores/users'
import { formatDate, sanitizeHTML } from '@/utils'
import { timestampCell } from '@/composables/useTimelinePreferences'
import { useTelemetry } from 'frappe-ui/frappe'
import { Tooltip, Avatar, Dropdown } from 'frappe-ui'
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'

const { getFormattedPercent, getFormattedFloat, getFormattedCurrency } =
  getMeta('CRM Task')
const { getUser, solaLettura } = usersStore()
const { capture } = useTelemetry()

const router = useRouter()

const tasksListView = ref(null)
const elencoCose = ref(null)

// tasks data is loaded in the ViewControls component
const tasks = ref({})
const loadMore = ref(1)
const triggerResize = ref(1)
const updatedPageCount = ref(20)
const viewControls = ref(null)

const showDeleteTaskModal = ref(false)
const taskToDelete = ref(null)

function getRow(name, field) {
  function getValue(value) {
    if (value && typeof value === 'object') {
      return value
    }
    return { label: value }
  }
  return getValue(rows.value?.find((row) => row.name == name)[field])
}

const rows = computed(() => {
  if (!tasks.value?.data?.data) return []

  if (tasks.value.data.view_type === 'kanban') {
    return getKanbanRows(tasks.value.data.data, tasks.value.data.fields)
  }

  openTaskFromURL()
  return parseRows(tasks.value?.data.data, tasks.value?.data.columns)
})

const columns = computed(() => {
  let _columns = tasks.value?.data?.columns || []

  // Set align right for last column
  if (_columns.length) {
    _columns = _columns.map((col, index) => {
      if (index === _columns.length - 1) {
        return { ...col, align: 'right' }
      }
      return col
    })
  }

  return _columns
})

function getKanbanRows(data, columns) {
  let _rows = []
  data.forEach((column) => {
    column.data?.forEach((row) => {
      _rows.push(row)
    })
  })
  return parseRows(_rows, columns)
}

function parseRows(rows, columns = []) {
  let view_type = tasks.value.data.view_type
  let key = view_type === 'kanban' ? 'fieldname' : 'key'
  let type = view_type === 'kanban' ? 'fieldtype' : 'type'

  return rows.map((task) => {
    let _rows = {}
    tasks.value?.data.rows.forEach((row) => {
      _rows[row] = task[row]

      let fieldType = columns?.find((col) => (col[key] || col.value) == row)?.[
        type
      ]

      if (
        fieldType &&
        ['Date', 'Datetime'].includes(fieldType) &&
        !['modified', 'creation', 'due_date'].includes(row)
      ) {
        _rows[row] = formatDate(task[row], '', true, fieldType == 'Datetime')
      }

      if (fieldType && fieldType == 'Currency') {
        _rows[row] = getFormattedCurrency(row, task)
      }

      if (fieldType && fieldType == 'Float') {
        _rows[row] = getFormattedFloat(row, task)
      }

      if (fieldType && fieldType == 'Percent') {
        _rows[row] = getFormattedPercent(row, task)
      }

      if (['modified', 'creation'].includes(row)) {
        _rows[row] = timestampCell(task[row])
      } else if (row == 'assigned_to') {
        _rows[row] = {
          label: task.assigned_to && getUser(task.assigned_to).full_name,
          ...(task.assigned_to && getUser(task.assigned_to)),
        }
      }
    })
    return _rows
  })
}

const { showModal } = useDoctypeModal()

// the list the page shows: the desk's, or the phone's
function ricaricaLeCose() {
  if (isMobileView.value) elencoCose.value?.ricarica()
  else tasks.value.reload()
}

const taskCallbacks = {
  afterInsert: () => {
    ricaricaLeCose()
    capture('task_created')
  },
  afterUpdate: () => {
    ricaricaLeCose()
    capture('task_updated')
  },
  // the sheet's «Delete»: on a phone the list has no menu of its own
  afterDelete: () => ricaricaLeCose(),
}

function showTask(name) {
  showModal({
    name,
    doctype: 'CRM Task',
    title: 'Task',
    callbacks: taskCallbacks,
  })
}

function createTask(column) {
  // one's own unless given to somebody else in the sheet: made without anyone,
  // it was nobody's, and «Mine» stayed empty as if it had not been saved
  const defaults = {
    status: 'Todo',
    priority: 'Low',
    assigned_to: getUser().name,
  }

  if (column?.column?.name) {
    let column_field = tasks.value.params.column_field
    if (column_field) {
      defaults[column_field] = column.column.name
    }
  }

  showModal({
    doctype: 'CRM Task',
    title: 'Task',
    defaults: defaults,
    callbacks: taskCallbacks,
  })
}

function actions(name) {
  return [
    {
      label: __('Edit'),
      icon: 'edit-2',
      onClick: () => showTask(name),
    },
    {
      label: __('Delete'),
      icon: 'trash-2',
      onClick: () => {
        taskToDelete.value = name
        showDeleteTaskModal.value = true
      },
    },
  ]
}

function redirect(doctype, docname) {
  if (!docname) return
  let name = doctype == 'CRM Deal' ? 'Deal' : 'Lead'
  let params = { leadId: docname }
  if (name == 'Deal') {
    params = { dealId: docname }
  }
  router.push({ name: name, params: params })
}

const openTaskFromURL = () => {
  const searchParams = new URLSearchParams(window.location.search)
  const taskName = searchParams.get('open')

  if (taskName && rows.value?.length) {
    showTask(parseInt(taskName))
    searchParams.delete('open')
    window.history.replaceState(null, '', window.location.pathname)
  }
}
</script>
