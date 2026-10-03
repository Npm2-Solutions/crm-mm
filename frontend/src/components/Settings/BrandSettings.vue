<!--
  Modifications copyright (c) 2026, NPM2 Solutions Srl

  Settings > The centre > General > Name & logo: the centre's own mark, which
  leads where a person deals with the centre - the client area, the public pages -
  while the product signs at the foot (crm.marchio); the sidebar wears the
  product's logo. The preview draws those pages' head and foot before saving.
-->
<template>
  <div
    class="flex h-full flex-col gap-6 px-6 py-8 text-ink-gray-8 max-md:px-3 max-md:py-5"
  >
    <!-- Header -->
    <div
      class="flex justify-between px-2 text-ink-gray-8 max-md:flex-col max-md:items-start max-md:gap-3"
    >
      <div class="flex flex-col gap-1">
        <h2
          class="flex gap-2 text-2xl-semibold leading-tight md:h-5 md:leading-none"
        >
          {{ __('Name & logo') }}
        </h2>
        <p class="text-p-base text-ink-gray-6">
          {{
            __(
              "The centre's name and logo, at the top of every page the people it looks after open: booking, forms, their area. {brand} signs at the bottom.",
            )
          }}
        </p>
      </div>
      <div
        class="flex items-start space-x-2 w-3/12 justify-end max-md:w-auto max-md:justify-start"
      >
        <Button
          v-if="settings.isDirty"
          :label="__('Update')"
          variant="solid"
          :loading="settings.loading"
          @click="updateSettings"
        />
      </div>
    </div>

    <!-- Fields: once the settings have come, or the first draw reads a name
         from nothing -->
    <div
      v-if="settings.doc"
      class="flex flex-1 flex-col gap-4 overflow-y-auto p-2"
    >
      <!-- on a phone the field goes under its label: beside it, it had room
           for «Enter Brand N» -->
      <div
        class="flex items-center justify-between gap-8 max-md:flex-col max-md:items-stretch max-md:gap-2"
      >
        <div class="flex min-w-0 flex-col">
          <div class="text-p-base-medium text-ink-gray-7">
            {{ __("Centre's name") }}
          </div>
          <div class="text-p-sm text-ink-gray-5">
            {{
              __(
                'How the centre is called to the people it looks after: in the emails and on the public pages.',
              )
            }}
          </div>
        </div>
        <div class="flex items-center gap-2">
          <FormControl
            v-model="settings.doc.brand_name"
            class="max-md:flex-1"
            type="text"
            size="md"
            :placeholder="__('e.g. Centro Aurora')"
          />
        </div>
      </div>
      <div class="h-px border-t border-outline-elevation-2" />

      <!-- logo -->
      <div
        class="flex items-center gap-5 max-md:flex-col max-md:items-stretch max-md:gap-3"
      >
        <div
          class="grid h-16 w-28 shrink-0 place-items-center rounded-lg border border-outline-gray-2 bg-white p-2"
        >
          <img
            v-if="logo"
            :src="logo"
            :alt="__('Logo')"
            class="max-h-full max-w-full object-contain"
          />
          <ImageIcon v-else class="size-5 text-ink-gray-4" />
        </div>
        <div class="flex min-w-0 flex-1 flex-col gap-1">
          <span class="text-p-base-medium text-ink-gray-7">{{
            __('Logo')
          }}</span>
          <span class="text-p-sm text-ink-gray-5">
            {{
              __(
                'PNG or SVG. A wide logo, with the name in it, goes on its own; a square one, beside the name. Without one, the initials stand in.',
              )
            }}
          </span>
        </div>
        <div class="shrink-0">
          <ImageUploader
            :image_url="settings.doc?.brand_logo"
            @upload="(url) => (settings.doc.brand_logo = url)"
            @remove="() => (settings.doc.brand_logo = '')"
          />
        </div>
      </div>
      <div class="h-px border-t border-outline-elevation-2" />

      <!-- how it looks, before saving -->
      <div class="flex flex-col gap-3">
        <div class="text-p-base-medium text-ink-gray-7">
          {{ __('How it looks') }}
        </div>
        <div class="max-w-md">
          <figure class="flex min-w-0 flex-col gap-2">
            <figcaption class="text-p-sm text-ink-gray-5">
              {{ __('On the booking page, the forms and their area') }}
            </figcaption>
            <div
              class="flex flex-col gap-4 rounded-lg border border-outline-gray-2 bg-surface-base p-4"
              aria-hidden="true"
            >
              <div class="flex min-w-0 items-center gap-2.5">
                <img
                  v-if="logo && forma === 'wide'"
                  :src="logo"
                  alt=""
                  class="h-9 min-w-0 max-w-full object-contain object-left dark:rounded dark:bg-white dark:px-1.5 dark:py-1"
                />
                <template v-else>
                  <CentreTile
                    v-if="logo"
                    :logo="logo"
                    :forma="forma"
                    :nome="nome"
                    class="size-10"
                  />
                  <span
                    v-if="nome"
                    class="min-w-0 truncate text-lg font-semibold text-ink-gray-9"
                  >
                    {{ nome }}
                  </span>
                  <img
                    v-else-if="!logo"
                    :src="platform.logo"
                    alt=""
                    class="h-7 w-auto"
                  />
                </template>
              </div>
              <div class="flex flex-col gap-1.5">
                <span class="h-2 w-3/4 rounded bg-surface-gray-2" />
                <span class="h-2 w-1/2 rounded bg-surface-gray-2" />
              </div>
              <div
                class="flex items-center justify-center gap-1.5 text-xs text-ink-gray-5"
              >
                <CRMLogo class="size-4 shrink-0 rounded-[4px]" />
                {{ __('Powered by {0}', [platform.name]) }}
              </div>
            </div>
          </figure>
        </div>
      </div>
    </div>
  </div>
</template>
<script setup>
import ImageIcon from '~icons/lucide/image'
import ImageUploader from '@/components/Controls/ImageUploader.vue'
import CentreTile from '@/components/CentreTile.vue'
import CRMLogo from '@/components/Icons/CRMLogo.vue'
import { useFormaDelLogo } from '@/composables/formaDelLogo'
import { FormControl } from 'frappe-ui'
import { getSettings } from '@/stores/settings'
import { showSettings } from '@/composables/settings'
import { marchio, nomeDelCentro } from '@/utils/marchio'
import { computed } from 'vue'

const { _settings: settings, setupBrand } = getSettings()
const platform = marchio()

// what is being typed and uploaded, before it is saved
const logo = computed(() => settings.doc?.brand_logo || '')
const nome = computed(() => nomeDelCentro(settings.doc?.brand_name))
const forma = useFormaDelLogo(logo, () =>
  logo.value && logo.value === platform.centre_logo
    ? platform.centre_logo_shape
    : '',
)

function updateSettings() {
  settings.save.submit(null, {
    onSuccess: () => {
      showSettings.value = false
      setupBrand()
    },
  })
}
</script>
