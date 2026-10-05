<!--
  What the software is, who makes it and under which licence: the notices the
  AGPL asks every screen of the work to be able to show (copyright, no warranty,
  where the licence is), with the product's own name.
-->
<template>
  <Dialog v-model:open="show" :size="'sm'">
    <template #body>
      <div class="p-4 pt-5">
        <div class="flex flex-col items-center text-center">
          <CRMLogo class="mb-3 size-12" />
          <h3 class="text-2xl-semibold text-ink-gray-9">{{ platform.name }}</h3>
          <p
            v-if="platform.description"
            class="mt-1 text-p-base text-ink-gray-6"
          >
            {{ platform.description }}
          </p>
        </div>
        <hr class="mx-2 my-3 border-t" />
        <div class="flex flex-col gap-2 px-2 text-p-sm text-ink-gray-6">
          <p>{{ __('© NPM2 Solutions Srl and contributors') }}</p>
          <p>
            {{
              __(
                'Free software under the GNU Affero General Public License, version 3, with no warranty. The source code of this version is available from NPM2 Solutions Srl.',
              )
            }}
          </p>
          <!-- the Italian words of the emoji are Unicode's (src/assets/emoji) -->
          <p>
            {{
              __(
                'The names of the emoji in Italian are Unicode CLDR data, © Unicode, Inc., under the Unicode License v3.',
              )
            }}
          </p>
        </div>
        <a
          class="mt-2 flex items-center rounded px-2 py-2 hover:bg-surface-gray-1"
          target="_blank"
          rel="noopener"
          href="https://www.gnu.org/licenses/agpl-3.0.html"
        >
          <LucideScale class="mr-2 size-4 text-ink-gray-7" />
          <span class="text-base text-ink-gray-8">
            {{ __('Read the licence') }}
          </span>
        </a>
      </div>
    </template>
  </Dialog>
</template>
<script setup>
import CRMLogo from '@/components/Icons/CRMLogo.vue'
import { marchio } from '@/utils/marchio'
import LucideScale from '~icons/lucide/scale'

let show = defineModel({ type: Boolean })
// the product's name and line are the brand's - the vertical's
const platform = marchio()
</script>
