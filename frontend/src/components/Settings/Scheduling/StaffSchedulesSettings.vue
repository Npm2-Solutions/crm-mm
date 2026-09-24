<template>
  <div class="flex h-full flex-col gap-6 py-8 px-6 text-ink-gray-8">
    <div class="flex items-center justify-between px-2">
      <div class="flex flex-col gap-1">
        <h2 class="flex gap-2 text-2xl-semibold leading-none h-5">
          {{ __('Team rota') }}
        </h2>
        <p class="text-p-base text-ink-gray-6">
          {{
            __(
              'The whole team at a glance: hours, days off and how full each day is. Click a person to edit.',
            )
          }}
        </p>
      </div>
      <Button
        variant="solid"
        :label="__('Set hours')"
        iconLeft="plus"
        @click="openEditor()"
      />
    </div>

    <div class="flex items-center gap-2 px-2">
      <Button
        variant="ghost"
        icon="lucide-chevron-left"
        @click="shiftWeek(-7)"
      />
      <Button variant="ghost" :label="__('This week')" @click="setWeek('')" />
      <Button
        variant="ghost"
        icon="lucide-chevron-right"
        @click="shiftWeek(7)"
      />
      <span class="text-p-base-medium text-ink-gray-7">{{ weekLabel }}</span>
      <span class="grow" />
      <span class="flex items-center gap-2 text-p-xs">
        <span class="rounded bg-surface-green-2 px-1.5 py-0.5 text-ink-green-8">
          {{ __('Working') }}
        </span>
        <span class="rounded bg-surface-amber-2 px-1.5 py-0.5 text-ink-amber-8">
          {{ __('Day off / holiday') }}
        </span>
        <span class="rounded bg-surface-blue-2 px-1.5 py-0.5 text-ink-blue-8">
          {{ __('Extra hours') }}
        </span>
        <span class="flex items-center gap-1 text-ink-gray-5">
          <span class="h-1 w-5 rounded bg-surface-gray-7" />
          {{ __('Booked') }}
        </span>
      </span>
    </div>

    <div class="flex-1 overflow-auto px-2">
      <div
        v-if="rota.data?.team?.length"
        class="min-w-[760px] rounded-lg border border-outline-gray-2"
      >
        <div
          class="grid grid-cols-[200px_repeat(7,minmax(0,1fr))] border-b border-outline-gray-2 bg-surface-gray-1 text-p-xs text-ink-gray-5"
        >
          <div class="px-3 py-2">{{ __('Professional') }}</div>
          <div
            v-for="day in rota.data.days"
            :key="day"
            class="px-2 py-2 text-center"
            :class="day === todayIso ? 'text-ink-gray-8 font-semibold' : ''"
          >
            {{ dayLabel(day) }}
          </div>
        </div>
        <div
          v-for="person in rota.data.team"
          :key="person.user"
          class="grid cursor-pointer grid-cols-[200px_repeat(7,minmax(0,1fr))] border-b border-outline-gray-1 last:border-b-0 hover:bg-surface-gray-1"
          @click="openEditor(person.user)"
        >
          <div class="flex min-w-0 items-center gap-2 px-3 py-2">
            <UserAvatar :user="person.user" size="sm" class="shrink-0" />
            <div class="min-w-0">
              <div class="truncate text-p-sm-medium text-ink-gray-8">
                {{ person.full_name }}
              </div>
              <div class="truncate text-p-xs text-ink-gray-5">
                {{ personHint(person) }}
              </div>
            </div>
          </div>
          <div
            v-for="cell in person.days"
            :key="cell.date"
            class="flex flex-col gap-1 border-l border-outline-gray-1 px-1.5 py-2"
          >
            <div
              v-for="(w, i) in cell.windows"
              :key="i"
              class="rounded px-1 py-0.5 text-center text-p-xs"
              :class="
                cell.state === 'extra'
                  ? 'bg-surface-blue-2 text-ink-blue-8'
                  : 'bg-surface-green-2 text-ink-green-8'
              "
            >
              {{ w[0] }}–{{ w[1] }}
            </div>
            <div
              v-if="cell.state === 'closed'"
              class="py-0.5 text-center text-p-xs text-ink-gray-4"
            >
              {{ __('Closed') }}
            </div>
            <div
              v-if="cell.state === 'off' || cell.state === 'holiday'"
              class="truncate rounded bg-surface-amber-2 px-1 py-0.5 text-center text-p-xs text-ink-amber-8"
              :title="cell.reason"
            >
              {{
                cell.state === 'holiday'
                  ? __('Holiday')
                  : cell.reason || __('Off')
              }}
            </div>
            <div
              v-if="cell.open_minutes"
              class="mt-auto h-1 overflow-hidden rounded bg-surface-gray-2"
              :title="
                __('{0} of {1} hours booked', [
                  Math.round(cell.booked_minutes / 6) / 10,
                  Math.round(cell.open_minutes / 6) / 10,
                ])
              "
            >
              <div
                class="h-full bg-surface-gray-7"
                :style="{
                  width: `${Math.min(100, (cell.booked_minutes / cell.open_minutes) * 100)}%`,
                }"
              />
            </div>
          </div>
        </div>
      </div>
      <div v-else-if="!rota.loading" class="px-2 text-p-base text-ink-gray-5">
        {{
          __(
            'Nobody on the team yet: add professionals to a service, or set their hours.',
          )
        }}
      </div>
    </div>
  </div>

  <Dialog v-model="showEditor" :options="{ title: editorTitle, size: '2xl' }">
    <template #body-content>
      <div class="flex flex-col gap-6">
        <PersonPicker
          v-if="!editingUser"
          v-model="form.user"
          :label="__('Professional')"
          :exclude="withOwnHours"
        />

        <!-- 1. when they work -->
        <section class="flex flex-col gap-3">
          <h3 class="text-p-base-medium text-ink-gray-8">
            {{ __('Working hours') }}
          </h3>
          <TabButtons
            :modelValue="form.enabled ? 'own' : 'studio'"
            :buttons="[
              { label: __('Studio hours'), value: 'studio' },
              { label: __('Own hours'), value: 'own' },
            ]"
            @update:modelValue="setOwnHours"
          />
          <div
            v-if="!form.enabled"
            class="rounded-lg bg-surface-gray-2 px-3 py-2.5 text-p-sm text-ink-gray-7"
          >
            <div v-if="studioSummary.length" class="flex flex-col gap-0.5">
              <div v-for="line in studioSummary" :key="line">{{ line }}</div>
            </div>
            <div v-else>
              {{ __('No studio hours set: available any time.') }}
            </div>
            <div class="mt-1.5 text-p-xs text-ink-gray-5">
              {{
                __(
                  'The studio hours are set in Agenda → Studio hours & rules and apply to everyone without their own.',
                )
              }}
            </div>
          </div>
          <WeeklyHours v-else v-model="form.availability" />
          <Link
            doctype="CRM Holiday List"
            :modelValue="form.holiday_list"
            :label="__('Holiday calendar')"
            :placeholder="
              form.enabled
                ? __('None')
                : form.default_holiday_list || __('The studio\'s')
            "
            :disabled="!form.enabled"
            @update:modelValue="(v) => (form.holiday_list = v)"
          />
        </section>

        <!-- 2. one-off days -->
        <section class="flex flex-col gap-2">
          <h3 class="text-p-base-medium text-ink-gray-8">
            {{ __('Days off and extra hours') }}
          </h3>
          <p class="text-p-sm text-ink-gray-5">
            {{ __('Holidays, sick days, or extra hours on one date.') }}
          </p>
          <div
            v-for="(row, i) in form.exceptions"
            :key="i"
            class="grid grid-cols-[140px_130px_1fr_1fr_1.4fr_32px] items-center gap-2"
          >
            <FormControl v-model="row.date" type="date" />
            <FormControl
              :modelValue="row.unavailable ? 'off' : 'extra'"
              type="select"
              :options="[
                { label: __('Day off'), value: 'off' },
                { label: __('Extra hours'), value: 'extra' },
              ]"
              @update:modelValue="(v) => (row.unavailable = v === 'off')"
            />
            <template v-if="!row.unavailable">
              <FormControl v-model="row.start_time" type="time" />
              <FormControl v-model="row.end_time" type="time" />
            </template>
            <span v-else class="col-span-2 text-p-sm text-ink-gray-5">
              {{ __('All day') }}
            </span>
            <FormControl
              v-model="row.reason"
              type="text"
              :placeholder="__('Reason (optional)')"
            />
            <Button
              variant="ghost"
              icon="lucide-trash-2"
              @click="form.exceptions.splice(i, 1)"
            />
          </div>
          <Button
            variant="ghost"
            size="sm"
            class="self-start"
            :label="__('Add a date')"
            iconLeft="plus"
            @click="
              form.exceptions.push({
                date: '',
                unavailable: true,
                start_time: '',
                end_time: '',
                reason: '',
              })
            "
          />
        </section>

        <!-- 3. how much -->
        <section class="flex flex-col gap-3">
          <h3 class="text-p-base-medium text-ink-gray-8">
            {{ __('Limits') }}
          </h3>
          <div class="grid grid-cols-2 gap-3">
            <FormControl
              v-model.number="form.max_daily_appointments"
              type="number"
              min="0"
              :label="__('Appointments per day')"
              :placeholder="__('No limit')"
            />
            <FormControl
              v-model.number="form.max_weekly_appointments"
              type="number"
              min="0"
              :label="__('Appointments per week')"
              :placeholder="__('No limit')"
            />
          </div>
        </section>
      </div>
    </template>
    <template #actions>
      <Button
        class="w-full"
        variant="solid"
        :label="__('Save')"
        :loading="saving"
        @click="save"
      />
    </template>
  </Dialog>
</template>

<script setup>
import Link from '@/components/Controls/Link.vue'
import PersonPicker from '@/components/Settings/Scheduling/PersonPicker.vue'
import UserAvatar from '@/components/UserAvatar.vue'
import WeeklyHours from '@/components/Settings/Scheduling/WeeklyHours.vue'
import {
  call,
  createResource,
  Dialog,
  FormControl,
  TabButtons,
  toast,
} from 'frappe-ui'
import { computed, reactive, ref } from 'vue'
import { hhmm } from '@/utils/scheduler'

const weekStart = ref('')
const todayIso = new Date().toISOString().slice(0, 10)

const rota = createResource({
  url: 'crm.api.booking_admin.get_team_rota',
  makeParams: () => ({ start: weekStart.value || undefined }),
  auto: true,
})

function setWeek(value) {
  weekStart.value = value
  rota.reload()
}

function shiftWeek(days) {
  const base = new Date((rota.data?.days?.[0] || todayIso) + 'T00:00:00Z')
  base.setUTCDate(base.getUTCDate() + days)
  setWeek(base.toISOString().slice(0, 10))
}

const weekLabel = computed(() => {
  const days = rota.data?.days
  if (!days?.length) return ''
  const fmt = new Intl.DateTimeFormat(undefined, {
    day: 'numeric',
    month: 'short',
    timeZone: 'UTC',
  })
  return `${fmt.format(new Date(days[0] + 'T00:00:00Z'))} – ${fmt.format(new Date(days[6] + 'T00:00:00Z'))}`
})

function dayLabel(day) {
  return new Intl.DateTimeFormat(undefined, {
    weekday: 'short',
    day: 'numeric',
    timeZone: 'UTC',
  }).format(new Date(day + 'T00:00:00Z'))
}

function personHint(person) {
  const parts = [person.own_schedule ? __('own hours') : __('studio hours')]
  if (person.daily_cap) parts.push(__('max {0}/day', [person.daily_cap]))
  if (person.weekly_cap) parts.push(__('max {0}/week', [person.weekly_cap]))
  if (!person.online) parts.push(__('not online'))
  return parts.join(' · ')
}

const showEditor = ref(false)
const saving = ref(false)
const editingUser = ref('')

const emptyForm = () => ({
  user: '',
  full_name: '',
  enabled: false,
  max_daily_appointments: null,
  max_weekly_appointments: null,
  holiday_list: '',
  availability: [],
  exceptions: [],
  default_availability: [],
  default_holiday_list: '',
})

const form = reactive(emptyForm())

const editorTitle = computed(() =>
  editingUser.value
    ? __('Hours of {0}', [form.full_name || editingUser.value])
    : __('Set hours'),
)

const withOwnHours = computed(() =>
  (rota.data?.team || []).filter((p) => p.own_schedule).map((p) => p.user),
)

// "Mon 09:00–13:00, 14:00–18:00" — the studio hours, read only
const studioSummary = computed(() => {
  const byDay = {}
  for (const row of form.default_availability || []) {
    ;(byDay[row.workday] ||= []).push(
      `${hhmm(row.start_time)}–${hhmm(row.end_time)}`,
    )
  }
  return Object.entries(byDay).map(
    ([day, windows]) => `${__(day)}: ${windows.join(', ')}`,
  )
})

function setOwnHours(mode) {
  form.enabled = mode === 'own'
  // start from the studio's week instead of an empty one
  if (form.enabled && !form.availability.length) {
    form.availability = (form.default_availability || []).map((row) => ({
      ...row,
    }))
  }
}

async function openEditor(user = '') {
  editingUser.value = user
  Object.assign(form, emptyForm())
  try {
    const data = await call('crm.api.appointments.get_schedule', {
      user,
    })
    Object.assign(form, data, {
      user,
      enabled: Boolean(data.enabled),
      max_daily_appointments: data.max_daily_appointments || null,
      max_weekly_appointments: data.max_weekly_appointments || null,
      holiday_list: data.holiday_list || '',
      availability: data.availability || [],
      exceptions: (data.exceptions || []).map((row) => ({
        date: row.date,
        unavailable: Boolean(row.unavailable),
        start_time: hhmm(row.start_time),
        end_time: hhmm(row.end_time),
        reason: row.reason || '',
      })),
    })
    showEditor.value = true
  } catch (e) {
    toast.error(e.messages?.[0] || __('Failed to load'))
  }
}

function save() {
  if (!form.user) {
    toast.error(__('Pick a professional'))
    return
  }
  if (form.enabled && !form.availability.length) {
    toast.error(__('Add at least one time slot, or use the studio hours'))
    return
  }
  saving.value = true
  createResource({
    url: 'crm.api.appointments.save_schedule',
    params: {
      schedule: {
        user: form.user,
        enabled: form.enabled ? 1 : 0,
        max_daily_appointments: Number(form.max_daily_appointments) || 0,
        max_weekly_appointments: Number(form.max_weekly_appointments) || 0,
        holiday_list: form.enabled ? form.holiday_list : '',
        availability: form.enabled ? form.availability : [],
        exceptions: form.exceptions,
      },
    },
    auto: true,
    onSuccess: () => {
      saving.value = false
      showEditor.value = false
      toast.success(__('Working hours saved'))
      rota.reload()
    },
    onError: (e) => {
      saving.value = false
      toast.error(e.messages?.[0] || __('Failed to save'))
    },
  })
}
</script>
