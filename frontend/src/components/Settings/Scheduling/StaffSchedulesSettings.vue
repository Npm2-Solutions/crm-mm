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
      <span class="flex items-center gap-3 text-p-xs text-ink-gray-5">
        <span class="flex items-center gap-1"
          ><span class="size-2.5 rounded-sm bg-surface-green-2" />{{
            __('Working')
          }}</span
        >
        <span class="flex items-center gap-1"
          ><span class="size-2.5 rounded-sm bg-surface-amber-2" />{{
            __('Day off / holiday')
          }}</span
        >
        <span class="flex items-center gap-1"
          ><span class="size-2.5 rounded-sm bg-surface-blue-2" />{{
            __('Extra hours')
          }}</span
        >
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

  <Dialog
    v-model="showEditor"
    :options="{ title: __('Working hours'), size: '2xl' }"
  >
    <template #body-content>
      <div class="flex flex-col gap-4">
        <div class="grid grid-cols-3 gap-3">
          <Link
            doctype="User"
            :modelValue="form.user"
            :label="__('Professional')"
            :disabled="Boolean(editingUser)"
            @update:modelValue="(v) => (form.user = v)"
          />
          <FormControl
            v-model.number="form.max_daily_appointments"
            type="number"
            min="0"
            :label="__('Max per day')"
            :description="__('0 = no limit')"
          />
          <Link
            doctype="CRM Holiday List"
            :modelValue="form.holiday_list"
            :label="__('Holiday list')"
            @update:modelValue="(v) => (form.holiday_list = v)"
          />
        </div>
        <div class="grid grid-cols-3 items-end gap-3">
          <FormControl
            v-model.number="form.max_weekly_appointments"
            type="number"
            min="0"
            :label="__('Max per week')"
            :description="__('0 = no limit')"
          />
          <label class="flex h-7 items-center gap-2 text-sm text-ink-gray-7">
            <Switch v-model="form.enabled" size="sm" /> {{ __('Own hours') }}
          </label>
          <label class="flex h-7 items-center gap-2 text-sm text-ink-gray-7">
            <Switch v-model="form.bookable_online" size="sm" />
            {{ __('Bookable online') }}
          </label>
        </div>
        <div class="grid grid-cols-2 gap-3">
          <FormControl
            v-model="form.public_title"
            type="text"
            :label="__('Title on the booking page')"
            :placeholder="__('e.g. Physiotherapist')"
          />
          <FormControl
            v-model="form.public_bio"
            type="text"
            :label="__('Short bio')"
          />
        </div>

        <WeeklyHours v-model="form.availability" :label="__('Weekly hours')" />

        <div class="flex flex-col gap-2">
          <FormLabel :label="__('Date overrides')" />
          <p class="text-p-xs text-ink-gray-5">
            {{ __('A day off, or extra hours on one specific date.') }}
          </p>
          <div
            v-for="(row, i) in form.exceptions"
            :key="i"
            class="grid grid-cols-[1fr_110px_1fr_1fr_1fr_32px] items-center gap-2"
          >
            <FormControl v-model="row.date" type="date" />
            <label class="flex items-center gap-1.5 text-p-xs text-ink-gray-7">
              <Switch v-model="row.unavailable" size="sm" /> {{ __('Off') }}
            </label>
            <FormControl
              v-model="row.start_time"
              type="time"
              :disabled="row.unavailable"
            />
            <FormControl
              v-model="row.end_time"
              type="time"
              :disabled="row.unavailable"
            />
            <FormControl
              v-model="row.reason"
              type="text"
              :placeholder="__('Reason')"
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
            :label="__('Add override')"
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
        </div>
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
import UserAvatar from '@/components/UserAvatar.vue'
import WeeklyHours from '@/components/Settings/Scheduling/WeeklyHours.vue'
import {
  createResource,
  Dialog,
  FormControl,
  FormLabel,
  Switch,
  toast,
} from 'frappe-ui'
import { computed, reactive, ref } from 'vue'

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
  const parts = [person.own_schedule ? __('own hours') : __('default hours')]
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
  enabled: true,
  max_daily_appointments: 0,
  max_weekly_appointments: 0,
  bookable_online: true,
  public_title: '',
  public_bio: '',
  holiday_list: '',
  availability: [],
  exceptions: [],
})

const form = reactive(emptyForm())

function openEditor(user = '') {
  editingUser.value = user
  Object.assign(form, emptyForm())
  if (!user) {
    showEditor.value = true
    return
  }
  createResource({
    url: 'crm.api.appointments.get_schedule',
    params: { user },
    auto: true,
    onSuccess: (data) => {
      Object.assign(form, data, {
        enabled: Boolean(data.enabled),
        bookable_online: data.bookable_online !== 0,
        holiday_list: data.holiday_list || '',
        availability: data.availability || [],
        exceptions: (data.exceptions || []).map((row) => ({
          date: row.date,
          unavailable: Boolean(row.unavailable),
          start_time: String(row.start_time || '').slice(0, 5),
          end_time: String(row.end_time || '').slice(0, 5),
          reason: row.reason || '',
        })),
      })
      showEditor.value = true
    },
    onError: (e) => toast.error(e.messages?.[0] || __('Failed to load')),
  })
}

function save() {
  if (!form.user) {
    toast.error(__('Pick a professional'))
    return
  }
  saving.value = true
  createResource({
    url: 'crm.api.appointments.save_schedule',
    params: {
      schedule: {
        ...form,
        enabled: form.enabled ? 1 : 0,
        bookable_online: form.bookable_online ? 1 : 0,
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
