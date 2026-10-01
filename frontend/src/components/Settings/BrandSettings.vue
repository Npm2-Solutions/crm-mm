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
              "The centre's name and logo. The product's brand, {brand}, stays everywhere: the logo goes beside it.",
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

    <!-- Fields -->
    <div class="flex flex-1 flex-col p-2 gap-4 overflow-y-auto">
      <!-- Brand Anm -->
      <!-- on a phone the field goes under its label: beside it, it had room
           for «Enter Brand N» -->
      <div
        class="flex items-center justify-between gap-8 max-md:flex-col max-md:items-stretch max-md:gap-2"
      >
        <div class="flex min-w-0 flex-col">
          <div class="text-p-base-medium text-ink-gray-7">
            {{ __('Brand Name') }}
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
            :placeholder="__('Enter Brand Name')"
          />
        </div>
      </div>
      <div class="h-px border-t border-outline-elevation-2" />

      <!-- logo -->
      <div class="flex flex-col justify-between gap-4">
        <div class="flex items-center flex-1 gap-5">
          <div
            class="flex items-center justify-center rounded border border-outline-elevation-2 size-20"
          >
            <img
              v-if="settings.doc?.brand_logo"
              :src="settings.doc?.brand_logo"
              alt="Logo"
              class="size-8 rounded"
            />
            <ImageIcon v-else class="size-5 text-ink-gray-4" />
          </div>
          <div class="flex flex-1 flex-col gap-1">
            <span class="text-p-base-medium text-ink-gray-7">{{
              __('Brand Logo')
            }}</span>
            <span class="text-p-sm text-ink-gray-5">
              {{
                __(
                  'Beside the icon of {brand} in the sidebar, in the client area and on the public pages. PNG or SVG, at least 64 px high.',
                )
              }}
            </span>
          </div>
          <div>
            <ImageUploader
              image_type="image/ico"
              :image_url="settings.doc?.brand_logo"
              @upload="(url) => (settings.doc.brand_logo = url)"
              @remove="() => (settings.doc.brand_logo = '')"
            />
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
<script setup>
import ImageIcon from '~icons/lucide/image'
import ImageUploader from '@/components/Controls/ImageUploader.vue'
import { FormControl } from 'frappe-ui'
import { getSettings } from '@/stores/settings'
import { showSettings } from '@/composables/settings'

const { _settings: settings, setupBrand } = getSettings()

function updateSettings() {
  settings.save.submit(null, {
    onSuccess: () => {
      showSettings.value = false
      setupBrand()
    },
  })
}
</script>
