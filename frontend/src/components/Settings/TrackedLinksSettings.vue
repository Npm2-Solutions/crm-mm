<!--
  Copyright (c) 2026, NPM2 Solutions Srl and contributors
  For license information, please see license.txt

  Short links that count who opens them and can start an automation.
-->
<template>
  <div
    class="flex h-full flex-col gap-6 py-8 px-6 text-ink-gray-8 max-md:px-3 max-md:py-5"
  >
    <div
      class="flex items-start justify-between gap-4 px-2 max-md:flex-col max-md:items-start max-md:gap-3"
    >
      <div class="flex flex-col gap-1">
        <h2
          class="flex gap-2 text-2xl-semibold leading-tight md:h-5 md:leading-none"
        >
          {{ __('Tracked Links') }}
        </h2>
        <p class="text-p-base text-ink-gray-6">{{ subtitle }}</p>
      </div>
      <Button
        variant="solid"
        :label="__('New link')"
        iconLeft="plus"
        @click="openEditor()"
      />
    </div>

    <div class="flex-1 overflow-y-auto px-2">
      <div
        v-if="links.data?.length"
        class="divide-y divide-outline-elevation-2 rounded-lg border border-outline-gray-2"
      >
        <div
          v-for="link in links.data"
          :key="link.name"
          class="flex cursor-pointer items-center gap-3 px-3 py-2.5 hover:bg-surface-gray-1"
          @click="openEditor(link)"
        >
          <Badge :label="link.slug" theme="blue" size="sm" />
          <span class="min-w-0 flex-1 truncate text-p-base text-ink-gray-6">
            {{ link.target_url }}
          </span>
          <span class="shrink-0 text-p-sm text-ink-gray-5">
            {{ __('{0} clicks', [link.click_count || 0]) }}
          </span>
          <Button
            :aria-label="__('Delete')"
            variant="ghost"
            icon="lucide-trash-2"
            @click.stop="removeLink(link)"
          />
        </div>
      </div>
      <EmptyState
        v-else-if="!links.loading"
        :title="__('No tracked links yet')"
        :text="
          __(
            'A short link that counts who opens it and can start an automation: put one in a message instead of the address.',
          )
        "
      />
    </div>
  </div>

  <Dialog
    v-model="showEditor"
    :options="{
      title: form.name ? __('Edit link') : __('New link'),
      size: 'lg',
    }"
  >
    <template #body-content>
      <div class="flex flex-col gap-3">
        <FormControl
          v-model="form.slug"
          type="text"
          :label="__('Short name')"
          :placeholder="'promo-estate'"
          :description="
            __(
              'Lowercase letters, digits and dashes: it is how an automation finds the link.',
            ) +
            ' ' +
            __('It cannot be changed later.')
          "
          :disabled="Boolean(form.name)"
        />
        <FormControl
          v-model="form.target_url"
          type="url"
          :label="__('Target URL')"
          :placeholder="'https://…'"
        />
        <FormControl
          v-model="form.description"
          type="text"
          :label="__('Description')"
        />
      </div>
    </template>
    <template #actions>
      <Button
        class="w-full"
        variant="solid"
        :label="__('Save')"
        @click="saveLink"
      />
    </template>
  </Dialog>
</template>

<script setup>
import EmptyState from '@/components/Espresso/EmptyState.vue'
import {
  createListResource,
  createResource,
  Dialog,
  FormControl,
  toast,
} from 'frappe-ui'
import { ref, reactive } from 'vue'

const subtitle =
  __('Short links that log clicks on leads and fire automations.') +
  ' ' +
  __(
    'In an automation’s message «Insert field» puts one in: each person receives their own.',
  )

const links = createListResource({
  doctype: 'CRM Tracked Link',
  fields: ['name', 'slug', 'target_url', 'click_count', 'description'],
  orderBy: 'modified desc',
  pageLength: 100,
  auto: true,
})

const showEditor = ref(false)
const form = reactive({ name: null, slug: '', target_url: '', description: '' })

function openEditor(link = null) {
  form.name = link?.name || null
  form.slug = link?.slug || ''
  form.target_url = link?.target_url || ''
  form.description = link?.description || ''
  showEditor.value = true
}

function saveLink() {
  if (form.name) {
    createResource({
      url: 'frappe.client.set_value',
      params: {
        doctype: 'CRM Tracked Link',
        name: form.name,
        fieldname: {
          target_url: form.target_url,
          description: form.description,
        },
      },
      auto: true,
      onSuccess: () => {
        showEditor.value = false
        links.reload()
      },
      onError: (e) => toast.error(e.messages?.[0] || __('Failed to save')),
    })
  } else {
    links.insert.submit(
      {
        slug: form.slug,
        target_url: form.target_url,
        description: form.description,
      },
      {
        onSuccess: () => {
          showEditor.value = false
          links.reload()
        },
        onError: (e) => toast.error(e.messages?.[0] || __('Failed to save')),
      },
    )
  }
}

function removeLink(link) {
  links.delete.submit(link.name, {
    onSuccess: () => links.reload(),
    onError: (e) => toast.error(e.messages?.[0] || __('Failed to delete')),
  })
}
</script>
