<!--
  Copyright (c) 2026, NPM2 Solutions Srl and contributors
  For license information, please see license.txt

  Settings > The centre > Features (doc 36; the plan of listino.md, doc 30): what
  the product comprises, on and set up from its pages; the extras, each saying
  what it adds, tried for free; the size and this month's usage. The plan itself
  is the agency's, from the Desk.
-->
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
          {{ __('Features') }}
        </h2>
        <p class="text-p-base text-ink-gray-6">
          {{
            __(
              'What {brand} includes for your centre, and the extras you can add when you need them.',
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
      class="flex flex-1 flex-col gap-8 overflow-y-auto px-2 pb-2"
    >
      <!-- what the centre signed up for: on, nothing to switch -->
      <section v-if="parti.compresi.length" class="flex flex-col gap-3">
        <div class="flex flex-col gap-0.5">
          <h3 class="text-base-semibold text-ink-gray-8">
            {{ __('Included in {brand}') }}
          </h3>
          <p class="text-p-sm text-ink-gray-5">
            {{
              __(
                'Ready to use, nothing to switch on: each part is set up from its pages.',
              )
            }}
          </p>
        </div>
        <ul
          class="divide-y divide-outline-elevation-2 rounded-lg border border-outline-gray-2"
        >
          <li
            v-for="modulo in parti.compresi"
            :key="modulo.key"
            class="flex items-start gap-3 px-4 py-3"
          >
            <span
              class="grid size-8 shrink-0 place-items-center rounded-lg bg-surface-gray-2"
              aria-hidden="true"
            >
              <component :is="iconaDi(modulo)" class="size-4 text-ink-gray-7" />
            </span>
            <div class="flex min-w-0 flex-1 flex-col gap-1.5">
              <div class="flex flex-wrap items-center gap-2">
                <span class="text-base-medium text-ink-gray-8">
                  {{ __(modulo.label) }}
                </span>
                <Badge
                  v-if="modulo.state !== 'active'"
                  :label="stateLabel(modulo)"
                  :theme="stateTheme(modulo)"
                  size="sm"
                />
              </div>
              <p class="text-p-sm text-ink-gray-6">
                {{ __(modulo.description) }}
              </p>
              <FeatureSetUp :pagine="modulo.settings" />
            </div>
          </li>
        </ul>
      </section>

      <!-- the extras: what each adds; one the centre does not have is tried
           for free, one it has says where it is set up -->
      <section v-if="parti.extra.length" class="flex flex-col gap-3">
        <div class="flex flex-col gap-0.5">
          <h3 class="text-base-semibold text-ink-gray-8">
            {{ __('Extras') }}
          </h3>
          <p class="text-p-sm text-ink-gray-5">
            {{
              __(
                'Add one when the centre needs it: free for {0} days, then the agency adds it to your plan from the month after. One that ends deletes nothing: its data stays readable.',
                [plan.data.trial_days],
              )
            }}
          </p>
        </div>
        <ul class="grid grid-cols-2 gap-3 max-md:grid-cols-1">
          <li
            v-for="modulo in parti.extra"
            :key="modulo.key"
            class="flex flex-col gap-3 rounded-lg border border-outline-gray-2 p-4"
          >
            <div class="flex items-start gap-3">
              <span
                class="grid size-8 shrink-0 place-items-center rounded-lg bg-surface-gray-2"
                aria-hidden="true"
              >
                <component
                  :is="iconaDi(modulo)"
                  class="size-4 text-ink-gray-7"
                />
              </span>
              <div class="flex min-w-0 flex-1 flex-col gap-1">
                <div class="flex flex-wrap items-center gap-2">
                  <span class="text-base-medium text-ink-gray-8">
                    {{ __(modulo.label) }}
                  </span>
                  <Badge
                    v-if="modulo.state !== 'off'"
                    :label="stateLabel(modulo)"
                    :theme="stateTheme(modulo)"
                    size="sm"
                  />
                  <Badge
                    v-if="modulo.comprised_by?.length"
                    :label="
                      __('Included in {0}', [
                        modulo.comprised_by.map((nome) => __(nome)).join(', '),
                      ])
                    "
                    theme="gray"
                    size="sm"
                  />
                  <Badge
                    v-if="modulo.included_in_service"
                    :label="
                      modulo.service
                        ? __('Included in {0}', [modulo.service])
                        : __('Included in the agency\'s service')
                    "
                    theme="gray"
                    size="sm"
                  />
                </div>
                <p class="text-p-sm text-ink-gray-6">
                  {{ __(modulo.description) }}
                </p>
              </div>
            </div>
            <div class="mt-auto">
              <Button
                v-if="modulo.can_start_trial"
                variant="solid"
                :label="__('Try it free for {0} days', [plan.data.trial_days])"
                :loading="
                  startTrial.loading && startTrial.params?.module === modulo.key
                "
                @click="startTrial.submit({ module: modulo.key })"
              />
              <p
                v-else-if="modulo.state === 'read_only'"
                class="text-p-sm text-ink-gray-5"
              >
                {{
                  __(
                    'Ended: its data stays readable. Ask the agency to renew it.',
                  )
                }}
              </p>
              <FeatureSetUp
                v-else-if="modulo.state !== 'off'"
                :pagine="modulo.settings"
              />
              <p v-else class="text-p-sm text-ink-gray-5">
                {{ __('Not in your plan: ask the agency to add it.') }}
              </p>
            </div>
          </li>
        </ul>
      </section>

      <!-- the size: counted, never enforced -->
      <section class="flex flex-col gap-3">
        <h3 class="text-base-semibold text-ink-gray-8">
          {{ __('Size and usage') }}
        </h3>
        <div
          class="flex flex-col gap-1.5 rounded-lg border border-outline-gray-2 p-4"
        >
          <div class="text-base-medium text-ink-gray-8">
            {{ sizeText }}
          </div>
          <div class="text-p-sm text-ink-gray-6">
            {{
              __('{0} active agendas this month', [plan.data.agendas.active])
            }}
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
                'An agenda is a practitioner with at least one appointment in the month, even one who never opens {brand}. Rooms, equipment, front desk and managers do not count.',
              )
            }}
          </p>
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
import LucideCalendarDays from '~icons/lucide/calendar-days'
import LucideMegaphone from '~icons/lucide/megaphone'
import LucidePackage from '~icons/lucide/package'
import LucideSmartphone from '~icons/lucide/smartphone'
import LucideSparkles from '~icons/lucide/sparkles'
import LucideStethoscope from '~icons/lucide/stethoscope'
import PhoneIcon from '@/components/Icons/PhoneIcon.vue'
import FeatureSetUp from '@/components/Settings/FeatureSetUp.vue'
import { usersStore } from '@/stores/users'
import { formatDate } from '@/utils'
import { dividi } from '@/utils/funzionalita'
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

// what the product comprises, then the extras
const parti = computed(() => dividi(plan.data?.modules))

// each module by what it is; one a new module brings gets the box
const ICONE = {
  base: LucideCalendarDays,
  clinica: LucideStethoscope,
  area: LucideSmartphone,
  marketing: LucideMegaphone,
  telefono: PhoneIcon,
  assistente: LucideSparkles,
}

function iconaDi(modulo) {
  return ICONE[modulo.key] || LucidePackage
}

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
