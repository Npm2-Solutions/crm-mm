<template>
  <div class="flex h-full flex-col overflow-hidden">
    <LayoutHeader>
      <template #left-header>
        <div class="flex min-w-0 items-center">
          <router-link
            :to="{ name: 'Dashboard' }"
            class="hidden px-0.5 py-1 text-lg-medium text-ink-gray-5 hover:text-ink-gray-7 focus:outline-none focus-visible:ring-2 focus-visible:ring-outline-gray-3 sm:block"
          >
            {{ __('Dashboard') }}
          </router-link>
          <span
            class="mx-0.5 hidden text-base text-ink-gray-4 sm:inline"
            aria-hidden="true"
          >
            /
          </span>
          <Dropdown :options="switcherOptions">
            <template #default="{ open }">
              <Button
                variant="ghost"
                class="text-lg-medium text-nowrap"
                :label="current?.title || __('Dashboard')"
                :iconRight="open ? 'chevron-up' : 'chevron-down'"
              >
                <template #prefix>
                  <Icon
                    :icon="current?.icon || 'layout-dashboard'"
                    class="size-4"
                  />
                </template>
              </Button>
            </template>
            <template #item-suffix="{ item }">
              <span
                v-if="item.key && item.key === current?.name"
                class="lucide-check size-4 text-ink-gray-7"
                aria-hidden="true"
              />
            </template>
          </Dropdown>
        </div>
      </template>
      <template #right-header>
        <template v-if="!editing">
          <Tooltip :text="__('Refresh')">
            <Button
              :aria-label="__('Refresh')"
              :loading="refreshing"
              @click="loadAnswers()"
            >
              <template #icon>
                <LucideRefreshCcw class="size-4" />
              </template>
            </Button>
          </Tooltip>
          <Button
            v-if="current?.can_edit && !isMobileView"
            :label="__('Edit')"
            :iconLeft="LucidePenLine"
            @click="startEditing"
          />
          <Dropdown :options="moreOptions" align="end">
            <template #default>
              <Button :aria-label="__('More')">
                <template #icon>
                  <LucideEllipsis class="size-4" />
                </template>
              </Button>
            </template>
          </Dropdown>
        </template>
        <template v-else>
          <Button
            :label="showLibrary ? __('Hide widgets') : __('Add widgets')"
            :iconLeft="LucidePanelRight"
            @click="showLibrary = !showLibrary"
          />
          <Button :label="__('Cancel')" @click="cancelEditing" />
          <Button
            variant="solid"
            :label="__('Save')"
            :loading="saving"
            @click="save"
          />
        </template>
      </template>
    </LayoutHeader>

    <div
      class="flex flex-wrap items-center gap-2 border-b border-outline-gray-1 px-3 py-2.5 sm:px-5"
    >
      <PeriodPicker
        v-model:period="period"
        v-model:range="range"
        :locale="locale"
      />
      <Link
        v-if="canFilterPeople"
        class="form-control w-full sm:w-48"
        variant="outline"
        :value="userFilter && getUser(userFilter).full_name"
        doctype="User"
        :filters="{
          name: ['in', users.data?.crmUsers?.map((u) => u.name) || []],
          ignore_user_type: 1,
        }"
        :placeholder="__('Whole team')"
        :hideMe="true"
        @change="(value) => (userFilter = value || null)"
      >
        <template #prefix>
          <UserAvatar
            v-if="userFilter"
            class="mr-2"
            :user="userFilter"
            size="sm"
          />
          <LucideUsers v-else class="mr-2 size-4 text-ink-gray-5" />
        </template>
        <template #item-prefix="{ option }">
          <UserAvatar class="mr-2" :user="option.value" size="sm" />
        </template>
        <template #item-label="{ option }">
          <div class="text-ink-gray-9">
            {{ getUser(option.value).full_name }}
          </div>
        </template>
      </Link>
      <div
        class="flex min-w-0 flex-1 items-center justify-end gap-3 text-xs text-ink-gray-5"
      >
        <span v-if="editing && current?.managed" class="truncate">
          {{
            __(
              'This dashboard follows its template. Saving makes this arrangement its own.',
            )
          }}
        </span>
        <span v-else-if="editing" class="hidden truncate md:inline">
          {{ __('Drag to move, pull the corner to resize') }}
        </span>
        <span
          v-if="current?.only_mine && !editing"
          class="inline-flex items-center gap-1"
        >
          <LucideUserRound class="size-3.5" />
          {{ __('Only your work') }}
        </span>
        <span v-if="updatedAt && !editing" class="hidden sm:inline">
          {{ __('Updated {0}', [updatedAtLabel]) }}
        </span>
      </div>
    </div>

    <div ref="area" class="relative flex min-h-0 flex-1">
      <div ref="scroller" class="min-w-0 flex-1 overflow-y-auto">
        <div
          v-if="loadingLayout && !items.length"
          class="grid grid-cols-2 gap-4 p-5 lg:grid-cols-5"
        >
          <div
            v-for="index in 10"
            :key="index"
            class="h-28 animate-pulse rounded-xl bg-surface-gray-1"
            :class="index > 5 ? 'col-span-2 h-72 lg:col-span-5' : ''"
          />
        </div>

        <div
          v-else-if="!items.length && current"
          class="flex h-full flex-col items-center justify-center gap-3 px-6 py-16 text-center"
        >
          <span
            class="grid size-12 place-items-center rounded-full bg-surface-gray-2"
          >
            <LucideLayoutDashboard class="size-5 text-ink-gray-6" />
          </span>
          <div class="text-base font-medium text-ink-gray-8">
            {{ __('This dashboard is empty') }}
          </div>
          <div class="max-w-sm text-p-sm text-ink-gray-5">
            {{
              __(
                'Pick the numbers you want to keep an eye on from the widget library.',
              )
            }}
          </div>
          <div class="flex gap-2">
            <Button
              v-if="current.can_edit && !isMobileView && !editing"
              variant="solid"
              :label="__('Add widgets')"
              iconLeft="plus"
              @click="startEditing"
            />
            <Button
              v-if="current.can_edit && current.template && !current.managed"
              :label="__('Back to the template')"
              @click="resetToTemplate"
            />
          </div>
        </div>

        <DashboardGrid
          v-else
          v-model="items"
          :answers="answers"
          :editing="editing"
          :refreshing="refreshing"
          :userFiltered="Boolean(userFilter)"
          :onlyMine="Boolean(current?.only_mine)"
          :locale="locale"
          :highlighted="highlighted"
          :configurable="configurable"
          @navigate="navigate"
          @setup="setUp"
          @configure="configure"
          @duplicate="duplicate"
          @remove="remove"
        />
      </div>

      <WidgetLibrary
        v-if="editing && showLibrary"
        :class="
          libraryFloats ? 'absolute inset-y-0 right-0 z-20 shadow-2xl' : ''
        "
        :catalog="catalog.data || undefined"
        :loading="catalog.loading"
        :items="items"
        :canSetUp="isManager()"
        @add="add"
        @setup="setUp"
        @close="showLibrary = false"
      />
    </div>
  </div>

  <WidgetConfigDialog
    v-model="showConfig"
    :item="configItem"
    :widget="configWidget"
    @apply="applyConfig"
  />
  <DashboardDialog
    v-model="showDashboardDialog"
    :mode="dashboardDialogMode"
    :dashboard="current"
    :templates="catalog.data?.templates || []"
    :canShare="Boolean(dashboards.data?.can_share)"
    @saved="onDashboardSaved"
  />
</template>

<script setup>
import LucideRefreshCcw from '~icons/lucide/refresh-ccw'
import LucidePenLine from '~icons/lucide/pen-line'
import LucideEllipsis from '~icons/lucide/ellipsis'
import LucidePanelRight from '~icons/lucide/panel-right'
import LucideUsers from '~icons/lucide/users'
import LucideUserRound from '~icons/lucide/user-round'
import LucideLayoutDashboard from '~icons/lucide/layout-dashboard'
import Icon from '@/components/Icon.vue'
import LayoutHeader from '@/components/LayoutHeader.vue'
import UserAvatar from '@/components/UserAvatar.vue'
import Link from '@/components/Controls/Link.vue'
import DashboardGrid from '@/components/Dashboard/DashboardGrid.vue'
import DashboardDialog from '@/components/Dashboard/DashboardDialog.vue'
import PeriodPicker from '@/components/Dashboard/PeriodPicker.vue'
import WidgetConfigDialog from '@/components/Dashboard/WidgetConfigDialog.vue'
import WidgetLibrary from '@/components/Dashboard/WidgetLibrary.vue'
import { isStructural, layoutWidgets } from '@/components/Dashboard/meta'
import { isMobileView } from '@/composables/breakpoints'
import { activeSettingsPage, showSettings } from '@/composables/settings'
import { globalStore } from '@/stores/global'
import { usersStore } from '@/stores/users'
import {
  DEFAULT_PERIOD,
  duplicateItem,
  newItem,
  periodRange,
  toSavedLayout,
} from '@/utils/dashboard'
import { timeAgo } from '@/utils'
import {
  call,
  createResource,
  Dropdown,
  toast,
  Tooltip,
  usePageMeta,
} from 'frappe-ui'
import { useElementSize, useIntervalFn, useNow } from '@vueuse/core'
import { computed, h, markRaw, nextTick, reactive, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'

const LAST_OPENED = 'crm_dashboard_last'
// a dashboard left open on a screen stays current without anyone touching it
const AUTO_REFRESH = 5 * 60 * 1000

const route = useRoute()
const router = useRouter()
const { users, getUser, isManager, isAdmin } = usersStore()
const { $dialog } = globalStore()

// numbers and dates in the reader's own locale, as the rest of the app does
const locale = undefined

const current = ref(null)
const items = ref([])
const answers = reactive({})
const loadingLayout = ref(false)
const refreshing = ref(false)
const updatedAt = ref(null)
const scroller = ref(null)
const area = ref(null)

const period = ref(DEFAULT_PERIOD)
const range = ref(periodRange(DEFAULT_PERIOD))
const userFilter = ref(null)
// what the numbers are asked for, as one comparable value: a new array with
// the same dates is not a new question
const filters = computed(() =>
  JSON.stringify([range.value?.[0], range.value?.[1], userFilter.value]),
)

const editing = ref(false)
const saving = ref(false)
const showLibrary = ref(true)
const highlighted = ref('')
let draft = null

const showConfig = ref(false)
const configItem = ref(null)
const configWidget = ref(null)

const showDashboardDialog = ref(false)
const dashboardDialogMode = ref('create')

const dashboards = createResource({
  url: 'crm.api.dashboard.get_dashboards',
  auto: true,
  onSuccess: () => {
    if (!current.value) openInitial()
  },
})

const catalog = createResource({
  url: 'crm.api.dashboard.get_widget_catalog',
  cache: 'crm-dashboard-catalog',
})

const list = computed(() => dashboards.data?.dashboards || [])

const canFilterPeople = computed(
  () => (isManager() || isAdmin()) && !current.value?.only_mine,
)

// the library sits beside the grid when both fit, over it when sharing the
// width would squeeze every widget to a sliver (a 1366px laptop)
const { width: areaWidth } = useElementSize(area)
const libraryFloats = computed(
  () => areaWidth.value > 0 && areaWidth.value < 1150,
)

// ticks so "Updated 3 m ago" stays true between refreshes
const clock = useNow({ interval: 30 * 1000 })
const updatedAtLabel = computed(() =>
  clock.value && updatedAt.value ? timeAgo(updatedAt.value) : '',
)

function iconOf(name) {
  return markRaw({
    render: () => h(Icon, { icon: name || 'layout-dashboard' }),
  })
}

const switcherOptions = computed(() => {
  const entry = (dashboard) => ({
    key: dashboard.name,
    label: dashboard.title,
    icon: iconOf(dashboard.icon),
    onClick: () => openDashboard(dashboard.name),
  })
  // a template the site cannot answer yet stays out of the way
  const shown = list.value.filter(
    (dashboard) =>
      dashboard.available || dashboard.name === current.value?.name,
  )
  const shared = shown.filter((dashboard) => !dashboard.private)
  const mine = shown.filter((dashboard) => dashboard.private)
  const groups = []
  if (shared.length)
    groups.push({ group: __('Team'), items: shared.map(entry) })
  if (mine.length) groups.push({ group: __('Mine'), items: mine.map(entry) })
  groups.push({
    group: '',
    hideLabel: true,
    items: [
      {
        label: __('New dashboard'),
        icon: iconOf('plus'),
        onClick: () => openDashboardDialog('create'),
      },
    ],
  })
  return groups
})

const moreOptions = computed(() => {
  const dashboard = current.value
  const options = [
    {
      label: __('New dashboard'),
      icon: iconOf('plus'),
      onClick: () => openDashboardDialog('create'),
    },
  ]
  if (!dashboard) return options
  options.push({
    label: dashboard.can_edit ? __('Duplicate') : __('Duplicate for me'),
    icon: iconOf('copy'),
    onClick: duplicateDashboard,
  })
  if (dashboard.can_edit) {
    options.push({
      label: __('Dashboard settings'),
      icon: iconOf('settings-2'),
      onClick: () => openDashboardDialog('settings'),
    })
    if (dashboard.template && !dashboard.managed) {
      options.push({
        label: __('Back to the template'),
        icon: iconOf('undo-2'),
        onClick: resetToTemplate,
      })
    }
    options.push({
      label: __('Delete'),
      icon: iconOf('trash-2'),
      theme: 'red',
      onClick: deleteDashboard,
    })
  }
  return options
})

// -- opening a dashboard ---------------------------------------------------------

function openInitial() {
  const wanted = route.query.d || safeStorage('get')
  const found =
    list.value.find((dashboard) => dashboard.name === wanted) ||
    list.value.find((dashboard) => dashboard.available) ||
    list.value[0]
  if (found) openDashboard(found.name, { replace: true })
}

async function openDashboard(name, { replace = false } = {}) {
  if (editing.value && changed()) {
    $dialog({
      title: __('Discard your changes?'),
      message: __('The widgets you moved, added or removed will not be saved.'),
      actions: [
        {
          label: __('Discard'),
          variant: 'solid',
          theme: 'red',
          onClick: (close) => {
            close()
            draft = null
            editing.value = false
            openDashboard(name, { replace })
          },
        },
      ],
    })
    return
  }
  editing.value = false
  loadingLayout.value = true
  if (route.query.d !== name) {
    router[replace ? 'replace' : 'push']({
      name: 'Dashboard',
      query: { ...route.query, d: name },
    })
  }
  safeStorage('set', name)
  try {
    const data = await call('crm.api.dashboard.get_dashboard_layout', { name })
    current.value = data
    items.value = data.layout || []
    for (const key of Object.keys(answers)) delete answers[key]
    const asked = filters.value
    // each dashboard opens on its own period: "my day" on today
    period.value = data.period || DEFAULT_PERIOD
    range.value = periodRange(period.value)
    if (data.only_mine) userFilter.value = null
    // new filters reload through their watcher; the same ones need asking here
    if (filters.value === asked) await loadAnswers()
  } catch (error) {
    toast.error(error?.messages?.[0] || __('Could not open the dashboard'))
    current.value = null
    items.value = []
  } finally {
    loadingLayout.value = false
  }
}

watch(
  () => route.query.d,
  (name) => {
    if (name && current.value && name !== current.value.name)
      openDashboard(name)
  },
)

function safeStorage(action, value) {
  try {
    if (action === 'get') return localStorage.getItem(LAST_OPENED)
    localStorage.setItem(LAST_OPENED, value)
  } catch {
    return null
  }
}

// -- the numbers -------------------------------------------------------------------

let request = 0

function asked(item) {
  return { i: item.layout.i, name: item.name, config: item.config || {} }
}

async function fetchAnswers(targets) {
  return call('crm.api.dashboard.get_widgets_data', {
    widgets: JSON.stringify(targets.map(asked)),
    from_date: range.value[0],
    to_date: range.value[1],
    user: userFilter.value,
    only_mine: current.value?.only_mine ? 1 : 0,
  })
}

async function loadAnswers() {
  const targets = items.value.filter((item) => !isStructural(item.name))
  if (!targets.length) return
  const mine = ++request
  refreshing.value = true
  try {
    const data = await fetchAnswers(targets)
    // a slower answer for an older period must not overwrite a newer one
    if (mine !== request) return
    Object.assign(answers, data)
    updatedAt.value = new Date()
  } catch (error) {
    if (mine === request)
      toast.error(error?.messages?.[0] || __('Could not load the numbers'))
  } finally {
    if (mine === request) refreshing.value = false
  }
}

async function loadOne(item) {
  if (isStructural(item.name)) return
  const key = item.layout.i
  delete answers[key]
  const asOf = request
  try {
    const data = await fetchAnswers([item])
    // the filters changed meanwhile: the full reload answers this one too
    if (asOf === request) Object.assign(answers, data)
  } catch (error) {
    answers[key] = {
      error: error?.messages?.[0] || __('This widget could not be loaded'),
    }
  }
}

watch(filters, () => {
  if (current.value) loadAnswers()
})

useIntervalFn(() => {
  if (!current.value || editing.value || document.visibilityState !== 'visible')
    return
  loadAnswers()
}, AUTO_REFRESH)

// -- building ----------------------------------------------------------------------

function startEditing() {
  draft = JSON.parse(JSON.stringify(items.value))
  editing.value = true
  showLibrary.value = true
  if (!catalog.data && !catalog.loading) catalog.fetch()
}

function cancelEditing() {
  if (draft) items.value = draft
  draft = null
  editing.value = false
}

async function save() {
  // nothing moved: a template dashboard stays on its template
  if (!changed()) {
    draft = null
    editing.value = false
    return
  }
  saving.value = true
  try {
    const saved = await call('crm.api.dashboard.save_dashboard_layout', {
      name: current.value.name,
      layout: JSON.stringify(toSavedLayout(items.value)),
    })
    current.value = saved
    items.value = saved.layout || []
    editing.value = false
    draft = null
    dashboards.reload()
    toast.success(__('Dashboard saved'))
    loadAnswers()
  } catch (error) {
    toast.error(error?.messages?.[0] || __('Could not save the dashboard'))
  } finally {
    saving.value = false
  }
}

function changed() {
  return (
    draft &&
    JSON.stringify(toSavedLayout(draft)) !==
      JSON.stringify(toSavedLayout(items.value))
  )
}

function add(widget) {
  const item = newItem(widget, items.value)
  if (widget.id === 'heading') item.config = {}
  items.value.push(item)
  loadOne(item)
  highlight(item.layout.i)
  if (widget.id === 'heading') configure(item)
}

function highlight(key) {
  highlighted.value = key
  nextTick(() => {
    scroller.value
      ?.querySelector(`[data-widget="${CSS.escape(key)}"]`)
      ?.scrollIntoView({ behavior: 'smooth', block: 'center' })
  })
  setTimeout(() => {
    if (highlighted.value === key) highlighted.value = ''
  }, 1600)
}

function remove(item) {
  items.value = items.value.filter((other) => other.layout.i !== item.layout.i)
}

function duplicate(item) {
  const copy = duplicateItem(item, items.value)
  items.value.push(copy)
  if (answers[item.layout.i]) answers[copy.layout.i] = answers[item.layout.i]
  highlight(copy.layout.i)
}

function widgetOf(item) {
  if (isStructural(item.name))
    return layoutWidgets().find((widget) => widget.id === item.name)
  return (catalog.data?.widgets || []).find((widget) => widget.id === item.name)
}

function configurable(item) {
  if (item.name === 'spacer') return false
  return true
}

function configure(item) {
  configItem.value = item
  configWidget.value = widgetOf(item) || {
    id: item.name,
    title: answers[item.layout.i]?.title,
    options: [],
  }
  showConfig.value = true
}

function applyConfig(config) {
  const item = items.value.find(
    (other) => other.layout.i === configItem.value?.layout.i,
  )
  if (!item) return
  item.config = config
  loadOne(item)
}

// -- going somewhere ----------------------------------------------------------------

function navigate(target) {
  if (!target) return
  if (target.settings) return openSettings(target.settings)
  if (target.route) router.push(target.route)
}

// the modal finds a page by its untranslated key or name, in every language
function openSettings(page) {
  activeSettingsPage.value = page
  showSettings.value = true
}

function setUp(feature) {
  if (!feature) return
  if (feature.key === 'automations') return router.push({ name: 'Automations' })
  if (feature.settings) openSettings(feature.settings)
}

// -- managing dashboards ------------------------------------------------------------

function openDashboardDialog(mode) {
  dashboardDialogMode.value = mode
  if (mode === 'create' && !catalog.data && !catalog.loading) catalog.fetch()
  showDashboardDialog.value = true
}

async function onDashboardSaved(summary) {
  await dashboards.reload()
  if (dashboardDialogMode.value === 'create') {
    await openDashboard(summary.name)
    if (!summary.template && summary.can_edit && !isMobileView.value)
      startEditing()
  } else {
    const asked = filters.value
    const periodChanged = summary.period !== current.value?.period
    current.value = { ...current.value, ...summary }
    if (periodChanged) {
      period.value = summary.period
      range.value = periodRange(summary.period)
    }
    if (summary.only_mine) userFilter.value = null
    // "only mine" is not one of the filters, so a change of it asks here
    if (filters.value === asked) loadAnswers()
  }
}

async function duplicateDashboard() {
  try {
    const copy = await call('crm.api.dashboard.create_dashboard', {
      title: '',
      private: 1,
      copy_of: current.value.name,
    })
    await dashboards.reload()
    await openDashboard(copy.name)
    toast.success(__('Copied to your dashboards'))
  } catch (error) {
    toast.error(error?.messages?.[0] || __('Could not copy the dashboard'))
  }
}

function resetToTemplate() {
  $dialog({
    title: __('Back to the template?'),
    message: __(
      'The dashboard goes back to the ready-made layout and keeps up with the site again. The current arrangement is lost.',
    ),
    actions: [
      {
        label: __('Reset'),
        variant: 'solid',
        onClick: async (close) => {
          try {
            const data = await call('crm.api.dashboard.reset_dashboard', {
              name: current.value.name,
            })
            current.value = data
            items.value = data.layout || []
            editing.value = false
            draft = null
            dashboards.reload()
            loadAnswers()
          } catch (error) {
            toast.error(
              error?.messages?.[0] || __('Could not reset the dashboard'),
            )
          }
          close()
        },
      },
    ],
  })
}

function deleteDashboard() {
  $dialog({
    title: __('Delete {0}?', [current.value.title]),
    message: current.value.private
      ? __('Only you could see it. This cannot be undone.')
      : __('Nobody on the team will see it any more. This cannot be undone.'),
    actions: [
      {
        label: __('Delete'),
        variant: 'solid',
        theme: 'red',
        onClick: async (close) => {
          try {
            await call('crm.api.dashboard.delete_dashboard', {
              name: current.value.name,
            })
          } catch (error) {
            close()
            toast.error(
              error?.messages?.[0] || __('Could not delete the dashboard'),
            )
            return
          }
          close()
          current.value = null
          items.value = []
          await dashboards.reload()
          openInitial()
        },
      },
    ],
  })
}

usePageMeta(() => ({ title: current.value?.title || __('Dashboard') }))
</script>
