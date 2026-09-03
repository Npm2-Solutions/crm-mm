<template>
  <div class="flex h-full flex-col gap-6 py-8 px-6 text-ink-gray-8">
    <div class="flex items-center justify-between px-2">
      <div class="flex flex-col gap-1">
        <h2 class="flex gap-2 text-2xl-semibold leading-none h-5">
          {{ __('Working Hours') }}
        </h2>
        <p class="text-p-base text-ink-gray-6">
          {{
            __(
              'When each professional is available, plus days off and one-off extra hours.',
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

    <div class="flex-1 overflow-y-auto px-2">
      <div
        v-if="schedules.data?.length"
        class="divide-y divide-outline-gray-1 rounded-lg border border-outline-gray-2"
      >
        <div
          v-for="schedule in schedules.data"
          :key="schedule.name"
          class="flex cursor-pointer items-center gap-3 px-3 py-2.5 hover:bg-surface-gray-1"
          @click="openEditor(schedule.user)"
        >
          <UserAvatar :user="schedule.user" size="sm" class="shrink-0" />
          <div class="min-w-0 flex-1">
            <div class="truncate text-p-base-medium text-ink-gray-8">
              {{ schedule.full_name }}
            </div>
            <div class="truncate text-p-sm text-ink-gray-5">
              {{ schedule.day_count }} {{ __('time bands') }}
              <span v-if="schedule.max_daily_appointments">
                ·
                {{
                  __('max {0}/day').replace(
                    '{0}',
                    schedule.max_daily_appointments,
                  )
                }}
              </span>
              <span v-if="schedule.holiday_list">
                · {{ schedule.holiday_list }}</span
              >
            </div>
          </div>
          <Badge
            :label="schedule.enabled ? __('Active') : __('Off')"
            :theme="schedule.enabled ? 'green' : 'gray'"
            size="sm"
          />
        </div>
      </div>
      <div
        v-else-if="!schedules.loading"
        class="px-2 text-p-base text-ink-gray-5"
      >
        {{
          __(
            'Nobody has custom hours yet — everyone follows the fallback hours in Scheduling.',
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
        <label class="flex items-center gap-2 text-sm text-ink-gray-7">
          <Switch v-model="form.enabled" size="sm" /> {{ __('Enabled') }}
        </label>

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
import { reactive, ref } from 'vue'

const schedules = createResource({
  url: 'crm.api.appointments.list_schedules',
  cache: 'crm-staff-schedules',
  auto: true,
})

const showEditor = ref(false)
const saving = ref(false)
const editingUser = ref('')

const emptyForm = () => ({
  user: '',
  enabled: true,
  max_daily_appointments: 0,
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
    params: { schedule: { ...form } },
    auto: true,
    onSuccess: () => {
      saving.value = false
      showEditor.value = false
      toast.success(__('Working hours saved'))
      schedules.reload()
    },
    onError: (e) => {
      saving.value = false
      toast.error(e.messages?.[0] || __('Failed to save'))
    },
  })
}
</script>
