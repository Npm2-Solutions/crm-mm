<template>
  <!-- The people this person belongs with: a parent, a child, a partner, a
       guardian. Who pays, books or acts for whom is said in words, from this
       page's side: the same link reads the other way on the other's page. -->
  <div v-if="related.data" class="flex flex-col">
    <div class="h-px w-full border-t" />
    <div class="p-1 sm:p-3">
      <CollapsibleSection
        labelClass="px-2 font-semibold"
        headerClass="h-8"
        :label="__('Linked people')"
        :count="related.data.people.length || ''"
      >
        <template #actions>
          <Button
            v-if="related.data.can_edit"
            variant="ghost"
            class="touch-target"
            icon="plus"
            :aria-label="__('Link someone')"
            :title="__('Link someone')"
            @click="openNew"
          />
        </template>
        <div class="flex flex-col gap-0.5 pb-1 pt-2">
          <div
            v-if="related.data.reached_through.length"
            class="mx-3 mb-1 flex items-start gap-1.5 rounded bg-surface-gray-2 px-2 py-1.5 text-p-sm text-ink-gray-7"
          >
            <span
              class="lucide-message-circle mt-0.5 size-3.5 shrink-0"
              aria-hidden="true"
            />
            <span class="min-w-0">
              {{
                __(
                  'No contact details of their own: messages reach them through {0}',
                  [related.data.reached_through.join(', ')],
                )
              }}
            </span>
          </div>
          <div
            v-for="person in related.data.people"
            :key="person.name"
            class="flex items-start gap-2 rounded px-3 py-1.5"
          >
            <Avatar
              class="mt-0.5 shrink-0"
              size="sm"
              :image="person.image"
              :label="person.other_name"
            />
            <div class="flex min-w-0 flex-1 flex-col">
              <router-link
                v-if="person.can_open"
                class="truncate text-base text-ink-gray-8 hover:underline"
                :to="{ name: 'Lead', params: { leadId: person.other } }"
              >
                {{ person.other_name }}
              </router-link>
              <span v-else class="truncate text-base text-ink-gray-8">
                {{ person.other_name }}
              </span>
              <span class="text-p-sm text-ink-gray-5">
                {{ relationLabel(person.relation) }}
              </span>
              <span
                v-if="actsLine(person)"
                class="text-p-sm text-ink-gray-6 [overflow-wrap:anywhere]"
              >
                {{ actsLine(person) }}
              </span>
            </div>
            <Button
              v-if="related.data.can_edit"
              size="sm"
              variant="ghost"
              class="touch-target shrink-0"
              :label="__('Edit')"
              @click="openEdit(person)"
            />
          </div>
          <div
            v-if="!related.data.people.length"
            class="px-3 py-1 text-p-sm text-ink-gray-5"
          >
            {{ __('Nobody linked yet: a parent, a child, a partner…') }}
          </div>
        </div>
      </CollapsibleSection>
    </div>
  </div>

  <Dialog
    v-model="dialog.show"
    :options="{
      title: dialog.name ? __('Change the link') : __('Link someone'),
      size: 'md',
    }"
  >
    <template #body-content>
      <div class="flex flex-col gap-4">
        <template v-if="!dialog.name">
          <div class="flex flex-wrap gap-2" role="group">
            <Button
              :variant="dialog.newPerson ? 'subtle' : 'solid'"
              :label="__('Someone in the CRM')"
              @click="dialog.newPerson = false"
            />
            <Button
              :variant="dialog.newPerson ? 'solid' : 'subtle'"
              :label="__('Someone new')"
              @click="dialog.newPerson = true"
            />
          </div>
          <div
            v-if="dialog.newPerson"
            class="grid grid-cols-2 gap-3 max-md:grid-cols-1"
          >
            <FormControl
              v-model="dialog.firstName"
              :label="__('First name')"
              :placeholder="__('Luca')"
            />
            <FormControl
              v-model="dialog.lastName"
              :label="__('Last name')"
              :placeholder="__('Rossi')"
            />
          </div>
          <Link
            v-else
            class="w-full"
            doctype="CRM Lead"
            variant="outline"
            :label="__('Person')"
            :filters="{ name: ['!=', lead] }"
            :modelValue="dialog.other"
            :placeholder="__('Search a person')"
            @update:modelValue="(value) => (dialog.other = value)"
          />
        </template>
        <div v-else class="text-base text-ink-gray-8">
          {{ dialog.otherName }}
        </div>
        <FormControl
          v-model="dialog.relation"
          type="select"
          :label="__('Who are they to {0}?', [me])"
          :options="relationOptions"
          @update:modelValue="suggest"
        />
        <FormControl
          v-model="dialog.acts"
          type="select"
          :label="__('Does one of them act for the other?')"
          :options="actsOptions"
        />
        <div v-if="dialog.acts" class="flex flex-col gap-2">
          <FormControl
            v-model="dialog.pays"
            type="checkbox"
            :label="__('Pays: the invoices are made out to them')"
          />
          <FormControl
            v-model="dialog.books"
            type="checkbox"
            :label="__('Books, and gets the messages about the appointments')"
          />
          <FormControl
            v-model="dialog.represents"
            type="checkbox"
            :label="
              __(
                'Signs and decides: a parent of a minor child, a legal guardian',
              )
            "
          />
        </div>
        <FormControl
          v-model="dialog.note"
          type="textarea"
          :label="__('Note')"
          :placeholder="__('Separated: the father books only on weekends')"
        />
        <ErrorMessage :message="dialog.error" />
      </div>
    </template>
    <template #actions>
      <div class="flex flex-wrap items-center justify-between gap-2">
        <Button
          v-if="dialog.name"
          variant="ghost"
          theme="red"
          :label="__('Unlink')"
          :loading="dialog.saving === 'remove'"
          @click="remove"
        />
        <span v-else />
        <Button
          variant="solid"
          :label="__('Save')"
          :loading="dialog.saving === 'save'"
          @click="save"
        />
      </div>
    </template>
  </Dialog>
</template>

<script setup>
import CollapsibleSection from '@/components/CollapsibleSection.vue'
import Link from '@/components/Controls/Link.vue'
import { usersStore } from '@/stores/users'
import {
  Avatar,
  Dialog,
  ErrorMessage,
  FormControl,
  createResource,
  call,
  toast,
} from 'frappe-ui'
import { computed, reactive, watch } from 'vue'

const props = defineProps({
  lead: { type: String, required: true },
})

const { puo } = usersStore()

const related = createResource({
  url: 'crm.persone.collegate.get_related_people',
  makeParams: () => ({ lead: props.lead }),
  onError: () => related.setData(null),
})

watch(
  () => props.lead,
  (lead) => lead && puo('persone.vedi') && related.reload(),
  { immediate: true },
)

const me = computed(() => related.data?.first_name || '')

const RELATIONS = {
  Parent: __('Parent'),
  Child: __('Child'),
  'Legal guardian': __('Legal guardian'),
  Ward: __('Ward'),
  Partner: __('Partner'),
  'Family member': __('Family member'),
  Other: __('Other'),
}

function relationLabel(value) {
  return RELATIONS[value] || value
}

const relationOptions = computed(() =>
  (related.data?.relations || Object.keys(RELATIONS)).map((value) => ({
    label: relationLabel(value),
    value,
  })),
)

const actsOptions = computed(() => [
  { label: __('Nobody acts for the other'), value: '' },
  { label: __('They act for {0}', [me.value]), value: 'them_for_me' },
  { label: __('{0} acts for them', [me.value]), value: 'me_for_them' },
])

// what they do, said from this page's side: "Pays for Luca", "Luca books for them"
function actsLine(person) {
  if (!person.acts) return ''
  const mine = person.acts === 'me_for_them'
  const says = []
  if (person.pays) {
    says.push(
      mine
        ? __('{0} pays for them', [me.value])
        : __('Pays for {0}', [me.value]),
    )
  }
  if (person.books) {
    says.push(
      mine
        ? __('{0} books for them', [me.value])
        : __('Books for {0}', [me.value]),
    )
  }
  if (person.represents) {
    says.push(
      mine
        ? __('{0} acts for them', [me.value])
        : __('Acts for {0}', [me.value]),
    )
  }
  return says.join(' · ')
}

const dialog = reactive({
  show: false,
  name: null,
  newPerson: false,
  other: '',
  otherName: '',
  firstName: '',
  lastName: '',
  relation: 'Parent',
  acts: 'them_for_me',
  pays: true,
  books: true,
  represents: false,
  note: '',
  error: '',
  saving: '',
})

function openNew() {
  Object.assign(dialog, {
    show: true,
    name: null,
    newPerson: false,
    other: '',
    otherName: '',
    firstName: '',
    lastName: '',
    relation: 'Parent',
    acts: 'them_for_me',
    pays: true,
    books: true,
    represents: false,
    note: '',
    error: '',
    saving: '',
  })
}

function openEdit(person) {
  Object.assign(dialog, {
    show: true,
    name: person.name,
    newPerson: false,
    other: person.other,
    otherName: person.other_name,
    firstName: '',
    lastName: '',
    relation: person.relation,
    acts: person.acts,
    pays: !!person.pays,
    books: !!person.books,
    represents: !!person.represents,
    note: person.note || '',
    error: '',
    saving: '',
  })
}

// a parent or a guardian usually acts for the one they look after; who is
// looked after by this person acts for nobody here. Only a suggestion.
function suggest(relation) {
  if (dialog.name) return
  const theyLookAfter = ['Parent', 'Legal guardian'].includes(relation)
  const iLookAfter = ['Child', 'Ward'].includes(relation)
  dialog.acts = theyLookAfter ? 'them_for_me' : iLookAfter ? 'me_for_them' : ''
  dialog.represents = ['Legal guardian', 'Ward'].includes(relation)
}

async function save() {
  dialog.saving = 'save'
  dialog.error = ''
  try {
    const data = await call('crm.persone.collegate.save_related_person', {
      lead: props.lead,
      name: dialog.name,
      other: dialog.newPerson ? null : dialog.other || null,
      first_name: dialog.newPerson ? dialog.firstName : null,
      last_name: dialog.newPerson ? dialog.lastName : null,
      relation: dialog.relation,
      acts: dialog.acts,
      pays: dialog.pays ? 1 : 0,
      books: dialog.books ? 1 : 0,
      represents: dialog.represents ? 1 : 0,
      note: dialog.note || null,
    })
    related.setData(data)
    dialog.show = false
    toast.success(__('Linked'))
  } catch (err) {
    dialog.error = err.messages?.[0] || err.message
  } finally {
    dialog.saving = ''
  }
}

async function remove() {
  dialog.saving = 'remove'
  dialog.error = ''
  try {
    const data = await call('crm.persone.collegate.remove_related_person', {
      lead: props.lead,
      name: dialog.name,
    })
    related.setData(data)
    dialog.show = false
    toast.success(__('Unlinked'))
  } catch (err) {
    dialog.error = err.messages?.[0] || err.message
  } finally {
    dialog.saving = ''
  }
}
</script>
