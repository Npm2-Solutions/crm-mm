<template>
  <div
    class="flex h-full flex-col gap-6 py-8 px-6 text-ink-gray-8 max-md:px-3 max-md:py-5"
  >
    <div
      class="flex items-start justify-between gap-4 px-2 max-md:flex-col max-md:items-start max-md:gap-3"
    >
      <div class="flex min-w-0 flex-col gap-1">
        <h2
          class="flex gap-2 text-2xl-semibold leading-tight md:h-5 md:leading-none"
        >
          {{ __('Plan') }}
        </h2>
        <p class="text-p-base text-ink-gray-6">
          {{
            __(
              'The modules your centre has, and what it used this month. A module that ends is never deleted: its data stays readable.',
            )
          }}
        </p>
      </div>
      <Button
        v-if="plan.data?.agency"
        class="shrink-0"
        :label="__('Edit in Desk')"
        icon-left="lucide-external-link"
        @click="openDesk"
      />
    </div>

    <div
      v-if="plan.data"
      class="flex flex-1 flex-col gap-6 overflow-y-auto px-2"
    >
      <!-- the size: counted, never enforced -->
      <section
        class="flex flex-col gap-1.5 rounded-lg border border-outline-gray-2 p-4"
      >
        <div class="text-base-semibold text-ink-gray-8">
          {{ sizeText }}
        </div>
        <div class="text-p-sm text-ink-gray-6">
          {{ __('{0} active agendas this month', [plan.data.agendas.active]) }}
        </div>
        <div
          v-if="plan.data.agendas.over"
          class="mt-1 flex gap-2 rounded bg-surface-amber-1 p-2 text-p-sm text-ink-amber-3"
        >
          <span
            class="lucide-info mt-0.5 size-3.5 shrink-0"
            aria-hidden="true"
          />
          <span>
            {{
              __(
                'More agendas than the plan covers. Nothing is blocked: appointments and invoices work as always, and the agency will propose the size above.',
              )
            }}
          </span>
        </div>
        <p class="text-p-sm text-ink-gray-5">
          {{
            __(
              'An agenda is a practitioner with at least one appointment in the month, even one who never opens the CRM. Rooms, equipment, front desk and managers do not count.',
            )
          }}
        </p>
      </section>

      <section class="flex flex-col gap-2">
        <div class="text-base-semibold text-ink-gray-8">
          {{ __('Modules') }}
        </div>
        <ul
          class="divide-y divide-outline-elevation-2 rounded-lg border border-outline-gray-2"
        >
          <li
            v-for="module in plan.data.modules"
            :key="module.key"
            class="flex items-start gap-3 px-4 py-3 max-md:flex-col"
          >
            <div class="flex min-w-0 flex-1 flex-col gap-1">
              <div class="flex flex-wrap items-center gap-2">
                <span class="text-base-medium text-ink-gray-8">
                  {{ __(module.label) }}
                </span>
                <Badge
                  :label="stateLabel(module)"
                  :theme="stateTheme(module)"
                  size="sm"
                />
                <Badge
                  v-if="module.included_in_service"
                  :label="
                    module.service
                      ? __('Included in {0}', [module.service])
                      : __('Included in the agency\'s service')
                  "
                  theme="gray"
                  size="sm"
                />
              </div>
              <p class="text-p-sm text-ink-gray-5">
                {{ __(module.description) }}
              </p>
            </div>
            <Button
              v-if="module.can_start_trial"
              class="shrink-0"
              variant="solid"
              :label="__('Try it for {0} days', [plan.data.trial_days])"
              :loading="
                startTrial.loading && startTrial.params?.module === module.key
              "
              @click="startTrial.submit({ module: module.key })"
            />
          </li>
        </ul>
      </section>

      <section class="flex flex-col gap-2">
        <div class="text-base-semibold text-ink-gray-8">
          {{ __('This month') }}
        </div>
        <div class="grid grid-cols-3 gap-3 max-md:grid-cols-1">
          <div
            v-for="item in usage"
            :key="item.label"
            class="flex flex-col gap-1 rounded-lg border border-outline-gray-2 p-3"
          >
            <span class="text-p-sm text-ink-gray-5">{{ item.label }}</span>
            <span class="text-xl-semibold text-ink-gray-8">
              {{ item.value ?? '–' }}
            </span>
          </div>
        </div>
        <p class="text-p-sm text-ink-gray-5">
          {{
            __(
              'Messages, SMS and call minutes are billed at cost by the agency, once a month.',
            )
          }}
        </p>
      </section>
    </div>
    <div v-else-if="plan.error" class="px-2 text-p-base text-ink-red-4">
      {{ plan.error.messages?.[0] || __('The plan could not be loaded') }}
    </div>
  </div>
</template>

<script setup>
// Settings > Plan (listino.md, doc 30 "il piano del centro"). The centre reads
// its plan here and starts the trial of a module it does not have; everything
// else about the plan is the agency's, from the Desk.
import { usersStore } from '@/stores/users'
import { formatDate } from '@/utils'
import { Badge, createResource, toast } from 'frappe-ui'
import { computed } from 'vue'

const { permissions } = usersStore()

const plan = createResource({
  url: 'crm.api.plan.get_plan',
  auto: true,
})

const startTrial = createResource({
  url: 'crm.api.plan.start_trial',
  onSuccess(data) {
    plan.setData(data)
    // the new module's capabilities, for the menus that depend on them
    permissions.reload()
    if (data.agency_notified) {
      toast.success(__('Trial started: the agency has been told'))
    } else {
      toast.warning(
        __('Trial started, but the agency could not be emailed: let them know'),
      )
    }
  },
  onError(error) {
    toast.error(error?.messages?.[0] || __('Something went wrong'))
  },
})

const SIZES = {
  Solo: __('Solo, one agenda'),
  Studio: __('Studio, up to 3 agendas'),
  Centre: __('Centre, up to 8 agendas'),
  Polyclinic: __('Polyclinic, up to 15 agendas'),
  Large: __('Over 15 agendas'),
}

const sizeText = computed(() =>
  plan.data?.size
    ? SIZES[plan.data.size] || plan.data.size
    : __('No size set yet: the agency sets it with the plan'),
)

const usage = computed(() => [
  { label: __('WhatsApp messages sent'), value: plan.data?.usage?.whatsapp },
  { label: __('SMS sent'), value: plan.data?.usage?.sms },
  { label: __('Call minutes'), value: plan.data?.usage?.call_minutes },
])

function stateLabel(module) {
  if (module.state === 'trial')
    return module.trial_until
      ? __('Trial until {0}', [formatDate(module.trial_until, 'D MMM')])
      : __('Trial')
  return {
    active: __('Active'),
    read_only: __('Read only'),
    off: __('Not included'),
  }[module.state]
}

function stateTheme(module) {
  return {
    active: 'green',
    trial: 'blue',
    read_only: 'orange',
    off: 'gray',
  }[module.state]
}

function openDesk() {
  window.open('/app/crm-plan', '_blank')
}
</script>
