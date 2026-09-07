<template>
  <Teleport to="body">
    <Transition
      enter-active-class="transition ease-out duration-200"
      enter-from-class="opacity-0"
      leave-active-class="transition ease-in duration-150"
      leave-to-class="opacity-0"
    >
      <div
        v-if="show"
        class="fixed inset-0 z-40 bg-black/20"
        @click="show = false"
      />
    </Transition>
    <Transition
      enter-active-class="transition ease-out duration-200"
      enter-from-class="translate-x-full"
      leave-active-class="transition ease-in duration-150"
      leave-to-class="translate-x-full"
    >
      <aside
        v-if="show"
        class="fixed inset-y-0 right-0 z-50 flex w-full flex-col border-l bg-surface-modal shadow-2xl sm:w-[36rem]"
      >
        <div class="flex items-center justify-between gap-2 border-b px-4 py-3">
          <div class="flex min-w-0 items-center gap-2">
            <div class="truncate text-lg-medium text-ink-gray-9">
              {{ title }}
            </div>
            <Dropdown
              v-if="doc.status"
              :options="statuses"
              placement="left"
              class="shrink-0"
            >
              <template #default="{ open }">
                <Button
                  :label="statusLabel(doc.status)"
                  size="sm"
                  :iconRight="open ? 'chevron-up' : 'chevron-down'"
                >
                  <template #prefix>
                    <IndicatorIcon :class="getDealStatus(doc.status).color" />
                  </template>
                </Button>
              </template>
            </Dropdown>
          </div>
          <div class="flex shrink-0 items-center gap-1">
            <Button
              v-if="doc.lead"
              variant="ghost"
              :tooltip="__('Open the person')"
              :icon="ContactsIcon"
              @click="openPerson"
            />
            <Button
              variant="ghost"
              :tooltip="__('Open full page')"
              :icon="ArrowUpRightIcon"
              @click="openFullPage"
            />
            <Button variant="ghost" icon="lucide-x" @click="show = false" />
          </div>
        </div>

        <Tabs
          v-model="tabIndex"
          as="div"
          :tabs="tabs"
          class="flex flex-1 flex-col overflow-hidden [&_[role='tab']]:px-0 [&_[role='tab']]:shrink-0 [&_[role='tablist']]:px-4 [&_[role='tablist']::-webkit-scrollbar]:h-0 [&_[role='tablist']]:min-h-[45px] [&_[role='tablist']]:gap-6 [&_[role='tabpanel']:not([hidden])]:flex [&_[role='tabpanel']:not([hidden])]:grow"
        >
          <template #tab-panel>
            <Activities
              v-model:tabIndex="tabIndex"
              doctype="CRM Deal"
              :docname="dealName"
              :tabs="tabs"
            />
          </template>
        </Tabs>
      </aside>
    </Transition>
  </Teleport>
</template>

<script setup>
// The opportunity as GoHighLevel shows it: a panel over the pipeline instead of
// a page you navigate away to. Same content as the deal page's tabs — this
// borrows Activities rather than reimplementing it — so the two cannot drift.
import Activities from '@/components/Activities/Activities.vue'
import ContactsIcon from '@/components/Icons/ContactsIcon.vue'
import ArrowUpRightIcon from '@/components/Icons/ArrowUpRightIcon.vue'
import DetailsIcon from '@/components/Icons/DetailsIcon.vue'
import EventIcon from '@/components/Icons/EventIcon.vue'
import TaskIcon from '@/components/Icons/TaskIcon.vue'
import NoteIcon from '@/components/Icons/NoteIcon.vue'
import IndicatorIcon from '@/components/Icons/IndicatorIcon.vue'
import { useDocument } from '@/data/document'
import { statusesStore } from '@/stores/statuses'
import { pipelinesStore } from '@/stores/pipelines'
import { getMeta } from '@/stores/meta'
import { isTranslatable } from '@/utils'
import { Tabs, Dropdown } from 'frappe-ui'
import { computed, ref, watch } from 'vue'
import { useRouter } from 'vue-router'

const props = defineProps({
  dealName: { type: String, required: true },
})

const show = defineModel({ type: Boolean })

const router = useRouter()
const { statusOptions, getDealStatus } = statusesStore()
const { getStageNames } = pipelinesStore()
const { doctypeMeta } = getMeta('CRM Deal')

const tabIndex = ref(0)

// the panel opens on a card, so it starts on what that card is about; the deal
// page keeps its own last-tab memory and is not disturbed by this one
watch(
  () => props.dealName,
  () => (tabIndex.value = 0),
)

const { document } = useDocument('CRM Deal', props.dealName)
const doc = computed(() => document.doc || {})

const title = computed(() => {
  const field = doctypeMeta.value?.title_field || 'name'
  return doc.value?.[field] || doc.value?.lead_name || props.dealName
})

const statuses = computed(() => {
  let customStatuses = document.statuses?.length
    ? document.statuses
    : document._statuses || []
  if (!customStatuses.length) {
    customStatuses = getStageNames(doc.value?.pipeline)
  }
  return statusOptions('deal', customStatuses, changeStatus)
})

function statusLabel(status) {
  if (isTranslatable('CRM Deal Status')) return __(status)
  return status
}

function changeStatus(value) {
  doc.value.status = value
  document.save.submit()
}

const tabs = [
  { name: 'Data', label: __('Data'), icon: DetailsIcon },
  { name: 'Notes', label: __('Notes'), icon: NoteIcon },
  { name: 'Tasks', label: __('Tasks'), icon: TaskIcon },
  { name: 'Events', label: __('Events'), icon: EventIcon },
]

function openPerson() {
  show.value = false
  router.push({ name: 'Lead', params: { leadId: doc.value.lead } })
}

function openFullPage() {
  show.value = false
  router.push({ name: 'Deal', params: { dealId: props.dealName } })
}
</script>
