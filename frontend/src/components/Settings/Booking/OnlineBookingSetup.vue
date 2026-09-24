<template>
  <div
    class="flex h-full flex-col gap-6 px-4 py-6 sm:px-6 sm:py-8 text-ink-gray-8"
  >
    <div
      class="flex flex-col items-stretch gap-3 px-2 sm:flex-row sm:items-start sm:justify-between sm:gap-4"
    >
      <div class="flex flex-col gap-1">
        <h2 class="flex gap-2 text-2xl-semibold leading-none h-5">
          {{ __('Online booking') }}
        </h2>
        <p class="text-p-base text-ink-gray-6">
          {{
            __(
              'Who clients can book, and for what. Every switch here applies at once.',
            )
          }}
        </p>
      </div>
      <Button
        :label="__('Why can\'t they book?')"
        icon-left="lucide-search-check"
        @click="showCheck = true"
      />
    </div>

    <div
      v-if="setup.data"
      class="flex flex-1 flex-col gap-6 overflow-y-auto px-2 pb-4"
    >
      <!-- 1. the page -->
      <section
        class="flex flex-col gap-3 rounded-lg border border-outline-gray-2 p-4"
      >
        <label class="flex items-center justify-between gap-4">
          <span class="flex flex-col gap-0.5">
            <span class="text-p-base-medium text-ink-gray-8">
              {{ __('Clients can book online') }}
            </span>
            <span class="text-p-sm text-ink-gray-6">
              {{
                setup.data.open
                  ? __('The booking page is open to everyone with the link.')
                  : __('The booking page is closed: nobody can book online.')
              }}
            </span>
          </span>
          <Switch
            :modelValue="setup.data.open"
            :disabled="busy"
            @update:modelValue="
              (v) => run('set_booking_open', { enabled: v ? 1 : 0 })
            "
          />
        </label>
        <div v-if="setup.data.open" class="flex items-end gap-2">
          <CopyRow class="flex-1" :label="__('Link')" :value="pageUrl" />
          <Button
            variant="ghost"
            icon="lucide-external-link"
            :tooltip="__('Open')"
            :link="pageUrl"
          />
        </div>
      </section>

      <!-- 2. the services -->
      <section class="flex flex-col gap-2">
        <div class="flex items-baseline justify-between">
          <h3 class="text-p-base-medium text-ink-gray-8">
            {{ __('Services clients can book') }}
          </h3>
          <span class="text-p-sm text-ink-gray-5">
            {{
              __('{0} of {1} online', [onlineServices.length, services.length])
            }}
          </span>
        </div>
        <div
          v-if="services.length"
          class="divide-y divide-outline-gray-1 rounded-lg border border-outline-gray-2"
        >
          <label
            v-for="service in services"
            :key="service.name"
            class="flex cursor-pointer items-center gap-3 px-3 py-2 hover:bg-surface-gray-1"
          >
            <span
              class="size-2.5 shrink-0 rounded-full"
              :style="{ backgroundColor: service.color || '#4C7EFF' }"
            />
            <span class="min-w-0 flex-1 truncate text-p-base text-ink-gray-8">
              {{ service.service_name }}
            </span>
            <span
              v-if="service.bookable_online"
              class="text-p-sm"
              :class="
                service.online_staff ? 'text-ink-gray-6' : 'text-ink-amber-8'
              "
            >
              {{
                service.online_staff
                  ? __('{0} bookable', [service.online_staff])
                  : __('Nobody bookable for it')
              }}
            </span>
            <Switch
              :modelValue="Boolean(service.bookable_online)"
              :disabled="busy"
              @update:modelValue="
                (v) =>
                  run('set_service_online', {
                    service: service.name,
                    online: v ? 1 : 0,
                  })
              "
            />
          </label>
        </div>
        <p v-else class="text-p-sm text-ink-gray-6">
          {{ __('No services yet. Create them in Agenda → Services.') }}
        </p>
      </section>

      <!-- 3. the people -->
      <section class="flex flex-col gap-2">
        <div class="flex items-baseline justify-between">
          <h3 class="text-p-base-medium text-ink-gray-8">
            {{ __('People clients can book') }}
          </h3>
          <span class="text-p-sm text-ink-gray-5">
            {{ __('Tap a service to turn it on or off for that person') }}
          </span>
        </div>
        <div
          class="divide-y divide-outline-gray-1 rounded-lg border border-outline-gray-2"
        >
          <div
            v-for="person in setup.data.team"
            :key="person.user"
            class="flex flex-col gap-2 px-3 py-3"
          >
            <div class="flex items-center gap-3">
              <UserAvatar :user="person.user" size="md" class="shrink-0" />
              <div class="min-w-0 flex-1">
                <div class="flex items-baseline gap-2">
                  <span class="truncate text-p-base-medium text-ink-gray-8">
                    {{ person.full_name }}
                  </span>
                  <span
                    v-if="person.public_title"
                    class="truncate text-p-sm text-ink-gray-5"
                  >
                    {{ person.public_title }}
                  </span>
                </div>
                <div
                  class="flex items-center gap-1 text-p-sm"
                  :class="
                    person.bookable.length
                      ? 'text-ink-green-8'
                      : 'text-ink-gray-6'
                  "
                >
                  <span
                    class="size-3.5 shrink-0"
                    :class="
                      person.bookable.length
                        ? 'lucide-circle-check'
                        : 'lucide-circle-minus'
                    "
                  />
                  {{
                    person.bookable.length
                      ? __('Bookable online for {0}', [
                          countLabel(person.bookable.length),
                        ])
                      : person.reason
                  }}
                </div>
              </div>
              <Button
                variant="ghost"
                size="sm"
                :label="__('Profile')"
                :tooltip="__('Title and bio on the booking page')"
                @click="editProfile(person)"
              />
              <Switch
                :modelValue="person.online"
                :disabled="busy"
                @update:modelValue="
                  (v) =>
                    run('set_person_online', {
                      user: person.user,
                      online: v ? 1 : 0,
                    })
                "
              />
            </div>
            <div
              v-if="person.online && onlineServices.length"
              class="flex flex-wrap gap-1.5 pl-11"
            >
              <button
                v-for="service in onlineServices"
                :key="service.name"
                class="flex h-7 items-center gap-1.5 rounded-full border px-2.5 text-p-sm transition-colors"
                :class="
                  takes(person, service)
                    ? 'border-outline-green-3 bg-surface-green-1 text-ink-green-8'
                    : 'border-dashed border-outline-gray-3 text-ink-gray-6 hover:border-outline-gray-4 hover:text-ink-gray-8'
                "
                :disabled="busy"
                @click="toggle(person, service)"
              >
                <span
                  class="size-3.5"
                  :class="
                    takes(person, service) ? 'lucide-check' : 'lucide-plus'
                  "
                />
                {{ service.service_name }}
              </button>
            </div>
            <p
              v-else-if="person.online"
              class="pl-11 text-p-sm text-ink-gray-5"
            >
              {{ __('Turn a service on above first.') }}
            </p>
          </div>
        </div>
        <p class="text-p-sm text-ink-gray-5">
          {{
            __(
              'Hours and days off: Agenda → Team rota. Own price or length for a service: Agenda → Services.',
            )
          }}
        </p>
      </section>
    </div>
  </div>

  <Dialog
    v-model="showProfile"
    :options="{ title: __('{0} on the booking page', [profile.full_name]) }"
  >
    <template #body-content>
      <div class="flex flex-col gap-3">
        <FormControl
          v-model="profile.public_title"
          type="text"
          :label="__('Title')"
          :placeholder="__('e.g. Physiotherapist')"
        />
        <FormControl
          v-model="profile.public_bio"
          type="textarea"
          :rows="3"
          :label="__('Short bio')"
          :placeholder="__('A line clients read before choosing them')"
        />
      </div>
    </template>
    <template #actions>
      <Button
        class="w-full"
        variant="solid"
        :label="__('Save')"
        :loading="busy"
        @click="saveProfile"
      />
    </template>
  </Dialog>

  <Dialog
    v-model="showCheck"
    :options="{ title: __('Why can\'t they book?'), size: '4xl' }"
  >
    <template #body-content>
      <div class="max-h-[70vh] overflow-y-auto">
        <AvailabilityCheck embedded />
      </div>
    </template>
  </Dialog>
</template>

<script setup>
import UserAvatar from '@/components/UserAvatar.vue'
import AvailabilityCheck from '@/components/Settings/Booking/AvailabilityCheck.vue'
import CopyRow from '@/components/Settings/Booking/CopyRow.vue'
import {
  createResource,
  call,
  Dialog,
  FormControl,
  Switch,
  toast,
} from 'frappe-ui'
import { computed, reactive, ref } from 'vue'

const setup = createResource({
  url: 'crm.api.booking_admin.get_online_setup',
  auto: true,
})

const busy = ref(false)
const showCheck = ref(false)

const services = computed(() => setup.data?.services || [])
const onlineServices = computed(() =>
  services.value.filter((s) => s.bookable_online),
)
const pageUrl = computed(
  () => window.location.origin + (setup.data?.link || '/prenota'),
)

function takes(person, service) {
  return Boolean(person.services?.[service.name])
}

function countLabel(n) {
  return n === 1 ? __('1 service') : __('{0} services', [n])
}

const showProfile = ref(false)
const profile = reactive({
  user: '',
  full_name: '',
  public_title: '',
  public_bio: '',
})

function editProfile(person) {
  Object.assign(profile, {
    user: person.user,
    full_name: person.full_name,
    public_title: person.public_title || '',
    public_bio: person.public_bio || '',
  })
  showProfile.value = true
}

async function saveProfile() {
  await run('set_person_profile', {
    user: profile.user,
    public_title: profile.public_title,
    public_bio: profile.public_bio,
  })
  showProfile.value = false
}

function toggle(person, service) {
  run('set_person_service_online', {
    user: person.user,
    service: service.name,
    online: takes(person, service) ? 0 : 1,
  })
}

async function run(method, params) {
  busy.value = true
  try {
    setup.setData(await call(`crm.api.booking_admin.${method}`, params))
  } catch (error) {
    toast.error(error.messages?.[0] || __('Could not save'))
  }
  busy.value = false
}
</script>
