<template>
  <Popover v-if="canAssign" placement="bottom-end">
    <template #target="{ togglePopover }">
      <div class="flex items-center" @click="togglePopover">
        <component
          :is="assignees?.length == 1 ? 'Button' : 'div'"
          v-if="assignees?.length"
        >
          <MultipleAvatar :avatars="assignees" />
        </component>
        <Button v-else :label="__('Assign To')" />
      </div>
    </template>
    <template #body="{ isOpen }">
      <AssignToBody
        v-show="isOpen"
        v-model="assignees"
        :docname="docname"
        :doctype="doctype"
        :open="isOpen"
        :onUpdate="ownerField && saveAssignees"
      />
    </template>
  </Popover>
  <!-- who it is with, for whoever may not change it -->
  <MultipleAvatar v-else-if="assignees?.length" :avatars="assignees" />
</template>
<script setup>
import MultipleAvatar from '@/components/MultipleAvatar.vue'
import AssignToBody from '@/components/AssignToBody.vue'
import { useDocument } from '@/data/document'
import { usersStore } from '@/stores/users'
import { toast, Popover } from 'frappe-ui'
import { computed } from 'vue'

const props = defineProps({
  doctype: { type: String, default: '' },
  docname: { type: String, default: '' },
})

const { document, canWrite } = useDocument(props.doctype, props.docname)
const { puo } = usersStore()

// Assigning a person or a deal hands it to somebody (doc 30): the capability,
// on a record the session may change. The server asks the same.
const canAssign = computed(
  () =>
    canWrite.value &&
    (!['CRM Lead', 'CRM Deal'].includes(props.doctype) ||
      puo('persone.assegna')),
)

const assignees = defineModel({ type: Array, default: () => [] })

const ownerField = computed(() => {
  if (props.doctype === 'CRM Lead') {
    return 'lead_owner'
  } else if (props.doctype === 'CRM Deal') {
    return 'deal_owner'
  } else {
    return null
  }
})

async function saveAssignees(
  addedAssignees,
  removedAssignees,
  addAssignees,
  removeAssignees,
) {
  if (removedAssignees.length) await removeAssignees.submit(removedAssignees)
  if (addedAssignees.length) await addAssignees.submit(addedAssignees)

  const nextAssignee = assignees.value.find(
    (a) => a.name !== document.doc[ownerField.value],
  )

  // the field's own label, in the user's language: «responsabile della persona»
  let owner = __(
    ownerField.value === 'deal_owner' ? 'Deal Owner' : 'Lead Owner',
  ).toLowerCase()

  if (
    document.doc[ownerField.value] &&
    removedAssignees.includes(document.doc[ownerField.value])
  ) {
    document.doc[ownerField.value] = nextAssignee ? nextAssignee.name : ''
    document.save.submit()

    if (nextAssignee) {
      toast.info(
        __(
          'Since you removed {0} from the assignee, the {0} has been changed to the next available assignee {1}.',
          [owner, nextAssignee.label || nextAssignee.name],
        ),
      )
    } else {
      toast.info(
        __(
          'Since you removed {0} from the assignee, the {0} has also been removed.',
          [owner],
        ),
      )
    }
  } else if (!document.doc[ownerField.value] && nextAssignee) {
    document.doc[ownerField.value] = nextAssignee ? nextAssignee.name : ''
    toast.info(
      __('Since you added a new assignee, the {0} has been set to {1}.', [
        owner,
        nextAssignee.label || nextAssignee.name,
      ]),
    )
  }
}
</script>
