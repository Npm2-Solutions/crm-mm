<template>
  <Dialog
    v-model:open="show"
    :title="__('Access for {0}', [user.full_name || user.name])"
    @close="show = false"
  >
    <template #default>
      <div class="flex flex-col gap-5">
        <div
          v-if="user.levels_implied"
          class="flex gap-2 rounded-lg bg-surface-gray-2 p-3 text-p-sm text-ink-gray-7"
        >
          <span
            class="lucide-info mt-0.5 size-3.5 shrink-0"
            aria-hidden="true"
          />
          <p>
            {{
              __(
                'No level yet: what {0} can do comes from roles given before levels existed. Choose their levels to replace them.',
                [user.first_name || user.full_name || user.name],
              )
            }}
          </p>
        </div>

        <LevelPicker v-model="selected" :levels="levels.data || []" />

        <div v-if="optional.length" class="flex flex-col gap-1">
          <div class="px-2 text-p-sm text-ink-gray-5">
            {{ __('Also allow') }}
          </div>
          <label
            v-for="capability in optional"
            :key="capability.name"
            class="flex cursor-pointer items-center gap-2.5 rounded-lg px-2 py-2 hover:bg-surface-gray-2"
          >
            <Checkbox
              class="shrink-0"
              :modelValue="allowed.includes(capability.name)"
              @update:modelValue="toggleAllowed(capability.name)"
            />
            <span class="text-base text-ink-gray-8">
              {{ __(capability.description || capability.name) }}
            </span>
          </label>
        </div>

        <ErrorMessage :message="error" />
      </div>
    </template>
    <template #actions>
      <div class="flex justify-end gap-2">
        <Button :label="__('Cancel')" @click="show = false" />
        <Button
          variant="solid"
          :label="__('Save')"
          :disabled="!selected.length || !changed"
          :loading="saving"
          @click="save"
        />
      </div>
    </template>
  </Dialog>
</template>

<script setup>
// One person's levels, and the optional capabilities those levels offer - off
// by default, the Manager turns them on for this person (doc 30, "a scelta").
import LevelPicker from '@/components/Settings/LevelPicker.vue'
import { useLevels } from '@/composables/levels'
import { usersStore } from '@/stores/users'
import { Checkbox, ErrorMessage, call, toast } from 'frappe-ui'
import { computed, ref } from 'vue'

const props = defineProps({
  user: { type: Object, required: true },
})

const show = defineModel({ type: Boolean })

const { users, permissions } = usersStore()
const levels = useLevels()

const selected = ref([...(props.user.levels || [])])
const allowed = ref([...(props.user.optional || [])])
const saving = ref(false)
const error = ref('')

// what the chosen levels offer, each once
const optional = computed(() => {
  const seen = new Map()
  for (const level of levels.data || []) {
    if (!selected.value.includes(level.key)) continue
    for (const capability of level.optional || []) {
      seen.set(capability.name, capability)
    }
  }
  return [...seen.values()]
})

const changed = computed(
  () =>
    props.user.levels_implied ||
    selected.value.join() !== (props.user.levels || []).join() ||
    allowedNow().join() !== [...(props.user.optional || [])].sort().join(),
)

function allowedNow() {
  const offered = optional.value.map((c) => c.name)
  return allowed.value.filter((name) => offered.includes(name)).sort()
}

function toggleAllowed(name) {
  allowed.value = allowed.value.includes(name)
    ? allowed.value.filter((n) => n !== name)
    : [...allowed.value, name]
}

async function save() {
  saving.value = true
  error.value = ''
  try {
    await call('crm.api.user.set_user_levels', {
      user: props.user.name,
      levels: JSON.stringify(selected.value),
    })
    // after the levels: the server checks each against them
    const before = props.user.optional || []
    const after = allowedNow()
    for (const name of optional.value.map((c) => c.name)) {
      const on = after.includes(name)
      if (on !== before.includes(name)) {
        await call('crm.api.user.set_user_capability', {
          user: props.user.name,
          capability: name,
          enabled: on ? 1 : 0,
        })
      }
    }
    toast.success(__('Access updated for {0}', [props.user.full_name]))
    users.reload()
    if (props.user.session_user) permissions.reload()
    show.value = false
  } catch (e) {
    error.value = e?.messages?.[0] || __('Something went wrong')
    users.reload()
  } finally {
    saving.value = false
  }
}
</script>
