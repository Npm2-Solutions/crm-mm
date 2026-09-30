<!--
  The person's plans: a diet, a training, exercises at home, habits. Each is
  written by a practitioner whose qualification allows its kind, and followed by
  the person in their area; here, how the last week went.
-->
<template>
  <section
    v-if="plans.data"
    class="flex flex-col gap-3 rounded-lg border border-outline-gray-2 p-4"
  >
    <div class="flex flex-wrap items-center justify-between gap-2">
      <h3 class="text-base-semibold text-ink-gray-8">{{ __('Plans') }}</h3>
      <Dropdown
        v-if="plans.data.kinds.length"
        :options="newOptions"
        placement="right"
      >
        <Button class="shrink-0" icon-left="plus" :label="__('New plan')" />
      </Dropdown>
    </div>
    <p v-if="!plans.data.plans.length" class="text-p-sm text-ink-gray-5">
      {{
        __(
          'No plans yet. Written here, a plan is followed by the person in their area, one tap at a time.',
        )
      }}
    </p>
    <button
      v-for="plan in plans.data.plans"
      :key="plan.name"
      type="button"
      class="flex items-center justify-between gap-3 rounded-md px-2 py-2 text-left hover:bg-surface-gray-2 focus-visible:bg-surface-gray-2 focus-visible:outline-none"
      @click="open(plan.name)"
    >
      <span class="flex min-w-0 flex-col">
        <span class="truncate text-base text-ink-gray-8">{{ plan.title }}</span>
        <span class="text-p-sm text-ink-gray-5">
          {{ __(plan.plan_type) }} · {{ plan.practitioner_name }}
        </span>
      </span>
      <span class="flex shrink-0 items-center gap-2">
        <span
          v-if="plan.status === 'Published'"
          class="text-p-xs text-ink-gray-5 max-md:hidden"
        >
          {{ __('{0} done this week', [plan.summary.Done]) }}
        </span>
        <Badge
          variant="subtle"
          :theme="statusTheme[plan.status] || 'gray'"
          :label="__(plan.status)"
        />
      </span>
    </button>
    <PlanDialog
      v-model="dialog.show"
      :lead="lead"
      :name="dialog.name"
      :kind="dialog.kind"
      @changed="plans.reload()"
    />
  </section>
</template>

<script setup>
import PlanDialog from '@/components/Clinic/PlanDialog.vue'
import { Badge, Button, Dropdown, createResource } from 'frappe-ui'
import { computed, reactive, watch } from 'vue'

const props = defineProps({ lead: { type: String, required: true } })

const statusTheme = { Draft: 'orange', Published: 'green', Closed: 'gray' }

const plans = createResource({
  url: 'crm.clinica.piani.get_plans',
  makeParams: () => ({ lead: props.lead }),
})
watch(
  () => props.lead,
  (lead) => lead && plans.reload(),
  { immediate: true },
)

const dialog = reactive({ show: false, name: null, kind: null })

// the kinds the practitioner's qualification writes
const newOptions = computed(() =>
  (plans.data?.kinds || []).map((kind) => ({
    label: __(kind),
    onClick: () => Object.assign(dialog, { show: true, name: null, kind }),
  })),
)

function open(name) {
  Object.assign(dialog, { show: true, name, kind: null })
}

defineExpose({ reload: () => plans.reload() })
</script>
