<!--
  What the centre gave online: until when, and a download after a code verified
  in the last minutes.
-->
<template>
  <div class="flex flex-col gap-4">
    <h1 class="text-xl font-semibold text-ink-gray-9">
      {{ __('Your documents') }}
    </h1>
    <p class="text-p-sm text-ink-gray-6">
      {{ __('Documents the centre gave you, online until the date shown.') }}
    </p>
    <template v-for="doc in documents.data?.documents || []" :key="doc.name">
      <HiddenCard
        v-if="doc.hidden"
        :when="__('Online until {0}', [day(doc.expires_on)])"
      />
      <div
        v-else
        class="flex items-center justify-between gap-3 rounded-lg bg-surface-elevation-1 p-4 shadow-sm"
      >
        <div class="flex min-w-0 flex-col">
          <span class="text-base text-ink-gray-9">{{ doc.title }}</span>
          <span class="text-p-sm text-ink-gray-5">
            {{ __(doc.document_type) }} ·
            {{ __('Online until {0}', [day(doc.expires_on)]) }}
          </span>
        </div>
        <!-- the centre's preview downloads nothing -->
        <Button
          v-if="!anteprima"
          class="shrink-0"
          :variant="doc.downloaded ? 'subtle' : 'solid'"
          :label="__('Download')"
          @click="download(doc)"
        />
      </div>
    </template>
    <p
      v-if="documents.data && !documents.data.documents.length"
      class="text-p-base text-ink-gray-5"
    >
      {{ __('Nothing here yet.') }}
    </p>
    <CodeDialog v-model="asking" @verified="afterCode" />
  </div>
</template>

<script setup>
import { Button, createResource } from 'frappe-ui'
import { ref } from 'vue'
import { anteprima } from '../anteprima'
import CodeDialog from '../components/CodeDialog.vue'
import HiddenCard from '../components/HiddenCard.vue'
import { day } from '../dates'
import { area } from '../store'

const documents = createResource({
  url: 'crm.documenti.area.get_documents',
  params: { person: area.person },
  auto: true,
})

const asking = ref(false)
const waiting = ref(null)

function download(doc) {
  if (!documents.data?.verified) {
    waiting.value = doc
    asking.value = true
    return
  }
  go(doc)
}

function afterCode() {
  documents.data.verified = true
  if (waiting.value) go(waiting.value)
  waiting.value = null
}

function go(doc) {
  const params = new URLSearchParams({
    person: area.person,
    delivery: doc.name,
  })
  window.location.href = `/api/method/crm.documenti.area.download_document?${params}`
  doc.downloaded = true
}
</script>
