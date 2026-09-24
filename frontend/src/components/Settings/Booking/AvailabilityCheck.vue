<template>
  <div
    class="flex h-full flex-col gap-6 text-ink-gray-8"
    :class="embedded ? '' : 'py-8 px-6'"
  >
    <div v-if="!embedded" class="flex flex-col gap-1 px-2">
      <h2 class="flex gap-2 text-2xl-semibold leading-none h-5">
        {{ __('Why is it not available?') }}
      </h2>
      <p class="text-p-base text-ink-gray-6">
        {{
          __(
            'Pick a service and a moment: see, professional by professional, what keeps it closed and where to change it.',
          )
        }}
      </p>
    </div>

    <div
      class="grid grid-cols-[1.4fr_1fr_0.7fr_auto_auto] items-end gap-3 px-2"
    >
      <FormControl
        v-model="service"
        type="select"
        :label="__('Service')"
        :options="serviceOptions"
      />
      <FormControl v-model="date" type="date" :label="__('Day')" />
      <FormControl v-model="time" type="time" :label="__('Time')" />
      <label class="flex h-7 items-center gap-2 text-sm text-ink-gray-7">
        <Switch v-model="online" size="sm" /> {{ __('As a client online') }}
      </label>
      <Button
        variant="solid"
        :label="__('Check')"
        :loading="check.loading"
        :disabled="!service || !date || !time"
        @click="run"
      />
    </div>

    <div v-if="result" class="flex flex-1 flex-col gap-4 overflow-y-auto px-2">
      <div
        class="flex items-center gap-2 rounded-lg px-3 py-2 text-p-base-medium"
        :class="
          result.offered
            ? 'bg-surface-green-1 text-ink-green-8'
            : 'bg-surface-red-1 text-ink-red-8'
        "
      >
        <span
          :class="result.offered ? 'lucide-circle-check' : 'lucide-circle-x'"
          class="size-4"
        />
        {{
          result.offered
            ? __('Bookable at this time')
            : __('Not bookable at this time')
        }}
      </div>

      <section v-if="result.service_reasons.length" class="flex flex-col gap-2">
        <h3 class="text-p-sm-medium text-ink-gray-6">
          {{ __('Service and online rules') }}
        </h3>
        <ReasonRow
          v-for="why in result.service_reasons"
          :key="why.code"
          :reason="why"
        />
      </section>

      <section
        v-if="result.resource_reasons.length"
        class="flex flex-col gap-2"
      >
        <h3 class="text-p-sm-medium text-ink-gray-6">
          {{ __('Rooms & equipment') }}
        </h3>
        <ReasonRow
          v-for="why in result.resource_reasons"
          :key="why.code + why.text"
          :reason="why"
        />
      </section>

      <section class="flex flex-col gap-2">
        <h3 class="text-p-sm-medium text-ink-gray-6">
          {{ __('Professionals') }}
          <span class="text-ink-gray-4">· {{ staffingLabel }}</span>
        </h3>
        <div
          class="divide-y divide-outline-gray-1 rounded-lg border border-outline-gray-2"
        >
          <div
            v-for="person in result.staff"
            :key="person.user"
            class="flex items-start gap-3 px-3 py-2.5"
          >
            <UserAvatar :user="person.user" size="sm" class="mt-0.5 shrink-0" />
            <div class="min-w-0 flex-1">
              <div class="flex items-center gap-2">
                <span class="text-p-base-medium text-ink-gray-8">{{
                  person.full_name
                }}</span>
                <span class="text-p-xs text-ink-gray-5"
                  >{{ person.duration }} min</span
                >
              </div>
              <div v-if="person.free" class="text-p-sm text-ink-green-8">
                {{ __('Free at this time') }}
              </div>
              <div
                v-for="why in person.reasons"
                :key="why.code"
                class="text-p-sm text-ink-gray-7"
              >
                <span class="font-mono text-p-xs text-ink-gray-4">{{
                  why.code
                }}</span>
                {{ why.text }}
                <span v-if="fixLabel(why.fix)" class="text-ink-gray-5">
                  → {{ fixLabel(why.fix) }}
                </span>
              </div>
            </div>
          </div>
        </div>
      </section>
    </div>
  </div>
</template>

<script setup>
import UserAvatar from '@/components/UserAvatar.vue'
import { createResource, FormControl, Switch, toast } from 'frappe-ui'
import { computed, defineComponent, h, ref } from 'vue'

defineProps({
  // inside a dialog: the dialog carries the title
  embedded: { type: Boolean, default: false },
})

const FIXES = {
  service: () => __('Agenda → Services'),
  online_rules: () => __('Booking page defaults, or the service online panel'),
  matrix: () =>
    __('Booking → Online booking, or the grid in Agenda → Services'),
  rota: () => __('Agenda → Team rota'),
  calendar: () => __('the calendar'),
  resources: () => __('Agenda → Rooms & equipment'),
}

function fixLabel(fix) {
  return FIXES[fix]?.() || ''
}

const ReasonRow = defineComponent({
  props: { reason: { type: Object, required: true } },
  setup(props) {
    return () =>
      h(
        'div',
        {
          class:
            'rounded-md border border-outline-gray-2 px-3 py-2 text-p-sm text-ink-gray-7',
        },
        [
          h(
            'span',
            { class: 'font-mono text-p-xs text-ink-gray-4' },
            props.reason.code + ' ',
          ),
          props.reason.text,
          fixLabel(props.reason.fix)
            ? h(
                'span',
                { class: 'text-ink-gray-5' },
                ` → ${fixLabel(props.reason.fix)}`,
              )
            : null,
        ],
      )
  },
})

const meta = createResource({
  url: 'crm.api.appointments.get_scheduler_meta',
  cache: 'crm-scheduler-meta',
  auto: true,
})

const serviceOptions = computed(() => [
  { label: __('Pick a service'), value: '' },
  ...(meta.data?.services || []).map((s) => ({
    label: s.service_name,
    value: s.name,
  })),
])

const service = ref('')
const tomorrow = new Date(Date.now() + 86400000).toISOString().slice(0, 10)
const date = ref(tomorrow)
const time = ref('10:00')
const online = ref(true)
const result = ref(null)

const check = createResource({
  url: 'crm.api.booking_admin.explain_slot',
  onSuccess: (data) => (result.value = data),
  onError: (e) => toast.error(e.messages?.[0] || __('Check failed')),
})

function run() {
  // the moment is read in the browser's timezone, like the calendar
  const start = new Date(`${date.value}T${time.value}:00`).toISOString()
  check.submit({ service: service.value, start, online: online.value ? 1 : 0 })
}

const staffingLabel = computed(
  () =>
    ({
      'Any one': __('any free one is enough'),
      'All required': __('everybody must be free'),
      'One per role': __('one free per role'),
    })[result.value?.staffing] || '',
)
</script>
