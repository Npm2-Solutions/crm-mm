<!--
  Copyright (c) 2026, NPM2 Solutions Srl and contributors
  For license information, please see license.txt

  The deals on a phone (docs/progetto-ghl/29): a board of columns does not fit a
  hand, so the stages are a row of chips with how many deals each holds, and the
  deals of the stage chosen are cards one under the other - who, what they are
  worth when there is a value, who follows them, when they last moved. It opens
  on the first open stage with deals; a pipeline is chosen above when there are
  more.
-->
<template>
  <div class="flex min-h-0 flex-1 flex-col">
    <div class="shrink-0 px-3 pt-1">
      <FormControl
        v-if="pipelineAttive.length > 1"
        v-model="pipeline"
        type="select"
        class="mb-2"
        :options="pipelineAttive"
        :aria-label="__('Pipeline')"
      />
      <div
        class="-mx-3 flex gap-2 overflow-x-auto px-3 pb-2"
        role="tablist"
        :aria-label="__('Stages')"
      >
        <button
          v-for="fase in fasi"
          :key="fase.name"
          type="button"
          role="tab"
          :aria-selected="fase.name === scelta"
          class="flex shrink-0 items-center gap-1.5 rounded-full border px-3 py-1.5 text-sm"
          :class="
            fase.name === scelta
              ? 'border-outline-gray-4 bg-surface-gray-3 text-ink-gray-9'
              : 'border-outline-gray-2 text-ink-gray-6'
          "
          @click="scegli(fase.name)"
        >
          <IndicatorIcon :class="parseColor(fase.color)" />
          {{ __(fase.name) }}
          <span class="text-ink-gray-5">{{ conteggi[fase.name] || 0 }}</span>
        </button>
      </div>
    </div>

    <div
      ref="contenitore"
      class="min-h-0 flex-1 overflow-y-auto px-3 pb-20"
      @scroll.passive="forseAltre"
    >
      <!-- pulled down from the top, the counts and the stage reload -->
      <TiraPerAggiornare v-bind="tira" />
      <router-link
        v-for="trattativa in righe"
        :key="trattativa.name"
        :to="{ name: 'Deal', params: { dealId: trattativa.name } }"
        class="mb-2 flex flex-col gap-1 rounded-lg border border-outline-gray-2 px-3 py-2.5 active:bg-surface-gray-2"
      >
        <span class="flex items-center justify-between gap-3">
          <span class="truncate text-base-medium text-ink-gray-9">
            {{
              trattativa.lead_name || trattativa.organization || trattativa.name
            }}
          </span>
          <span
            v-if="valoreDellaTrattativa(trattativa, lingua)"
            class="shrink-0 text-base-medium text-ink-gray-8"
          >
            {{ valoreDellaTrattativa(trattativa, lingua) }}
          </span>
        </span>
        <span class="flex items-center gap-2 text-p-sm text-ink-gray-5">
          <Avatar
            v-if="trattativa.deal_owner"
            :image="getUser(trattativa.deal_owner)?.user_image"
            :label="getUser(trattativa.deal_owner)?.full_name"
            size="xs"
          />
          <span class="truncate">{{ secondaRiga(trattativa) }}</span>
          <span class="ml-auto shrink-0">{{
            __(timeAgo(trattativa.modified))
          }}</span>
        </span>
      </router-link>

      <div v-if="carica.loading" class="flex justify-center py-6">
        <LoadingIndicator class="size-5" />
      </div>
      <EmptyState
        v-else-if="!righe.length && carica.fetched"
        :title="__('No deals in this stage')"
        :text="
          puo('trattative.scrivi')
            ? __(
                'A deal moves here from its page, or starts here with the + button.',
              )
            : ''
        "
      />
    </div>
  </div>
</template>

<script setup>
import TiraPerAggiornare from '@/components/Mobile/TiraPerAggiornare.vue'
import { useTiraPerAggiornare } from '@/composables/tiraPerAggiornare'
import EmptyState from '@/components/Espresso/EmptyState.vue'
import IndicatorIcon from '@/components/Icons/IndicatorIcon.vue'
import { pipelinesStore } from '@/stores/pipelines'
import { usersStore } from '@/stores/users'
import { parseColor, timeAgo } from '@/utils'
import { faseIniziale, valoreDellaTrattativa } from '@/utils/sulTelefono'
import {
  Avatar,
  FormControl,
  LoadingIndicator,
  createResource,
} from 'frappe-ui'
import { storeToRefs } from 'pinia'
import { computed, ref, watch } from 'vue'

const pipelineStore = pipelinesStore()
const { pipelines, getStages } = pipelineStore
// a computed read off the store stays a ref only through storeToRefs
const { defaultPipeline } = storeToRefs(pipelineStore)
const { getUser, puo } = usersStore()
const lingua = window.navigator?.language || 'it-IT'

const pipeline = ref('')
const scelta = ref('')
const righe = ref([])
const altre = ref(false)
const contenitore = ref(null)

const pipelineAttive = computed(() =>
  (pipelines.data || [])
    .filter((p) => !p.disabled)
    .map((p) => ({ label: __(p.name), value: p.name })),
)
const fasi = computed(() => getStages(pipeline.value))

const conteggiResource = createResource({
  url: 'crm.api.sul_telefono.get_deal_stages',
  onSuccess: () => {
    // the stage it was on, else the first open one with deals
    scegli(faseIniziale(fasi.value, conteggi.value, scelta.value))
  },
})
const conteggi = computed(() =>
  Object.fromEntries(
    (conteggiResource.data || []).map((r) => [r.status, r.deals]),
  ),
)

const carica = createResource({
  url: 'crm.api.sul_telefono.get_deals',
  onSuccess(dati) {
    righe.value = dati.start ? [...righe.value, ...dati.rows] : dati.rows
    altre.value = dati.more
  },
})

// the company when the title is the person, else who follows the deal; never
// the viewer standing in for nobody (getUser() without a name is the session's)
function secondaRiga(trattativa) {
  if (trattativa.organization && trattativa.lead_name)
    return trattativa.organization
  if (!trattativa.deal_owner) return ''
  return getUser(trattativa.deal_owner)?.full_name || trattativa.deal_owner
}

const tira = useTiraPerAggiornare(contenitore, () =>
  conteggiResource.submit({ pipeline: pipeline.value }),
)

function scegli(fase) {
  scelta.value = fase
  righe.value = []
  if (fase) carica.submit({ status: fase, pipeline: pipeline.value, start: 0 })
}

function forseAltre() {
  const el = contenitore.value
  if (!el || !altre.value || carica.loading) return
  if (el.scrollTop + el.clientHeight < el.scrollHeight - 300) return
  carica.submit({
    status: scelta.value,
    pipeline: pipeline.value,
    start: righe.value.length,
  })
}

watch(pipeline, (nome) => {
  scelta.value = ''
  conteggiResource.submit({ pipeline: nome })
})
// the default pipeline to start with, once the pipelines are there. They are
// there already when another page asked for them first, and the pipeline is
// set while the page is made: the watch above has to be listening by then, or
// the stages stay at 0 and no deal is asked for
watch(
  () => defaultPipeline.value?.name,
  (nome) => {
    if (!pipeline.value && nome) pipeline.value = nome
  },
  { immediate: true },
)

defineExpose({
  ricarica: () => conteggiResource.submit({ pipeline: pipeline.value }),
  // where a deal started now would go: a closed stage is no place to start
  dove: () => {
    const fase = fasi.value.find((f) => f.name === scelta.value)
    const aperta = fase && !['Won', 'Lost'].includes(fase.type)
    return { pipeline: pipeline.value, fase: aperta ? fase.name : '' }
  },
})
</script>
