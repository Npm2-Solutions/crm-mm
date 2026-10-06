<!--
  Modifications copyright (c) 2026, NPM2 Solutions Srl

  How the agenda opens, the minutes its grid moves by (docs/progetto-ghl/
  56-agenda.md), and when events are reminded; the fields wait for the
  settings, as a page opened from a link draws before they come.
-->
<!-- eslint-disable vue/no-v-html -->
<template>
  <div
    class="flex h-full flex-col gap-6 px-6 py-8 text-ink-gray-8 max-md:px-3 max-md:py-5"
  >
    <!-- Header -->
    <div
      class="flex justify-between px-2 text-ink-gray-8 impostazioni-strette:flex-col impostazioni-strette:items-start impostazioni-strette:gap-3"
    >
      <div class="flex flex-col gap-1">
        <h2
          class="flex gap-2 text-2xl-semibold leading-tight md:h-5 md:leading-none"
        >
          {{ __('Agenda & reminders') }}
        </h2>
        <p class="text-p-base text-ink-gray-6">
          {{
            __(
              'How the agenda opens, the minutes its grid moves by, when you are reminded of events.',
            )
          }}
        </p>
      </div>
      <div
        class="flex items-start space-x-2 w-3/12 justify-end impostazioni-strette:w-auto impostazioni-strette:justify-start"
      >
        <AzioneImpostazioni
          v-if="settings.isDirty"
          :loading="settings.loading"
          @click="updateSettings"
        />
      </div>
    </div>

    <!-- Fields: once the settings have come, or the first draw reads them
         from nothing -->
    <div v-if="settings.doc" class="flex flex-1 flex-col overflow-y-auto">
      <!-- where the agenda opens, and the minutes its grid moves by -->
      <div
        v-for="riga in righe"
        :key="riga.campo"
        class="flex items-center justify-between gap-8 px-2 py-3 impostazioni-strette:flex-col impostazioni-strette:items-stretch impostazioni-strette:gap-2"
      >
        <div class="flex min-w-0 flex-col">
          <div class="text-p-base-medium text-ink-gray-7">
            {{ riga.etichetta }}
          </div>
          <div class="text-p-sm text-ink-gray-5">{{ riga.descrizione }}</div>
        </div>
        <div class="w-36 shrink-0 impostazioni-strette:w-full">
          <FormControl
            v-model="settings.doc[riga.campo]"
            type="select"
            :aria-label="riga.etichetta"
            :options="riga.opzioni"
          />
        </div>
      </div>
      <div class="h-px border-t mx-2 border-outline-elevation-2" />
      <div class="flex flex-col gap-3 px-2 py-3">
        <div>
          <div class="text-p-base-medium text-ink-gray-7 truncate">
            {{ __('Event Notifications') }}
          </div>
          <div
            class="text-p-sm text-ink-gray-5"
            v-html="
              __(
                'Reminders will be sent <b>before the event starts</b>, based on the configured time',
              )
            "
          />
        </div>
        <div
          v-if="notifications?.length"
          class="rounded-lg flex flex-col gap-2 w-fit impostazioni-strette:w-full"
        >
          <div v-for="notification in notifications" :key="notification.name">
            <!-- on a phone the kind takes its line and the rest wraps
                 under it: in one row the minutes went off the screen -->
            <div class="flex flex-wrap items-center gap-2">
              <!-- a select draws no box of its own: its width is the
                   box's around it -->
              <div class="w-36 shrink-0 impostazioni-strette:w-full">
                <FormControl
                  v-model="notification.type"
                  :aria-label="__('Type')"
                  type="select"
                  :options="[
                    {
                      label: __('Notification'),
                      value: 'Notification',
                    },
                    {
                      label: __('Email'),
                      value: 'Email',
                    },
                  ]"
                  :placeholder="__('Notification')"
                />
              </div>
              <FormControl
                v-model.number="notification.before"
                :aria-label="__('How long before')"
                class="w-20 shrink-0"
                type="number"
                inputmode="numeric"
                :min="min(notification)"
                :max="max(notification)"
                :step="notification.interval == 'minutes' ? 5 : 1"
                :placeholder="__('10')"
                @blur="handleIntervalChange(notification)"
              />
              <div class="w-32 shrink-0">
                <FormControl
                  v-model="notification.interval"
                  :aria-label="__('Unit')"
                  type="select"
                  :options="[
                    {
                      label:
                        notification.before == 1 ? __('minute') : __('minutes'),
                      value: 'minutes',
                    },
                    {
                      label:
                        notification.before == 1 ? __('hour') : __('hours'),
                      value: 'hours',
                    },
                    {
                      label: notification.before == 1 ? __('day') : __('days'),
                      value: 'days',
                    },
                    {
                      label:
                        notification.before == 1 ? __('week') : __('weeks'),
                      value: 'weeks',
                    },
                  ]"
                  :placeholder="__('minutes')"
                  @update:modelValue="() => handleIntervalChange(notification)"
                />
              </div>
              <Button
                :aria-label="__('Remove')"
                icon="lucide-x"
                variant="ghost"
                @click="
                  notifications.splice(notifications.indexOf(notification), 1)
                "
              />
            </div>
          </div>
        </div>
        <Button
          class="w-fit"
          :label="__('Add Notification')"
          iconLeft="plus"
          @click="
            notifications.push({
              type: 'Notification',
              before: 10,
              interval: 'minutes',
            })
          "
        />
      </div>
      <div class="h-px border-t mx-2 border-outline-elevation-2" />
      <div class="flex flex-col gap-3 py-3 px-2">
        <div>
          <div class="text-p-base-medium text-ink-gray-7 truncate">
            {{ __('All Day Event Notifications') }}
          </div>
          <div
            class="text-p-sm text-ink-gray-5"
            v-html="
              __(
                'For all-day events, <b>set a time</b> to send reminders before the event starts',
              )
            "
          />
        </div>
        <div
          v-if="allDayNotifications?.length"
          class="rounded-lg flex flex-col gap-2 w-fit impostazioni-strette:w-full"
        >
          <div
            v-for="notification in allDayNotifications"
            :key="notification.name"
          >
            <!-- on a phone the kind takes its line and the rest wraps
                 under it: in one row the minutes went off the screen -->
            <div class="flex flex-wrap items-center gap-2">
              <!-- a select draws no box of its own: its width is the
                   box's around it -->
              <div class="w-36 shrink-0 impostazioni-strette:w-full">
                <FormControl
                  v-model="notification.type"
                  :aria-label="__('Type')"
                  type="select"
                  :options="[
                    {
                      label: __('Notification'),
                      value: 'Notification',
                    },
                    {
                      label: __('Email'),
                      value: 'Email',
                    },
                  ]"
                  :placeholder="__('Notification')"
                />
              </div>
              <FormControl
                v-model.number="notification.before"
                :aria-label="__('How long before')"
                class="w-20 shrink-0"
                type="number"
                inputmode="numeric"
                :min="min(notification)"
                :max="max(notification)"
                :placeholder="__('10')"
                @blur="handleIntervalChange(notification)"
              />
              <div class="w-32 shrink-0">
                <FormControl
                  v-model="notification.interval"
                  :aria-label="__('Unit')"
                  type="select"
                  :options="[
                    {
                      label: notification.before == 1 ? __('day') : __('days'),
                      value: 'days',
                    },
                    {
                      label:
                        notification.before == 1 ? __('week') : __('weeks'),
                      value: 'weeks',
                    },
                  ]"
                  :placeholder="__('minutes')"
                  @update:modelValue="() => handleIntervalChange(notification)"
                />
              </div>
              <div class="text-p-sm text-ink-gray-5">
                {{ __('before at') }}
              </div>
              <TimePicker
                v-model="notification.time"
                class="w-32 shrink-0"
                placeholder="08:00"
              />
              <Button
                :aria-label="__('Remove')"
                icon="lucide-x"
                variant="ghost"
                @click="
                  allDayNotifications.splice(
                    allDayNotifications.indexOf(notification),
                    1,
                  )
                "
              />
            </div>
          </div>
        </div>
        <Button
          class="w-fit"
          :label="__('Add Notification')"
          iconLeft="plus"
          @click="
            allDayNotifications.push({
              type: 'Notification',
              before: 1,
              interval: 'days',
              time: '08:00',
            })
          "
        />
      </div>
    </div>
  </div>
</template>
<script setup>
import AzioneImpostazioni from '@/components/Settings/AzioneImpostazioni.vue'
import { getSettings } from '@/stores/settings'
import { showSettings } from '@/composables/settings'
import { min, max, handleIntervalChange } from '@/components/Calendar/utils'
import { FormControl, TimePicker } from 'frappe-ui'
import { computed } from 'vue'

const { _settings: settings } = getSettings()

const righe = [
  {
    campo: 'default_calendar_view',
    etichetta: __('Opening view'),
    descrizione: __(
      'Where the agenda opens until someone picks another view: then each keeps their own.',
    ),
    opzioni: [
      { label: __('Day'), value: 'Daily' },
      { label: __('Week'), value: 'Weekly' },
      { label: __('Month'), value: 'Monthly' },
    ],
  },
  {
    campo: 'calendar_grid_step',
    etichetta: __('Grid step'),
    descrizione: __(
      'A click on a free time and a moved appointment start on these minutes.',
    ),
    opzioni: ['5', '10', '15', '30'].map((minuti) => ({
      label: __('{0} minutes', [minuti]),
      value: minuti,
    })),
  },
]

const notifications = computed({
  get: () => settings.doc?.event_notifications || [],
  set: (val) => (settings.doc.event_notifications = val),
})

const allDayNotifications = computed({
  get: () => settings.doc?.all_day_event_notifications || [],
  set: (val) => (settings.doc.all_day_event_notifications = val),
})

function updateSettings() {
  settings.save.submit(null, {
    onSuccess: () => {
      showSettings.value = false
    },
  })
}
</script>
