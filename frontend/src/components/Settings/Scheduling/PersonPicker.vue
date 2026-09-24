<template>
  <div class="flex flex-col gap-1.5">
    <label v-if="label" class="text-xs text-ink-gray-5">{{ label }}</label>
    <Autocomplete
      :modelValue="modelValue"
      :options="options"
      :placeholder="placeholder || __('Pick a person')"
      :disabled="disabled"
      @update:modelValue="
        (option) => option?.value && emit('update:modelValue', option.value)
      "
    >
      <template #prefix>
        <UserAvatar :user="modelValue" size="xs" class="mr-2 shrink-0" />
      </template>
      <template #item-prefix="{ option }">
        <UserAvatar :user="option.value" size="sm" class="mr-2 shrink-0" />
      </template>
    </Autocomplete>
  </div>
</template>

<script setup>
// The team picker of the agenda settings: CRM users by name and photo, never a
// bare email address.
import Autocomplete from '@/components/frappe-ui/Autocomplete.vue'
import UserAvatar from '@/components/UserAvatar.vue'
import { usersStore } from '@/stores/users'
import { computed } from 'vue'

const props = defineProps({
  modelValue: { type: String, default: '' },
  label: { type: String, default: '' },
  placeholder: { type: String, default: '' },
  disabled: { type: Boolean, default: false },
  /** people already chosen elsewhere: not offered again */
  exclude: { type: Array, default: () => [] },
})
const emit = defineEmits(['update:modelValue'])

const { users } = usersStore()

const options = computed(() =>
  (users.data?.crmUsers || [])
    .filter(
      (u) =>
        u.name !== 'Administrator' &&
        (u.name === props.modelValue || !props.exclude.includes(u.name)),
    )
    .map((u) => ({ label: u.full_name, value: u.name, description: u.email })),
)
</script>
