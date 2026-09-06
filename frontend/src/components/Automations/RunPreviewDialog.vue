<template>
  <Dialog v-model="show" :options="{ title: __('Test run'), size: '2xl' }">
    <template #body-content>
      <div class="flex flex-col gap-4">
        <p class="text-sm text-ink-gray-5">
          {{
            __(
              'Walks the flow you have on screen against one real record. Conditions and branches are evaluated for real; nothing is sent, written or enrolled.',
            )
          }}
        </p>

        <div class="grid grid-cols-[140px_1fr_auto] items-end gap-2">
          <FormControl
            v-model="doctype"
            type="select"
            :label="__('Record')"
            :options="[
              { label: __('Lead'), value: 'CRM Lead' },
              { label: __('Deal'), value: 'CRM Deal' },
            ]"
          />
          <div>
            <div class="mb-1 text-xs text-ink-gray-5">{{ __('Pick one') }}</div>
            <Link
              :key="doctype"
              v-model="record"
              :doctype="doctype"
              :placeholder="__('Search')"
            />
          </div>
          <Button
            variant="solid"
            :label="__('Run')"
            :loading="running"
            :disabled="!record"
            @click="run"
          />
        </div>

        <div
          v-if="trace.length"
          class="divide-y divide-outline-gray-1 rounded-lg border border-outline-gray-2"
        >
          <div
            v-for="(entry, index) in trace"
            :key="index"
            class="flex items-start gap-2.5 px-3 py-2"
          >
            <div
              class="mt-0.5 grid size-6 shrink-0 place-items-center rounded-md"
              :class="
                STATUS_STYLE[entry.status]?.classes ||
                'bg-surface-gray-2 text-ink-gray-7'
              "
            >
              <FeatherIcon
                :name="STATUS_STYLE[entry.status]?.icon || 'circle'"
                class="size-3.5"
              />
            </div>
            <div class="min-w-0 flex-1">
              <div class="flex items-center gap-2">
                <span class="text-base font-medium text-ink-gray-8">
                  {{ stepLabel(entry.type) }}
                </span>
                <Badge size="sm" theme="gray" :label="__(entry.status)" />
              </div>
              <div class="text-sm text-ink-gray-5">{{ entry.detail }}</div>
            </div>
          </div>
        </div>
        <div v-else-if="ran" class="text-sm text-ink-gray-5">
          {{ __('Nothing would happen for this record.') }}
        </div>
      </div>
    </template>
  </Dialog>
</template>

<script setup>
import Link from '@/components/Controls/Link.vue'
import {
  Badge,
  Button,
  Dialog,
  FeatherIcon,
  FormControl,
  call,
  toast,
} from 'frappe-ui'
import { ref, watch } from 'vue'
import { stepLabel } from '@/utils/automation'

const props = defineProps({
  steps: { type: Array, required: true },
  defaultDoctype: { type: String, default: 'CRM Lead' },
})

const show = defineModel({ type: Boolean, default: false })

const STATUS_STYLE = {
  'Would run': { icon: 'play', classes: 'bg-surface-blue-1 text-ink-blue-3' },
  Skipped: {
    icon: 'corner-down-right',
    classes: 'bg-surface-gray-2 text-ink-gray-6',
  },
  Wait: { icon: 'clock', classes: 'bg-surface-amber-1 text-ink-amber-3' },
  Branch: { icon: 'git-branch', classes: 'bg-surface-blue-1 text-ink-blue-3' },
  Goal: { icon: 'target', classes: 'bg-surface-violet-1 text-ink-violet-1' },
  Jump: {
    icon: 'corner-down-right',
    classes: 'bg-surface-violet-1 text-ink-violet-1',
  },
  Exited: { icon: 'log-out', classes: 'bg-surface-red-1 text-ink-red-3' },
  End: { icon: 'check-circle', classes: 'bg-surface-green-1 text-ink-green-3' },
  Failed: {
    icon: 'alert-triangle',
    classes: 'bg-surface-red-1 text-ink-red-3',
  },
}

const doctype = ref(props.defaultDoctype)
const record = ref('')
const trace = ref([])
const running = ref(false)
const ran = ref(false)

watch(doctype, () => (record.value = ''))
watch(show, (open) => {
  if (open) {
    doctype.value = props.defaultDoctype
    trace.value = []
    ran.value = false
  }
})

async function run() {
  running.value = true
  try {
    const result = await call('crm.api.automation.simulate_automation', {
      reference_doctype: doctype.value,
      reference_name: record.value,
      steps: props.steps,
    })
    trace.value = result.trace || []
    ran.value = true
  } catch (error) {
    toast.error(error.messages?.[0] || __('The test run failed'))
  }
  running.value = false
}
</script>
