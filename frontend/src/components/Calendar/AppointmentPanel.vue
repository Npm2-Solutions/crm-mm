<!--
  Copyright (c) 2026, NPM2 Solutions Srl and contributors
  For license information, please see license.txt

  An appointment, in the same side panel as an event.

  It used to be a dialog four columns wide, opened over the calendar: two
  columns of boxes — service, date, start, minutes, professionals, rooms,
  participants with a name, an email, a status and an amount each, a price
  list, a price — every one of them there at once, whatever was being done.
  An event, meanwhile, opened beside the calendar as a panel that reads
  top to bottom: a line for each thing, an icon at its start, the time you
  clicked still in sight. Two ways of putting something in the same
  calendar, and the plainer one was the one used less.

  Now an appointment is that panel too. It reads first — who, when, with whom,
  where, for how much — with its status one click away, which is most of what
  is done to an appointment once it exists. Editing is the same panel, a line
  per thing: the service, the client, the day and the times, the people and
  the rooms that the service can have. What the service does not use is not
  shown: no room line in a studio without rooms, one client for a service
  that takes one.
-->
<template>
  <div class="flex h-full w-full flex-col text-base">
    <div
      class="flex items-center justify-between gap-2 p-4.5 text-lg-medium text-ink-gray-7"
    >
      <!-- `data-titolo-pannello`: where the agenda puts focus when the panel
           opens (pages/Calendar.vue), so a screen reader starts here -->
      <button
        v-if="mode === 'edit'"
        type="button"
        data-titolo-pannello
        class="flex min-w-0 items-center gap-x-2 hover:text-ink-gray-8"
        @click="backToDetails"
      >
        <span class="lucide-chevron-left size-4 shrink-0" aria-hidden="true" />
        <span class="truncate">{{ heading }}</span>
      </button>
      <h2
        v-else
        data-titolo-pannello
        tabindex="-1"
        class="truncate focus:outline-none"
      >
        {{ heading }}
      </h2>
      <div class="flex shrink-0 items-center gap-x-1">
        <!-- who reads the agenda without booking sees it, nothing to change -->
        <Button
          v-if="mode === 'details' && doc?.can_write"
          variant="ghost"
          icon="lucide-pencil"
          :tooltip="__('Edit')"
          :aria-label="__('Edit')"
          @click="emit('mode', 'edit')"
        />
        <Button
          v-if="mode !== 'new' && doc?.can_delete"
          variant="ghost"
          icon="lucide-trash-2"
          :tooltip="__('Delete')"
          :aria-label="__('Delete')"
          @click="confirmDelete"
        />
        <Button
          variant="ghost"
          icon="lucide-x"
          :tooltip="__('Close')"
          :aria-label="__('Close')"
          @click="close"
        />
      </div>
    </div>
    <slot name="kind" />

    <!-- reading -->
    <div v-if="mode === 'details'" class="flex flex-1 flex-col overflow-y-auto">
      <div
        v-if="!doc"
        class="flex flex-1 items-center justify-center text-p-base text-ink-gray-5"
      >
        {{ __('Loading…') }}
      </div>
      <template v-else>
        <div
          class="flex items-start gap-2 px-4.5 pt-1"
          @dblclick="doc.can_write && emit('mode', 'edit')"
        >
          <div
            class="mx-0.5 my-[7px] size-2.5 shrink-0 rounded-full"
            :style="{ backgroundColor: serviceColor || 'var(--ink-gray-4)' }"
          />
          <div class="flex min-w-0 flex-col gap-[3px]">
            <div
              class="text-2xl-semibold"
              :class="
                doc.status === 'Cancelled'
                  ? 'text-ink-gray-5 line-through'
                  : 'text-ink-gray-8'
              "
            >
              {{ clientNames || serviceName }}
            </div>
            <div class="text-p-base text-ink-gray-6">
              {{ clientNames ? `${serviceName} · ` : '' }}{{ whenLabel }}
            </div>
          </div>
        </div>

        <!-- what is done to an appointment once it exists: its status -->
        <div class="flex items-center gap-2 px-4.5 pt-3">
          <Dropdown v-if="doc.can_write" :options="statusActions">
            <Button
              size="sm"
              :variant="'subtle'"
              :theme="STATUS_THEME[doc.status] || 'gray'"
              :label="__(doc.status)"
              iconRight="chevron-down"
              :loading="changing"
            />
          </Dropdown>
          <Badge
            v-else
            size="lg"
            variant="subtle"
            :theme="STATUS_THEME[doc.status] || 'gray'"
            :label="__(doc.status)"
          />
          <span v-if="doc.series" class="text-p-sm text-ink-gray-5">
            {{ __('Part of a series') }}
          </span>
        </div>

        <!-- cancelling asks first, and why: the time goes back free at once
             (the waiting list may offer it) and the reason reaches the
             platform it was booked on. One tap in a menu cancelled it -->
        <div
          v-if="cancelling.open"
          class="mx-4.5 mt-3 flex flex-col gap-2 rounded-md bg-surface-gray-2 p-3"
        >
          <div class="text-p-base font-medium text-ink-gray-8">
            {{ __('Cancel this appointment?') }}
          </div>
          <div class="text-p-sm text-ink-gray-6">
            {{ __('Its time goes back free for others.') }}
          </div>
          <FormControl
            v-model="cancelling.reason"
            type="textarea"
            variant="outline"
            :rows="2"
            :placeholder="__('Why, if you know (they called, ill…)')"
            :aria-label="__('Why')"
          />
          <div class="flex flex-wrap justify-end gap-2">
            <Button
              :label="__('Keep it', null, 'Appointment')"
              @click="cancelling.open = false"
            />
            <Button
              variant="solid"
              theme="red"
              :label="__('Cancel the appointment')"
              :loading="changing"
              @click="cancelIt"
            />
          </div>
        </div>
        <!-- a cancelled one says why, when somebody said -->
        <div
          v-else-if="doc.status === 'Cancelled' && doc.cancellation_reason"
          class="flex items-start gap-2 px-4.5 pt-2 text-p-sm text-ink-gray-6"
        >
          <span
            class="lucide-circle-x mt-0.5 size-4 shrink-0"
            aria-hidden="true"
          />
          <span class="min-w-0 whitespace-pre-line break-words">
            {{ doc.cancellation_reason }}
          </span>
        </div>

        <!-- which session of its cycle it is: in or out by hand, when the
             desk booked it before selling the cycle, or the other way round -->
        <div
          v-if="doc.cycle"
          class="flex items-center gap-2 px-4.5 pt-2 text-p-sm text-ink-gray-6"
        >
          <span class="lucide-repeat size-4 shrink-0" aria-hidden="true" />
          <span class="min-w-0 flex-1 truncate">{{ cycleLine }}</span>
          <Dropdown
            v-if="doc.cycle.can_manage && cycleActions.length"
            :options="cycleActions"
          >
            <Button
              size="sm"
              variant="ghost"
              class="touch-target shrink-0"
              :label="__('Change')"
              iconRight="chevron-down"
              :loading="changing"
            />
          </Dropdown>
        </div>

        <!-- each person's subscription whose entry they use: in or out by hand -->
        <div
          v-for="who in doc.subscription?.people || []"
          :key="who.party"
          class="flex items-center gap-2 px-4.5 pt-2 text-p-sm text-ink-gray-6"
        >
          <span class="lucide-ticket size-4 shrink-0" aria-hidden="true" />
          <span class="min-w-0 flex-1 truncate">{{
            subscriptionLine(who)
          }}</span>
          <Dropdown
            v-if="
              doc.subscription.can_manage && subscriptionActions(who).length
            "
            :options="subscriptionActions(who)"
          >
            <Button
              size="sm"
              variant="ghost"
              class="touch-target shrink-0"
              :label="__('Change')"
              :aria-label="
                manyPeople
                  ? __('Change the subscription of {0}', [who.participant_name])
                  : undefined
              "
              iconRight="chevron-down"
              :loading="changing === who.party"
            />
          </Dropdown>
        </div>

        <div class="mx-4.5 my-3 border-t border-outline-gray-1" />

        <!-- the clients, and whether they came -->
        <div
          v-for="row in doc.participants || []"
          :key="row.name"
          class="flex items-center gap-3 px-4.5 py-1.5 text-ink-gray-7"
        >
          <span class="lucide-user size-4 shrink-0" aria-hidden="true" />
          <div class="min-w-0 flex-1">
            <div class="truncate text-ink-gray-8">
              {{ row.participant_name || row.party }}
            </div>
            <div
              v-if="row.email || row.phone"
              class="truncate text-p-sm text-ink-gray-5"
            >
              {{
                [leggibile(row.phone), row.email].filter(Boolean).join(' · ')
              }}
            </div>
          </div>
          <Dropdown v-if="doc.can_write" :options="attendanceActions(row)">
            <Button
              size="sm"
              variant="ghost"
              :label="__(row.status || 'Booked')"
              iconRight="chevron-down"
            />
          </Dropdown>
          <span v-else class="shrink-0 text-p-sm text-ink-gray-6">
            {{ __(row.status || 'Booked') }}
          </span>
          <Button
            v-if="row.party"
            variant="ghost"
            :tooltip="__('Open the person')"
            :aria-label="__('Open the person')"
            icon="lucide-arrow-up-right"
            @click="openPerson(row.party)"
          />
        </div>

        <div
          v-if="doc.staff?.length"
          class="flex items-start gap-3 px-4.5 py-2 text-ink-gray-7"
        >
          <span
            class="lucide-users mt-0.5 size-4 shrink-0"
            aria-hidden="true"
          />
          <div class="flex min-w-0 flex-wrap gap-x-3 gap-y-1.5">
            <span
              v-for="row in doc.staff"
              :key="row.user"
              class="flex min-w-0 items-center gap-1.5"
            >
              <UserAvatar :user="row.user" size="sm" />
              <span class="truncate">{{ personName(row.user) }}</span>
            </span>
          </div>
        </div>

        <div
          v-if="doc.resources?.length"
          class="flex items-start gap-3 px-4.5 py-2 text-ink-gray-7"
        >
          <span
            class="lucide-door-open mt-0.5 size-4 shrink-0"
            aria-hidden="true"
          />
          <div>{{ resourceSummary(doc.resources) }}</div>
        </div>

        <div
          v-if="doc.total_amount"
          class="flex items-start gap-3 px-4.5 py-2 text-ink-gray-7"
        >
          <span
            class="lucide-banknote mt-0.5 size-4 shrink-0"
            aria-hidden="true"
          />
          <div class="min-w-0">
            <div>{{ money(doc.total_amount, doc.currency) }}</div>
            <div v-if="doc.price_source" class="text-p-sm text-ink-gray-5">
              {{ doc.price_source }}
            </div>
          </div>
        </div>

        <div
          v-if="doc.location"
          class="flex items-start gap-3 px-4.5 py-2 text-ink-gray-7"
        >
          <MapIcon class="mt-0.5 size-4 shrink-0" />
          <div class="min-w-0 break-words">{{ doc.location }}</div>
        </div>

        <div
          v-if="doc.notes"
          class="flex items-start gap-3 px-4.5 py-2 text-ink-gray-7"
        >
          <DescriptionIcon class="mt-0.5 size-4 shrink-0" />
          <div class="min-w-0 whitespace-pre-line break-words">
            {{ doc.notes }}
          </div>
        </div>

        <!-- where it came from, when it was not typed in here -->
        <div
          v-if="doc.source && doc.source !== 'Internal'"
          class="mx-4.5 mt-2 flex flex-col gap-1 rounded-md bg-surface-gray-2 px-3 py-2 text-p-sm text-ink-gray-7"
        >
          <div class="flex items-center gap-2">
            <span
              :class="
                doc.source === 'Online' ? 'lucide-globe' : 'lucide-plug-zap'
              "
              class="size-4 shrink-0 text-ink-gray-5"
              aria-hidden="true"
            />
            <span class="min-w-0 flex-1 truncate font-medium">
              {{
                doc.source === 'Online'
                  ? __('Booked online by the client')
                  : __('Booked on {0}', [doc.external_platform])
              }}
            </span>
            <a
              v-if="doc.external_url"
              :href="doc.external_url"
              target="_blank"
              rel="noopener"
              class="shrink-0 text-ink-blue-link underline"
            >
              {{ __('Open', null, 'Action') }}
            </a>
          </div>
          <div v-if="doc.reschedule_count" class="text-ink-gray-5">
            {{ __('Moved {0} times', [doc.reschedule_count]) }}
          </div>
          <div v-if="doc.customer_notes" class="whitespace-pre-line">
            {{ doc.customer_notes }}
          </div>
        </div>

        <!-- a booking forced through a clash keeps the clash in sight -->
        <div
          v-if="doc.conflict_note"
          class="mx-4.5 mt-2 rounded-md bg-surface-amber-1 px-3 py-2 text-p-sm text-ink-amber-8 ring-1 ring-inset ring-outline-amber-2"
        >
          <div class="font-medium">{{ __('Booked despite a conflict') }}</div>
          <div class="whitespace-pre-line">{{ doc.conflict_note }}</div>
        </div>

        <!-- a course, a cycle of sessions: the same appointment, repeated.
             Rarely wanted, it is a row that opens: always open at the foot it
             took the bottom of a phone's screen, where the hand is -->
        <div
          v-if="doc.can_write && !doc.series && doc.status !== 'Cancelled'"
          class="mt-auto border-t border-outline-gray-1 px-4.5 py-3 max-md:mt-2"
        >
          <button
            v-if="!repeatOpen"
            type="button"
            class="flex min-h-8 w-full items-center gap-3 text-left text-ink-gray-7"
            @click="repeatOpen = true"
          >
            <span class="lucide-repeat size-4 shrink-0" aria-hidden="true" />
            <span class="min-w-0 flex-1">{{
              __('Repeat this appointment')
            }}</span>
            <span
              class="lucide-chevron-down size-4 shrink-0 text-ink-gray-5"
              aria-hidden="true"
            />
          </button>
          <div v-else class="mb-2 text-p-sm text-ink-gray-6">
            {{ __('Repeat this appointment') }}
          </div>
          <div v-if="repeatOpen" class="flex items-center gap-2">
            <FormControl
              v-model="repeat.rule"
              class="min-w-0 flex-1"
              type="select"
              size="sm"
              :options="repeatOptions"
            />
            <FormControl
              v-model.number="repeat.occurrences"
              class="w-16"
              type="number"
              inputmode="numeric"
              size="sm"
              min="1"
              :aria-label="__('Times')"
            />
            <!-- the number said nothing by itself: «4» of what -->
            <span class="shrink-0 text-p-sm text-ink-gray-6" aria-hidden="true">
              {{ __('times') }}
            </span>
            <Button
              size="sm"
              :label="__('Create')"
              :loading="repeating"
              :disabled="!repeat.rule"
              @click="createSeries"
            />
          </div>
        </div>
      </template>
    </div>

    <!-- writing -->
    <div v-else class="flex flex-1 flex-col overflow-y-auto">
      <!-- the service decides the rest: length, who can do it, where, how many -->
      <div class="flex items-center gap-3 px-4.5 py-[7px] text-ink-gray-7">
        <!-- the service's colour where the other rows have their icon, the
             fields one under the other -->
        <div class="flex size-4 shrink-0 items-center justify-center">
          <div
            class="size-2.5 rounded-full"
            :style="{
              backgroundColor: formServiceColor || 'var(--ink-gray-4)',
            }"
          />
        </div>
        <FormControl
          :modelValue="form.service"
          class="w-full"
          type="select"
          variant="outline"
          :options="serviceOptions"
          :aria-label="__('Service')"
          @update:modelValue="onServiceChange"
        />
      </div>
      <div
        v-if="serviceSummary"
        class="-mt-1 pb-1 pl-[46px] pr-4.5 text-p-sm text-ink-gray-5"
      >
        {{ serviceSummary }}
      </div>

      <!-- who it is for -->
      <div
        v-for="(row, i) in form.participants"
        :key="row.key"
        class="flex items-start gap-3 px-4.5 py-[7px] text-ink-gray-7"
      >
        <span class="lucide-user mt-2 size-4 shrink-0" aria-hidden="true" />
        <div class="min-w-0 flex-1">
          <template v-if="!row.manual">
            <!-- once picked, the person by name: the picker could only show
                 the record's id («CRM-LEAD-2026-00055») once its search had
                 moved on. The × puts the picker back. -->
            <div
              v-if="row.party"
              data-campo
              class="flex h-7 w-full items-center gap-2 rounded border border-outline-gray-2 bg-surface-base px-2 text-base text-ink-gray-8"
            >
              <span class="min-w-0 flex-1 truncate">
                {{ row.participant_name || row.party }}
              </span>
              <button
                type="button"
                class="touch-target flex shrink-0 text-ink-gray-5 hover:text-ink-gray-8"
                :aria-label="__('Choose someone else')"
                @click="pickParty(row, '')"
              >
                <span class="lucide-x size-3.5" aria-hidden="true" />
              </button>
            </div>
            <Link
              v-else
              class="w-full"
              doctype="CRM Lead"
              variant="outline"
              :modelValue="row.party"
              :placeholder="__('Who is it for?')"
              @update:modelValue="(value) => pickParty(row, value)"
            />
            <!-- booked by somebody else: the contact below is theirs -->
            <div
              v-if="row.party && row.booked_by_name"
              class="mt-1 truncate text-p-sm text-ink-gray-6"
            >
              {{ __('Booked by {0}', [row.booked_by_name]) }}
            </div>
            <div
              v-if="row.party && (row.phone || row.email)"
              class="mt-1 truncate text-p-sm text-ink-gray-5"
            >
              {{
                [leggibile(row.phone), row.email].filter(Boolean).join(' · ')
              }}
            </div>
            <button
              v-else-if="!row.party"
              type="button"
              class="mt-0.5 py-1 text-p-sm text-ink-gray-5 hover:text-ink-gray-7 hover:underline"
              @click="row.manual = true"
            >
              {{ __('Not in {brand}? Type a name') }}
            </button>
          </template>
          <div v-else class="flex flex-col gap-1.5">
            <TextInput
              v-model="row.participant_name"
              variant="outline"
              :placeholder="__('Name')"
            />
            <!-- side by side an email had 160 points on a phone, and read cut -->
            <div class="grid grid-cols-2 gap-1.5 max-md:grid-cols-1">
              <TextInput
                v-model="row.phone"
                v-bind="tastiera('telefono')"
                variant="outline"
                :placeholder="__('Phone')"
              />
              <TextInput
                v-model="row.email"
                v-bind="tastiera('email')"
                variant="outline"
                :placeholder="__('Email')"
              />
            </div>
            <button
              type="button"
              class="self-start text-p-sm text-ink-gray-5 hover:text-ink-gray-7 hover:underline"
              @click="row.manual = false"
            >
              {{ __('Search {brand} instead') }}
            </button>
          </div>
        </div>
        <Button
          v-if="form.participants.length > 1"
          variant="ghost"
          icon="lucide-x"
          :tooltip="__('Remove')"
          :aria-label="__('Remove')"
          @click="form.participants.splice(i, 1)"
        />
      </div>
      <div v-if="maxParticipants > 1" class="pl-[46px] pr-4.5">
        <Button
          variant="ghost"
          size="sm"
          iconLeft="plus"
          :label="
            __('Add a participant ({0}/{1})', [
              form.participants.length,
              maxParticipants,
            ])
          "
          :disabled="form.participants.length >= maxParticipants"
          @click="addParticipant"
        />
      </div>

      <div class="mx-4.5 my-2.5 border-t border-outline-gray-1" />

      <!-- when -->
      <div class="flex items-center gap-3 px-4.5 py-[7px] text-ink-gray-7">
        <CalendarIcon class="size-4 shrink-0" />
        <DatePicker
          class="w-full"
          variant="outline"
          :modelValue="form.date"
          format="ddd, D MMM YYYY"
          :clearable="false"
          @update:modelValue="setDate"
        />
      </div>
      <div class="flex items-center gap-3 px-4.5 py-[7px] text-ink-gray-7">
        <span class="lucide-clock size-4 shrink-0" aria-hidden="true" />
        <div class="flex w-full items-center gap-x-1.5">
          <TimePicker
            class="w-full"
            variant="outline"
            :modelValue="form.time"
            :placeholder="__('Start', null, 'Start time')"
            @update:modelValue="setStart"
          />
          <TimePicker
            class="w-full"
            variant="outline"
            :modelValue="form.end"
            :options="endOptions"
            :placeholder="__('End')"
            placement="bottom-end"
            @update:modelValue="setEnd"
          />
        </div>
      </div>
      <div class="pb-1 pl-[46px] pr-4.5">
        <div class="flex flex-wrap items-center gap-x-2 gap-y-1">
          <Button
            size="sm"
            variant="subtle"
            iconLeft="search"
            :label="__('Find a free time')"
            :loading="slots.loading"
            :disabled="!form.service"
            @click="findSlots"
          />
          <span v-if="slotHint" class="text-p-xs text-ink-gray-5">
            {{ slotHint }}
          </span>
        </div>
        <!-- a day at a time, as a booking app shows them: the day once, then
             its times; a day with many shows the first and the rest asked -->
        <div v-if="slotDays.length" class="mt-2 flex flex-col gap-2.5">
          <div v-for="day in slotDays" :key="day.giorno">
            <div
              class="mb-1 text-p-xs font-medium text-ink-gray-6 first-letter:uppercase"
            >
              {{ slotDayLabel(day.giorno) }}
            </div>
            <div class="flex flex-wrap gap-1.5">
              <Button
                v-for="slot in day.orari"
                :key="slot.start + (slot.join_appointment || '')"
                size="sm"
                variant="outline"
                class="tabular-nums"
                :label="slotLabel(slot)"
                @click="applySlot(slot)"
              />
              <Button
                v-if="day.altri"
                size="sm"
                variant="ghost"
                :label="__('{0} more', [day.altri], 'Free times')"
                @click="slotDaysOpen.add(day.giorno)"
              />
            </div>
          </div>
        </div>
      </div>

      <!-- with whom -->
      <div class="flex items-start gap-3 px-4.5 py-[7px] text-ink-gray-7">
        <span class="lucide-users mt-1.5 size-4 shrink-0" aria-hidden="true" />
        <div class="min-w-0 flex-1">
          <div v-if="eligibleStaff.length" class="flex flex-wrap gap-1.5">
            <Button
              v-for="person in eligibleStaff"
              :key="person.user"
              size="sm"
              :variant="isAssigned(person.user) ? 'solid' : 'outline'"
              :label="staffLabel(person)"
              :aria-pressed="isAssigned(person.user) ? 'true' : 'false'"
              @click="toggleStaff(person)"
            />
            <Button
              size="sm"
              variant="ghost"
              :label="__('Whoever is free')"
              :tooltip="__('Pick the professionals free at this time')"
              @click="autoAssign"
            />
          </div>
          <div v-else class="py-1.5 text-p-sm text-ink-gray-5">
            {{
              form.service
                ? __('Nobody delivers this service yet')
                : __('Pick a service to see who can deliver it')
            }}
          </div>
          <div v-if="staffHint" class="mt-1 text-p-xs text-ink-gray-5">
            {{ staffHint }}
          </div>
        </div>
      </div>

      <!-- where: only where there are rooms or equipment to book -->
      <div
        v-if="resourceChoices.length"
        class="flex items-start gap-3 px-4.5 py-[7px] text-ink-gray-7"
      >
        <span
          class="lucide-door-open mt-2 size-4 shrink-0"
          aria-hidden="true"
        />
        <div class="flex min-w-0 flex-1 flex-col gap-1.5">
          <div
            v-for="(row, i) in form.resources"
            :key="i"
            class="flex items-center gap-1.5"
          >
            <FormControl
              v-model="row.resource"
              class="min-w-0 flex-1"
              type="select"
              variant="outline"
              :options="resourceOptions"
            />
            <FormControl
              v-model.number="row.quantity"
              class="w-14"
              type="number"
              v-bind="tastiera('intero')"
              variant="outline"
              min="1"
              :aria-label="__('Quantity')"
            />
            <Button
              variant="ghost"
              icon="lucide-x"
              :aria-label="__('Remove')"
              @click="form.resources.splice(i, 1)"
            />
          </div>
          <Button
            variant="ghost"
            size="sm"
            class="self-start"
            iconLeft="plus"
            :label="__('Add a room or equipment')"
            @click="form.resources.push({ resource: '', quantity: 1 })"
          />
        </div>
      </div>

      <div class="flex items-center gap-3 px-4.5 py-[7px] text-ink-gray-7">
        <MapIcon class="size-4 shrink-0" />
        <TextInput
          v-model="form.location"
          class="w-full"
          variant="outline"
          :placeholder="__('Add a place or a meeting link')"
        />
      </div>
      <div class="flex items-start gap-3 px-4.5 py-[7px] text-ink-gray-7">
        <DescriptionIcon class="mt-2 size-4 shrink-0" />
        <Textarea
          v-model="form.notes"
          class="w-full"
          variant="outline"
          :rows="2"
          :placeholder="__('Add notes')"
        />
      </div>

      <div class="mx-4.5 my-2.5 border-t border-outline-gray-1" />

      <!-- how much -->
      <div
        v-if="form.service"
        class="flex items-start gap-3 px-4.5 py-[7px] text-ink-gray-7"
      >
        <span
          class="lucide-banknote mt-0.5 size-4 shrink-0"
          aria-hidden="true"
        />
        <div class="min-w-0 flex-1">
          <div class="flex items-center gap-1.5">
            <span class="text-ink-gray-8">{{ priceLabel }}</span>
            <span
              v-if="quote.loading"
              class="lucide-loader-circle size-3.5 animate-spin text-ink-gray-4"
              aria-hidden="true"
            />
          </div>
          <div v-if="quote.data?.source" class="text-p-sm text-ink-gray-5">
            {{ quote.data.source }}
          </div>
        </div>
      </div>

      <CollapsibleSection
        headerClass="mx-4.5 my-2.5"
        :opened="false"
        :label="__('More options')"
      >
        <div class="flex flex-col gap-2 px-4.5 pb-2">
          <FormControl
            v-model="form.status"
            type="select"
            variant="outline"
            :label="__('Status')"
            :options="statusOptions"
          />
          <FormControl
            v-if="priceListOptions.length > 1"
            v-model="form.price_list"
            type="select"
            variant="outline"
            :label="__('Price list')"
            :options="priceListOptions"
            @update:modelValue="refreshPrice"
          />
          <!-- what each client pays, when it is not the list price -->
          <div
            v-for="row in form.participants.filter(
              (one) => one.party || one.participant_name,
            )"
            :key="`amount-${row.key}`"
            class="flex items-center gap-2"
          >
            <span class="min-w-0 flex-1 truncate text-p-sm text-ink-gray-6">
              {{ row.participant_name || row.party }}
            </span>
            <FormControl
              v-model="row.status"
              class="w-28"
              type="select"
              variant="outline"
              size="sm"
              :options="attendanceOptions"
            />
            <FormControl
              v-model.number="row.amount"
              class="w-24"
              type="number"
              variant="outline"
              size="sm"
              :aria-label="__('Amount')"
            >
              <template #prefix>
                <span class="text-p-sm text-ink-gray-5">{{
                  currencySymbol
                }}</span>
              </template>
            </FormControl>
          </div>
        </div>
      </CollapsibleSection>

      <!-- a clash, said before saving rather than after -->
      <div
        v-if="conflicts.length"
        class="mx-4.5 mb-2 mt-1 rounded-md bg-surface-red-1 px-3 py-2 ring-1 ring-inset ring-outline-red-2"
      >
        <div class="text-p-sm font-medium text-ink-red-8">
          {{ __('Scheduling conflict') }}
        </div>
        <ul class="mt-1 list-inside list-disc text-p-xs text-ink-red-8">
          <li v-for="(conflict, i) in conflicts" :key="i">{{ conflict }}</li>
        </ul>
        <label
          v-if="canOverride"
          class="mt-2 flex items-center gap-2 text-p-xs text-ink-gray-7"
        >
          <Switch v-model="form.override_conflicts" size="sm" />
          {{ __('Book anyway and record the conflict') }}
        </label>
      </div>
    </div>

    <div v-if="mode !== 'details'" class="px-4.5 py-3">
      <ErrorMessage class="mb-2" :message="error" />
      <Button
        variant="solid"
        class="w-full"
        :loading="saving"
        :label="mode === 'new' ? __('Book appointment') : __('Save')"
        @click="save"
      />
    </div>
  </div>
</template>

<script setup>
import CalendarIcon from '@/components/Icons/CalendarIcon.vue'
import DescriptionIcon from '@/components/Icons/DescriptionIcon.vue'
import MapIcon from '@/components/Icons/MapIcon.vue'
import CollapsibleSection from '@/components/CollapsibleSection.vue'
import Link from '@/components/Controls/Link.vue'
import UserAvatar from '@/components/UserAvatar.vue'
import { buildEndTimeOptions } from '@/composables/event'
import { globalStore } from '@/stores/global'
import { usersStore } from '@/stores/users'
import { rigaDelPosto } from '@/utils/abbonamenti'
import { laSeduta } from '@/utils/cicli'
import { appLocale } from '@/utils/locale'
import {
  adessoDelCentro,
  addMinutes,
  minutesBetween,
  oggiDelCentro,
  oraDelCentro,
  orariPerGiorno,
  sulCentro,
} from '@/utils/scheduler'
import { tastiera } from '@/utils/tastiera'
import { leggibile } from '@/utils/telefono'
import {
  Badge,
  Button,
  DatePicker,
  Dropdown,
  ErrorMessage,
  FormControl,
  Switch,
  TextInput,
  Textarea,
  TimePicker,
  createResource,
  dayjs,
  toast,
} from 'frappe-ui'
import { computed, reactive, ref, watch } from 'vue'
import { useRouter } from 'vue-router'

const props = defineProps({
  // details, edit, or new
  mode: { type: String, default: 'details' },
  // the appointment, for details and edit
  name: { type: String, default: '' },
  // for a new one: { date, time, staff, resource, service, party }
  seed: { type: Object, default: () => ({}) },
  meta: { type: Object, default: () => ({}) },
})

// `mode`: the panel asks to be read or edited; `saved` carries the appointment
const emit = defineEmits(['close', 'mode', 'saved', 'deleted'])

const router = useRouter()
const { $dialog } = globalStore()
const { getUser } = usersStore()

const STATUSES = ['Scheduled', 'Confirmed', 'Completed', 'No Show', 'Cancelled']
// grey for cancelled, as its block on the calendar is
const STATUS_THEME = {
  Scheduled: 'blue',
  Confirmed: 'green',
  Completed: 'gray',
  'No Show': 'red',
  Cancelled: 'gray',
}
// «Arrived» is the desk's check-in: in the waiting room, not yet seen
const ATTENDANCE = ['Booked', 'Arrived', 'Attended', 'No Show', 'Cancelled']

// --- the appointment as it is ---------------------------------------------

// what the server has, for reading; `form` is what is being edited
const doc = ref(null)

const appointment = createResource({
  url: 'crm.api.appointments.get_appointment',
})

function load(name) {
  doc.value = null
  // another appointment, or the series just made: the repeat row closed again,
  // and no question about cancelling left open
  repeatOpen.value = false
  repeat.rule = ''
  cancelling.open = false
  appointment.submit(
    { name },
    {
      onSuccess: (data) => {
        doc.value = data
        // asked to edit (a double click) one it may not change: it reads
        if (props.mode === 'edit' && !data.can_write) emit('mode', 'details')
        else if (props.mode !== 'details') loadInto(data)
      },
      onError: (e) => {
        toast.error(e.messages?.[0] || __('Could not open the appointment'))
        emit('close')
      },
    },
  )
}

const services = computed(() => props.meta?.services || [])

function serviceOf(name) {
  return services.value.find((one) => one.name === name)
}

const serviceName = computed(
  () => serviceOf(doc.value?.service)?.service_name || doc.value?.service || '',
)
const serviceColor = computed(
  () => doc.value?.color || serviceOf(doc.value?.service)?.color || '',
)

const clientNames = computed(() =>
  (doc.value?.participants || [])
    .filter(
      (row) => row.status !== 'Cancelled' || doc.value.status === 'Cancelled',
    )
    .map((row) => row.participant_name || row.party)
    .filter(Boolean)
    .join(', '),
)

const whenLabel = computed(() => {
  if (!doc.value) return ''
  const start = dayjs(doc.value.starts_on)
  const end = dayjs(doc.value.ends_on)
  return `${start.format('ddd D MMM YYYY')} · ${start.format('HH:mm')} – ${end.format('HH:mm')}`
})

const heading = computed(() => {
  if (props.mode === 'new') return __('New appointment')
  if (props.mode === 'edit') return __('Edit appointment')
  return __('Appointment')
})

function personName(user) {
  return getUser(user)?.full_name || user
}

function resourceSummary(rows) {
  return rows
    .map((row) => {
      const resource = (props.meta?.resources || []).find(
        (one) => one.name === row.resource,
      )
      const label = resource?.resource_name || row.resource
      return row.quantity > 1 ? `${label} ×${row.quantity}` : label
    })
    .join(', ')
}

function money(amount, currency) {
  return new Intl.NumberFormat(appLocale(), {
    style: 'currency',
    currency: currency || 'EUR',
  }).format(amount || 0)
}

function openPerson(lead) {
  router.push({ name: 'Lead', params: { leadId: lead } })
}

// --- quick changes while reading --------------------------------------------

const changing = ref(false)

function apply(url, params, done) {
  changing.value = true
  createResource({
    url,
    params,
    auto: true,
    onSuccess: (data) => {
      changing.value = false
      doc.value = data
      emit('saved', data)
      done?.(data)
    },
    onError: (e) => {
      changing.value = false
      toast.error(e.messages?.[0] || __('Could not change it'))
    },
  })
}

const statusActions = computed(() =>
  STATUSES.filter((status) => status !== doc.value?.status).map((status) => ({
    label: __(status),
    onClick: () =>
      status === 'Cancelled'
        ? askToCancel()
        : apply(
            'crm.api.appointments.set_status',
            { name: doc.value.name, status },
            () =>
              toast.success(__('Marked as {0}', [__(status).toLowerCase()])),
          ),
  })),
)

const cancelling = reactive({ open: false, reason: '' })

function askToCancel() {
  cancelling.reason = ''
  cancelling.open = true
}

function cancelIt() {
  apply(
    'crm.api.appointments.set_status',
    {
      name: doc.value.name,
      status: 'Cancelled',
      reason: cancelling.reason.trim() || null,
    },
    () => {
      cancelling.open = false
      toast.success(__('Appointment cancelled'))
    },
  )
}

function attendanceActions(row) {
  return ATTENDANCE.filter((status) => status !== (row.status || 'Booked')).map(
    (status) => ({
      label: __(status),
      onClick: () =>
        apply('crm.api.appointments.set_participant_status', {
          name: doc.value.name,
          participant: row.name,
          status,
        }),
    }),
  )
}

// --- its cycle of sessions ----------------------------------------------------

const cycleLine = computed(() => {
  const cycle = doc.value?.cycle
  if (!cycle) return ''
  if (!cycle.cycle) return __('Not in a cycle of sessions')
  return (
    laSeduta(cycle, (text, args) => __(text, args)) ||
    __('In a cycle, not counted')
  )
})

const cycleActions = computed(() => {
  const cycle = doc.value?.cycle
  if (!cycle) return []
  const people = new Set((cycle.options || []).map((one) => one.lead_name))
  const actions = (cycle.options || [])
    .filter((one) => one.name !== cycle.cycle)
    .map((one) => ({
      label: __('Into the cycle from {0} ({1} to book)', [
        (people.size > 1 ? `${one.lead_name}, ` : '') +
          dayjs(one.starts_on).format('D MMM'),
        one.left,
      ]),
      onClick: () => moveToCycle(one.name),
    }))
  if (cycle.cycle)
    actions.push({
      label: __('Out of the cycle'),
      onClick: () => moveToCycle(null),
    })
  return actions
})

function moveToCycle(cycle) {
  changing.value = true
  createResource({
    url: 'crm.scheduling.cicli.attach',
    params: { appointment: doc.value.name, cycle },
    auto: true,
    onSuccess: () => {
      changing.value = false
      toast.success(
        cycle ? __('Now a session of the cycle') : __('Out of the cycle'),
      )
      load(doc.value.name)
    },
    onError: (e) => {
      changing.value = false
      toast.error(e.messages?.[0] || __('Could not change it'))
    },
  })
}

// --- its subscription --------------------------------------------------------

// a class: each line says whose place it is
const manyPeople = computed(
  () =>
    (doc.value?.participants || []).filter(
      (row) => row.party_type === 'CRM Lead',
    ).length > 1,
)

function subscriptionLine(who) {
  return rigaDelPosto(who, manyPeople.value, __)
}

function subscriptionActions(who) {
  const actions = (who.options || [])
    .filter((one) => one.name !== who.subscription)
    .map((one) => ({
      label: __('An entry of {0}', [one.type]),
      onClick: () => moveToSubscription(who, one.name),
    }))
  if (who.subscription)
    actions.push({
      label: __('Out of the subscription'),
      onClick: () => moveToSubscription(who, null),
    })
  return actions
}

function moveToSubscription(who, subscription) {
  changing.value = who.party
  createResource({
    url: 'crm.scheduling.abbonamenti.attach',
    params: { appointment: doc.value.name, subscription, party: who.party },
    auto: true,
    onSuccess: () => {
      changing.value = false
      toast.success(
        subscription
          ? __('Now an entry of the subscription')
          : __('Out of the subscription'),
      )
      load(doc.value.name)
    },
    onError: (e) => {
      changing.value = false
      toast.error(e.messages?.[0] || __('Could not change it'))
    },
  })
}

// --- repeating -------------------------------------------------------------

const repeat = reactive({ rule: '', occurrences: 4 })
const repeatOpen = ref(false)
const repeating = ref(false)
const repeatOptions = [
  { label: __('Does not repeat'), value: '' },
  { label: __('Every day'), value: 'Daily' },
  { label: __('Every week'), value: 'Weekly' },
  { label: __('Every 2 weeks'), value: 'Biweekly' },
  { label: __('Every month'), value: 'Monthly' },
]

function createSeries() {
  repeating.value = true
  createResource({
    url: 'crm.api.appointments.create_series',
    params: {
      name: doc.value.name,
      repeat: repeat.rule,
      occurrences: repeat.occurrences,
    },
    auto: true,
    onSuccess: (data) => {
      repeating.value = false
      repeat.rule = ''
      const created = data.created?.length || 0
      const skipped = data.skipped?.length || 0
      toast.success(
        skipped
          ? __('{0} appointments created, {1} skipped for conflicts', [
              created,
              skipped,
            ])
          : __('{0} appointments created', [created]),
      )
      load(doc.value.name)
      emit('saved', doc.value)
    },
    onError: (e) => {
      repeating.value = false
      toast.error(e.messages?.[0] || __('Could not create the series'))
    },
  })
}

// --- the form --------------------------------------------------------------

let keys = 0
const emptyForm = () => ({
  name: null,
  service: '',
  status: 'Scheduled',
  date: oggiDelCentro(),
  time: '09:00',
  end: '09:30',
  staff: [],
  participants: [],
  resources: [],
  price_list: '',
  location: '',
  notes: '',
  override_conflicts: false,
})

const form = reactive(emptyForm())
const saving = ref(false)
const error = ref('')
const conflicts = ref([])
const slotList = ref([])
const slotHint = ref('')
// the days whose every time was asked for («3 more»)
const slotDaysOpen = reactive(new Set())
// a free time comes as a UTC instant: its day and hour on the centre's clock,
// as the agenda shows the appointments (utils/scheduler.js, sulCentro)
const fusoDelCentro = window.timezone?.system || null
const delCentro = (istante) => sulCentro(istante, fusoDelCentro)
const slotDays = computed(() =>
  orariPerGiorno(slotList.value, {
    perGiorno: 12,
    giorni: 5,
    giornoDi: (slot) => delCentro(slot.start)?.giorno,
  }).map((day) =>
    slotDaysOpen.has(day.giorno)
      ? {
          ...day,
          orari: slotList.value.filter(
            (slot) => delCentro(slot.start)?.giorno === day.giorno,
          ),
          altri: 0,
        }
      : day,
  ),
)
// what the form held when it was opened, to know whether leaving loses anything
const opened = ref('')

const service = computed(() => serviceOf(form.service))
const formServiceColor = computed(() => service.value?.color || '')
const canOverride = computed(() => Boolean(props.meta?.settings?.can_override))

const serviceOptions = computed(() => [
  ...(form.service ? [] : [{ label: __('Choose a service…'), value: '' }]),
  ...services.value.map((one) => ({
    label: `${one.service_name} · ${one.duration} ${__('min')}`,
    value: one.name,
  })),
])
const resourceChoices = computed(() => props.meta?.resources || [])
const resourceOptions = computed(() => [
  { label: __('Choose…'), value: '' },
  ...resourceChoices.value.map((one) => ({
    label: `${one.resource_name} (${__(one.resource_type)})`,
    value: one.name,
  })),
])
const priceListOptions = computed(() => [
  { label: __('Default'), value: '' },
  ...(props.meta?.price_lists || []).map((one) => ({
    label: one.price_list_name,
    value: one.name,
  })),
])
const statusOptions = STATUSES.map((status) => ({
  label: __(status),
  value: status,
}))
const attendanceOptions = ATTENDANCE.map((status) => ({
  label: __(status),
  value: status,
}))

const eligibleStaff = computed(() => service.value?.staff || [])
const maxParticipants = computed(() => service.value?.max_participants || 1)

const serviceSummary = computed(() => {
  if (!service.value) return ''
  const parts = []
  if (service.value.staff_selection === 'All required') {
    parts.push(__('all its professionals together'))
  } else if (service.value.staff_selection === 'One per role') {
    parts.push(__('one professional per role'))
  } else if (service.value.staff_count > 1) {
    parts.push(__('{0} professionals', [service.value.staff_count]))
  }
  if (service.value.max_participants > 1) {
    parts.push(__('up to {0} people', [service.value.max_participants]))
  }
  return parts.join(' · ')
})

const staffHint = computed(() => {
  if (service.value?.staff_selection === 'All required') {
    return __('This service books every listed professional together.')
  }
  if (service.value?.staff_selection === 'One per role') {
    return __('One professional per role is needed.')
  }
  return ''
})

const endOptions = computed(() => buildEndTimeOptions(form.time))

const startsOn = computed(() =>
  dayjs(`${form.date} ${form.time}`, 'YYYY-MM-DD HH:mm').toDate(),
)
const endsOn = computed(() =>
  dayjs(`${form.date} ${form.end}`, 'YYYY-MM-DD HH:mm').toDate(),
)

function setDate(value) {
  if (value) form.date = dayjs(value).format('YYYY-MM-DD')
}

// moving the start keeps the length: a 45-minute session stays 45 minutes
function setStart(value) {
  if (!value) return
  const length =
    minutesBetween(form.time, form.end) || service.value?.duration || 30
  form.time = value
  form.end = addMinutes(value, length)
}

function setEnd(value) {
  if (value) form.end = value
}

const quote = createResource({ url: 'crm.api.appointments.quote_price' })
const slots = createResource({
  url: 'crm.api.appointments.get_available_slots',
})
const conflictCheck = createResource({
  url: 'crm.api.appointments.check_conflicts',
})

const currencySymbol = computed(
  () =>
    new Intl.NumberFormat(appLocale(), {
      style: 'currency',
      currency: quote.data?.currency || 'EUR',
    })
      .formatToParts(0)
      .find((part) => part.type === 'currency')?.value || '',
)

const priceLabel = computed(() => {
  const data = quote.data
  if (!data) return '—'
  const total = money(data.total, data.currency)
  return data.per_participant
    ? `${total} (${__('per participant')} × ${form.participants.length || 1})`
    : total
})

function payload() {
  return {
    service: form.service,
    status: form.status,
    // the centre's clock, as every page reads it back
    starts_on: oraDelCentro(startsOn.value),
    ends_on: oraDelCentro(endsOn.value),
    staff: form.staff.map((user) => ({ user, required: 1 })),
    participants: form.participants
      .filter((row) => row.party || row.participant_name)
      // what the form keeps for itself stays here
      .map((row) => {
        const copy = { ...row }
        delete copy.key
        delete copy.manual
        return copy
      }),
    resources: form.resources.filter((row) => row.resource),
    price_list: form.price_list || null,
    location: form.location,
    notes: form.notes,
    override_conflicts: form.override_conflicts ? 1 : 0,
  }
}

function snapshot() {
  return JSON.stringify(payload())
}

function refreshPrice() {
  if (!form.service) return
  quote.submit({
    service: form.service,
    when: oraDelCentro(startsOn.value),
    price_list: form.price_list || null,
    staff: form.staff,
    resources: form.resources.map((row) => row.resource).filter(Boolean),
    participants: form.participants.length || 1,
  })
}

function refreshConflicts() {
  if (!form.service || !form.staff.length) {
    conflicts.value = []
    return
  }
  conflictCheck.submit(
    { appointment: { ...payload(), name: form.name } },
    { onSuccess: (data) => (conflicts.value = data || []) },
  )
}

function findSlots() {
  if (!form.service) return
  slotHint.value = ''
  slots.submit(
    {
      service: form.service,
      start_date: form.date,
      end_date: dayjs(form.date).add(6, 'day').format('YYYY-MM-DD'),
      staff: form.staff,
      resources: form.resources.map((row) => row.resource).filter(Boolean),
      participants: Math.max(form.participants.length, 1),
      exclude_appointment: form.name || null,
    },
    {
      onSuccess: (data) => {
        slotDaysOpen.clear()
        slotList.value = data || []
        slotHint.value = slotList.value.length
          ? __('{0} free times in the next 7 days', [data.length])
          : __('No free time in the next 7 days')
      },
      onError: (e) =>
        toast.error(e.messages?.[0] || __('Could not load free times')),
    },
  )
}

// the time alone: the day is said once, above its times
function slotLabel(slot) {
  const when = delCentro(slot.start)?.ora || ''
  return slot.join_appointment
    ? `${when} · ${__('join')} (${slot.seats_left})`
    : when
}

function slotDayLabel(day) {
  return dayjs(day).format('dddd D MMMM')
}

function applySlot(slot) {
  const inizio = delCentro(slot.start)
  const fine = delCentro(slot.end)
  if (!inizio || !fine) return
  form.date = inizio.giorno
  form.time = inizio.ora
  form.end = fine.ora
  form.staff = [...(slot.staff || [])]
  if (slot.resources?.length) {
    form.resources = slot.resources.map((row) => ({ ...row }))
  }
  slotList.value = []
  slotHint.value = ''
}

function staffLabel(person) {
  const name = personName(person.user)
  return person.role ? `${name} · ${person.role}` : name
}

function isAssigned(user) {
  return form.staff.includes(user)
}

function toggleStaff(person) {
  const i = form.staff.indexOf(person.user)
  if (i === -1) form.staff.push(person.user)
  else form.staff.splice(i, 1)
}

function autoAssign() {
  if (!form.service) return
  slots.submit(
    {
      service: form.service,
      start_date: form.date,
      end_date: form.date,
      participants: Math.max(form.participants.length, 1),
      exclude_appointment: form.name || null,
    },
    {
      onSuccess: (data) => {
        const wanted = `${form.date} ${form.time}`
        const match =
          (data || []).find((slot) => {
            const inizio = delCentro(slot.start)
            return inizio && `${inizio.giorno} ${inizio.ora}` === wanted
          }) || null
        if (!match) {
          toast.error(__('Nobody is free at this time'))
          return
        }
        form.staff = [...(match.staff || [])]
        if (
          match.resources?.length &&
          !form.resources.some((r) => r.resource)
        ) {
          form.resources = match.resources.map((row) => ({ ...row }))
        }
      },
    },
  )
}

function participantRow(values = {}) {
  keys += 1
  return {
    key: keys,
    manual: false,
    party_type: 'CRM Lead',
    party: '',
    participant_name: '',
    email: '',
    phone: '',
    status: 'Booked',
    amount: 0,
    ...values,
  }
}

function addParticipant() {
  form.participants.push(participantRow())
}

const partyDetails = createResource({
  url: 'crm.persone.collegate.get_contact_for',
})

function pickParty(row, value) {
  row.party_type = 'CRM Lead'
  row.party = value || ''
  if (!value) {
    row.participant_name = ''
    row.email = ''
    row.phone = ''
    row.booked_by = ''
    row.booked_by_name = ''
    return
  }
  // a child without a contact of their own is reached through whoever books for
  // them: the reminders go to the parent
  partyDetails.submit(
    { lead: value },
    {
      onSuccess: (data) => {
        row.participant_name = data?.lead_name || value
        row.email = data?.email || ''
        row.phone = data?.phone || ''
        row.booked_by = data?.booked_by || ''
        row.booked_by_name = data?.booked_by_name || ''
      },
      onError: () => (row.participant_name = value),
    },
  )
}

function loadInto(data) {
  Object.assign(form, emptyForm(), {
    name: data.name,
    service: data.service,
    status: data.status,
    date: dayjs(data.starts_on).format('YYYY-MM-DD'),
    time: dayjs(data.starts_on).format('HH:mm'),
    end: dayjs(data.ends_on).format('HH:mm'),
    staff: (data.staff || []).map((row) => row.user),
    participants: (data.participants || []).map((row) =>
      participantRow({
        party_type: row.party_type || 'CRM Lead',
        party: row.party || '',
        participant_name: row.participant_name || '',
        email: row.email || '',
        phone: row.phone || '',
        status: row.status || 'Booked',
        amount: row.amount || 0,
        booked_by: row.booked_by || '',
        booked_by_name: row.booked_by_name || '',
        manual: !row.party && Boolean(row.participant_name),
      }),
    ),
    resources: (data.resources || []).map((row) => ({
      resource: row.resource,
      quantity: row.quantity || 1,
    })),
    price_list: data.price_list || '',
    location: data.location || '',
    notes: data.notes || '',
    override_conflicts: Boolean(data.override_conflicts),
  })
  if (!form.participants.length) addParticipant()
  afterOpen()
}

function seedForm() {
  const seed = props.seed || {}
  doc.value = null
  Object.assign(form, emptyForm(), {
    date: seed.date || oggiDelCentro(),
    time: seed.time || dayjs(adessoDelCentro()).format('HH:mm'),
    price_list: props.meta?.settings?.default_price_list || '',
  })
  const preferred =
    seed.service || (services.value.length === 1 ? services.value[0].name : '')
  if (preferred) onServiceChange(preferred)
  else
    form.end = addMinutes(
      form.time,
      props.meta?.settings?.default_duration || 30,
    )
  if (seed.staff) form.staff = [seed.staff]
  if (seed.resource) form.resources = [{ resource: seed.resource, quantity: 1 }]
  addParticipant()
  if (seed.party) pickParty(form.participants[0], seed.party)
  afterOpen()
}

function afterOpen() {
  error.value = ''
  conflicts.value = []
  slotList.value = []
  slotHint.value = ''
  refreshPrice()
  refreshConflicts()
  opened.value = snapshot()
}

function onServiceChange(value) {
  form.service = value
  const picked = serviceOf(value)
  if (!picked) return
  form.end = addMinutes(form.time, picked.duration || 30)
  // a service delivered by everyone together books them all; otherwise it
  // waits for the pick, keeping whoever can deliver this one too
  form.staff =
    picked.staff_selection === 'All required'
      ? (picked.staff || []).map((row) => row.user)
      : form.staff.filter((user) =>
          (picked.staff || []).some((row) => row.user === user),
        )
  if ((picked.staff || []).length === 1 && !form.staff.length) {
    form.staff = [picked.staff[0].user]
  }
  if (!form.resources.length && picked.resources?.length) {
    form.resources = picked.resources
      .filter((row) => row.resource)
      .map((row) => ({ resource: row.resource, quantity: row.quantity || 1 }))
  }
  while (form.participants.length > (picked.max_participants || 1)) {
    form.participants.pop()
  }
}

watch(
  () => [
    form.service,
    form.date,
    form.time,
    form.end,
    form.staff.join(),
    form.resources.map((row) => row.resource).join(),
    form.participants.length,
  ],
  () => {
    if (props.mode === 'details') return
    refreshPrice()
    refreshConflicts()
  },
)

function save() {
  error.value = ''
  if (!form.service) {
    error.value = __('Pick a service')
    return
  }
  if (!form.participants.some((row) => row.party || row.participant_name)) {
    error.value = __('Say who it is for')
    return
  }
  if (minutesBetween(form.time, form.end) <= 0) {
    error.value = __('It has to end after it starts')
    return
  }
  if (!form.staff.length) {
    error.value = __('Assign at least one professional')
    return
  }
  saving.value = true
  createResource({
    url: 'crm.api.appointments.save_appointment',
    params: { appointment: payload(), name: form.name || null },
    auto: true,
    onSuccess: (data) => {
      saving.value = false
      toast.success(
        form.name ? __('Appointment updated') : __('Appointment booked'),
      )
      doc.value = data
      opened.value = snapshot()
      emit('saved', data)
      emit('mode', 'details', data.name)
    },
    onError: (e) => {
      saving.value = false
      error.value = e.messages?.[0] || __('Could not save the appointment')
      refreshConflicts()
    },
  })
}

// --- leaving ---------------------------------------------------------------

function discardFirst(then) {
  if (props.mode === 'details' || snapshot() === opened.value) return then()
  $dialog({
    title: __('Discard unsaved changes?'),
    message: __('What you changed in this appointment will be lost.'),
    actions: [
      { label: __('Keep editing'), onClick: (closeDialog) => closeDialog() },
      {
        label: __('Discard'),
        variant: 'solid',
        onClick: (closeDialog) => {
          closeDialog()
          then()
        },
      },
    ],
  })
}

function close() {
  discardFirst(() => emit('close'))
}

function backToDetails() {
  discardFirst(() => emit('mode', 'details'))
}

function confirmDelete() {
  $dialog({
    title: __('Delete this appointment?'),
    message: __(
      'It is removed from the calendar, and from the calendars it was synced to. To keep a record of it, cancel it instead.',
    ),
    actions: [
      {
        label: __('Cancel it instead'),
        onClick: (closeDialog) => {
          closeDialog()
          askToCancel()
        },
      },
      {
        label: __('Delete'),
        variant: 'solid',
        theme: 'red',
        onClick: (closeDialog) => {
          closeDialog()
          createResource({
            url: 'crm.api.appointments.delete_appointment',
            params: { name: doc.value.name },
            auto: true,
            onSuccess: () => {
              toast.success(__('Appointment deleted'))
              emit('deleted', doc.value.name)
            },
            onError: (e) =>
              toast.error(e.messages?.[0] || __('Could not delete it')),
          })
        },
      },
    ],
  })
}

// --- opening ---------------------------------------------------------------

watch(
  () => [props.mode, props.name, props.seed],
  ([mode, name, seed], before) => {
    const [oldMode, , oldSeed] = before || []
    if (mode === 'new') {
      if (oldMode !== 'new' || seed !== oldSeed) seedForm()
      return
    }
    if (!name) return
    // a different appointment is fetched; the same one, read or edited, or
    // just saved, is already here
    if (doc.value?.name !== name) {
      load(name)
      return
    }
    if (mode === 'edit' && oldMode !== 'edit') {
      if (doc.value?.can_write) loadInto(doc.value)
      else if (doc.value) emit('mode', 'details')
    }
  },
  { immediate: true },
)

defineExpose({ close })
</script>
