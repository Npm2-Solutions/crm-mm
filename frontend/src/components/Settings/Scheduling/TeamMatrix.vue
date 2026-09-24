<template>
  <!-- the body of the Services page: services by people, one grid -->
  <div class="isolate flex min-h-0 flex-1 flex-col gap-4 text-ink-gray-8">
    <div class="flex-1 overflow-auto px-2">
      <table
        v-if="matrix.data?.services?.length"
        class="w-max border-separate border-spacing-0 text-p-sm"
      >
        <thead class="sticky top-0 z-10 bg-surface-white">
          <tr>
            <th
              class="sticky left-0 z-20 w-[300px] min-w-[300px] border-b border-outline-gray-2 bg-surface-white px-3 py-2 text-left align-bottom text-p-xs font-medium text-ink-gray-5"
            >
              {{ __('Service') }}
            </th>
            <th
              v-for="person in matrix.data.staff"
              :key="person.user"
              class="min-w-[104px] border-b border-outline-gray-2 px-1 py-2 text-center align-top"
            >
              <Dropdown :options="columnActions(person)">
                <button
                  class="mx-auto flex min-h-[72px] w-full max-w-[110px] flex-col items-center justify-start gap-1 rounded px-1 py-1.5 hover:bg-surface-gray-2"
                  :title="__('Actions for {0}', [person.full_name])"
                >
                  <UserAvatar :user="person.user" size="sm" />
                  <span
                    class="w-full truncate text-p-xs font-medium text-ink-gray-7"
                    >{{ person.full_name }}</span
                  >
                  <span
                    v-if="!person.online"
                    class="rounded bg-surface-gray-2 px-1 text-p-xs text-ink-gray-5"
                    >{{ __('not online') }}</span
                  >
                </button>
              </Dropdown>
            </th>
          </tr>
        </thead>
        <tbody>
          <template v-for="group in groups" :key="group.category">
            <tr v-if="groups.length > 1">
              <td
                :colspan="matrix.data.staff.length + 1"
                class="sticky left-0 bg-surface-gray-1 px-3 py-1.5 text-p-xs font-medium uppercase text-ink-gray-5"
              >
                {{ group.category || __('No category') }}
              </td>
            </tr>
            <tr
              v-for="service in group.services"
              :key="service.name"
              class="hover:bg-surface-gray-1"
            >
              <td
                class="sticky left-0 border-b border-outline-gray-1 bg-surface-white px-3 py-2"
              >
                <div class="flex items-center gap-2">
                  <span
                    class="size-2.5 shrink-0 rounded-full"
                    :style="{ backgroundColor: service.color || '#4C7EFF' }"
                  />
                  <button
                    class="min-w-0 truncate text-left text-p-base-medium text-ink-gray-8 hover:underline"
                    :class="service.enabled ? '' : 'line-through opacity-60'"
                    @click="emit('edit', service)"
                  >
                    {{ service.service_name }}
                  </button>
                  <Badge
                    v-if="service.bookable_online"
                    :label="__('Online')"
                    theme="blue"
                    size="sm"
                  />
                  <Badge
                    v-if="!service.enabled"
                    :label="__('Off')"
                    theme="gray"
                    size="sm"
                  />
                  <span class="grow" />
                  <Dropdown :options="rowActions(service)">
                    <Button
                      variant="ghost"
                      size="sm"
                      icon="lucide-ellipsis"
                      :disabled="busy"
                    />
                  </Dropdown>
                </div>
                <div class="truncate pl-4.5 text-p-xs text-ink-gray-5">
                  {{ describe(service) }}
                </div>
                <div
                  v-for="warning in service.warnings"
                  :key="warning"
                  class="mt-0.5 pl-4.5 text-p-xs text-ink-amber-8"
                >
                  {{ warning }}
                </div>
              </td>
              <td
                v-for="person in matrix.data.staff"
                :key="person.user"
                class="border-b border-outline-gray-1 p-1 text-center"
              >
                <button
                  class="group mx-auto flex h-8 w-full max-w-[96px] items-center justify-center gap-1 rounded border text-p-xs"
                  :class="cellClass(service, person.user)"
                  :title="cellTitle(service, person.user)"
                  :disabled="busy"
                  @click="clickCell(service, person)"
                >
                  <span
                    v-if="!cell(service, person.user)"
                    class="lucide-plus size-3.5 opacity-0 group-hover:opacity-100"
                  />
                  <template v-else>
                    <span class="lucide-check size-3.5" />
                    <span v-if="overrideText(service, person.user)">{{
                      overrideText(service, person.user)
                    }}</span>
                    <span
                      v-if="!cell(service, person.user).bookable_online"
                      class="lucide-globe-lock size-3.5"
                    />
                  </template>
                </button>
              </td>
            </tr>
          </template>
        </tbody>
      </table>
      <div
        v-if="matrix.data?.services?.length"
        class="flex flex-wrap items-center gap-4 px-3 pt-3 text-p-xs text-ink-gray-6"
      >
        <span class="flex items-center gap-1.5">
          <span
            class="size-3 rounded-sm border border-outline-green-3 bg-surface-green-2"
          />
          {{ __('Delivers it') }}
        </span>
        <span class="flex items-center gap-1.5">
          <span
            class="size-3 rounded-sm border border-outline-blue-3 bg-surface-blue-2"
          />
          {{ __('Own length or price, or not online') }}
        </span>
        <span class="flex items-center gap-1.5">
          <span
            class="size-3 rounded-sm border border-dashed border-outline-gray-3"
          />
          {{ __('Click to assign') }}
        </span>
      </div>
      <div v-else-if="!matrix.loading" class="px-2 text-p-base text-ink-gray-5">
        {{ __('No services yet. Create the first one!') }}
      </div>
    </div>
  </div>

  <Dialog v-model="showCell" :options="{ title: cellDialogTitle, size: 'lg' }">
    <template #body-content>
      <div class="flex flex-col gap-4">
        <p class="text-p-sm text-ink-gray-6">
          {{
            __('Leave empty to use the service values ({0} min, {1}).', [
              editing.service?.duration,
              formatPrice(editing.service),
            ])
          }}
        </p>
        <div class="grid grid-cols-2 gap-3">
          <FormControl
            v-model.number="editing.values.duration"
            type="number"
            min="0"
            :label="__('Own length (min)')"
            :placeholder="String(editing.service?.duration || '')"
          />
          <FormControl
            v-model.number="editing.values.priority"
            type="number"
            :label="__('Priority')"
            :description="__('Lower is picked first')"
          />
        </div>
        <div class="grid grid-cols-2 items-end gap-3">
          <label class="flex h-7 items-center gap-2 text-sm text-ink-gray-7">
            <Switch v-model="editing.values.custom_price" size="sm" />
            {{ __('Own price') }}
          </label>
          <FormControl
            v-model.number="editing.values.price"
            type="number"
            min="0"
            :disabled="!editing.values.custom_price"
            :label="__('Price')"
          />
        </div>
        <FormControl
          v-model="editing.values.role"
          type="text"
          :label="__('Role (for one-per-role services)')"
        />
        <label class="flex items-center gap-2 text-sm text-ink-gray-7">
          <Switch v-model="editing.values.bookable_online" size="sm" />
          {{ __('Clients can book them for this online') }}
        </label>
      </div>
    </template>
    <template #actions>
      <div class="flex gap-2">
        <Button
          theme="red"
          variant="subtle"
          :label="__('Remove')"
          :loading="busy"
          @click="saveCell(false)"
        />
        <Button
          class="flex-1"
          variant="solid"
          :label="__('Save')"
          :loading="busy"
          @click="saveCell(true)"
        />
      </div>
    </template>
  </Dialog>
</template>

<script setup>
import UserAvatar from '@/components/UserAvatar.vue'
import {
  createResource,
  Dialog,
  Dropdown,
  FormControl,
  Switch,
  call,
  toast,
} from 'frappe-ui'
import { computed, reactive, ref } from 'vue'

const props = defineProps({
  query: { type: String, default: '' },
})
const emit = defineEmits(['edit', 'remove'])

const matrix = createResource({
  url: 'crm.api.booking_admin.get_matrix',
  auto: true,
})

const busy = ref(false)

const groups = computed(() => {
  const q = props.query.trim().toLowerCase()
  const out = []
  for (const service of matrix.data?.services || []) {
    if (q && !service.service_name.toLowerCase().includes(q)) continue
    let group = out.find((g) => g.category === (service.category || ''))
    if (!group) {
      group = { category: service.category || '', services: [] }
      out.push(group)
    }
    group.services.push(service)
  }
  return out
})

function cell(service, user) {
  return service.cells?.[user]
}

function overrideText(service, user) {
  const c = cell(service, user)
  if (!c) return ''
  const parts = []
  if (c.duration) parts.push(`${c.duration}'`)
  if (c.custom_price) parts.push(formatMoney(c.price, service.currency))
  return parts.join(' · ')
}

function cellClass(service, user) {
  const c = cell(service, user)
  if (!c) {
    return 'border-dashed border-outline-gray-3 text-ink-gray-5 hover:border-outline-gray-4 hover:bg-surface-gray-2'
  }
  if (overrideText(service, user) || !c.bookable_online) {
    return 'border-outline-blue-3 bg-surface-blue-2 text-ink-blue-8'
  }
  return 'border-outline-green-3 bg-surface-green-2 text-ink-green-8'
}

function cellTitle(service, user) {
  const c = cell(service, user)
  if (!c) return __('Click to assign')
  const parts = [__('Delivers it')]
  if (c.duration) parts.push(__('{0} min', [c.duration]))
  if (c.custom_price) parts.push(formatMoney(c.price, service.currency))
  if (!c.bookable_online) parts.push(__('not bookable online'))
  return parts.join(' · ')
}

function formatMoney(value, currency) {
  try {
    return new Intl.NumberFormat(undefined, {
      style: 'currency',
      currency: currency || 'EUR',
      maximumFractionDigits: 0,
    }).format(value || 0)
  } catch {
    return String(value)
  }
}

function formatPrice(service) {
  return service ? formatMoney(service.default_price, service.currency) : ''
}

function rowFull(service) {
  const staff = matrix.data?.staff || []
  return staff.length > 0 && staff.every((p) => cell(service, p.user))
}

async function run(method, params) {
  busy.value = true
  try {
    const data = await call(`crm.api.booking_admin.${method}`, params)
    matrix.setData(data)
    for (const error of data?.errors || []) toast.error(error)
  } catch (error) {
    toast.error(error.messages?.[0] || __('Could not save'))
  }
  busy.value = false
}

function describe(service) {
  const parts = [`${service.duration} ${__('min')}`]
  parts.push(
    {
      'Any one': __('round robin'),
      'All required': __('collective'),
      'One per role': __('one per role'),
    }[service.staff_selection] || service.staff_selection,
  )
  if (service.max_participants > 1) {
    parts.push(__('up to {0} people', [service.max_participants]))
  }
  if (service.default_price) {
    parts.push(formatMoney(service.default_price, service.currency))
  }
  if (service.upcoming_count) {
    parts.push(__('{0} upcoming', [service.upcoming_count]))
  }
  return parts.join(' · ')
}

function rowActions(service) {
  const actions = [
    {
      label: __('Edit service'),
      icon: 'edit',
      onClick: () => emit('edit', service),
    },
    {
      label: __('Remove everyone'),
      icon: 'square',
      onClick: () => toggleRow(service, false),
    },
    {
      label: __('Delete service'),
      icon: 'trash-2',
      theme: 'red',
      onClick: () => emit('remove', service),
    },
  ]
  if (!rowFull(service)) {
    actions.splice(1, 0, {
      label: __('Everyone delivers it'),
      icon: 'check-square',
      onClick: () => toggleRow(service, true),
    })
  }
  return actions
}

function toggleRow(service, value) {
  run('set_row', {
    service: service.name,
    users: (matrix.data?.staff || []).map((p) => p.user),
    enabled: value ? 1 : 0,
  })
}

function columnActions(person) {
  const services = (matrix.data?.services || []).map((s) => s.name)
  const others = (matrix.data?.staff || []).filter(
    (p) => p.user !== person.user,
  )
  return [
    {
      label: __('Assign every service'),
      icon: 'check-square',
      onClick: () =>
        run('set_column', { user: person.user, services, enabled: 1 }),
    },
    {
      label: __('Remove every service'),
      icon: 'square',
      onClick: () =>
        run('set_column', { user: person.user, services, enabled: 0 }),
    },
    ...(others.length
      ? [
          {
            group: __('Copy the services of…'),
            items: others.map((other) => ({
              label: other.full_name,
              onClick: () =>
                run('copy_column', { source: other.user, target: person.user }),
            })),
          },
        ]
      : []),
  ]
}

const showCell = ref(false)
const editing = reactive({ service: null, person: null, values: {} })
const cellDialogTitle = computed(() =>
  editing.service && editing.person
    ? `${editing.service.service_name} · ${editing.person.full_name}`
    : '',
)

function clickCell(service, person) {
  const c = cell(service, person.user)
  if (!c) {
    run('set_cell', { service: service.name, user: person.user, enabled: 1 })
    return
  }
  editing.service = service
  editing.person = person
  editing.values = {
    duration: c.duration || null,
    priority: c.priority || 0,
    custom_price: Boolean(c.custom_price),
    price: c.price || 0,
    role: c.role || '',
    bookable_online: Boolean(c.bookable_online),
  }
  showCell.value = true
}

async function saveCell(keep) {
  await run('set_cell', {
    service: editing.service.name,
    user: editing.person.user,
    enabled: keep ? 1 : 0,
    values: {
      ...editing.values,
      duration: Number(editing.values.duration) || 0,
      custom_price: editing.values.custom_price ? 1 : 0,
      bookable_online: editing.values.bookable_online ? 1 : 0,
    },
  })
  showCell.value = false
}

defineExpose({ reload: () => matrix.reload() })
</script>
