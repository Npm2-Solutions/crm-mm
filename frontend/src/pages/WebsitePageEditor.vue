<template>
  <div
    class="flex h-screen w-screen flex-col overflow-hidden bg-surface-gray-2"
  >
    <!-- One thin strip, and nothing else of the CRM: Builder brings its own toolbar and
         panels, so anything more here would just be a second set of chrome over the same
         canvas. Back, where you are, and whether it is live — that is all this needs. -->
    <header
      class="flex h-9 shrink-0 items-center gap-2 border-b border-outline-gray-2 bg-surface-white px-2"
    >
      <Button variant="ghost" size="sm" icon="arrow-left" @click="back">
        <template #default>
          <span class="text-p-sm">{{ __('Site') }}</span>
        </template>
      </Button>
      <span class="truncate text-p-sm text-ink-gray-7">
        {{ page.data?.page_title || __('Page') }}
      </span>
      <span
        v-if="page.data?.route"
        class="hidden truncate font-mono text-xs text-ink-gray-4 sm:inline"
      >
        /{{ page.data.route }}
      </span>
      <Badge
        v-if="page.data"
        :label="page.data.published ? __('Published') : __('Draft')"
        :theme="page.data.published ? 'green' : 'gray'"
        size="sm"
      />
      <Badge
        v-if="page.data?.has_draft"
        :label="__('Unpublished changes')"
        theme="orange"
        size="sm"
      />
      <a
        v-if="page.data?.published"
        :href="page.data.url"
        target="_blank"
        rel="noopener"
        class="ml-auto text-p-sm text-ink-gray-5 hover:text-ink-gray-8"
      >
        {{ __('Open the page') }}
      </a>
    </header>

    <div class="relative min-h-0 flex-1">
      <!-- Builder refuses to render below its own breakpoint, and its message would read
           as a broken CRM. Say it ourselves. -->
      <div
        v-if="tooSmall"
        class="flex h-full flex-col items-center justify-center gap-2 px-6 text-center"
      >
        <span class="text-p-lg-medium text-ink-gray-8">
          {{ __('The canvas needs a bigger screen') }}
        </span>
        <span class="max-w-sm text-p-base text-ink-gray-5">
          {{
            __(
              'Designing pages works from a tablet in landscape or a desktop. Everything else about the site works here.',
            )
          }}
        </span>
        <Button class="mt-2" :label="__('Back to the site')" @click="back" />
      </div>

      <iframe
        v-else-if="editorUrl"
        ref="frame"
        :src="editorUrl"
        class="block h-full w-full border-0"
        :title="__('Page editor')"
        @load="onFrameLoad"
      />

      <div
        v-else
        class="flex h-full items-center justify-center text-p-base text-ink-gray-5"
      >
        {{ __('Loading the editor…') }}
      </div>
    </div>
  </div>
</template>

<script setup>
import { Badge, createResource, toast } from 'frappe-ui'
import { ref, computed, onMounted, onBeforeUnmount, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'

const route = useRoute()
const router = useRouter()

const frame = ref(null)
const width = ref(window.innerWidth)
let watcher = null

// Builder's own guard is 768px; stop a little earlier so the canvas has room to work.
const tooSmall = computed(() => width.value < 900)

const status = createResource({ url: 'crm.api.site.get_status', auto: true })

const page = createResource({
  url: 'crm.api.site.get_page',
  makeParams: () => ({ name: route.params.name }),
  auto: true,
})

const editorPath = computed(() => status.data?.editor_path || 'builder')
const editorUrl = computed(() =>
  status.data ? `/${editorPath.value}/page/${route.params.name}` : '',
)

function onResize() {
  width.value = window.innerWidth
}

onMounted(() => {
  window.addEventListener('resize', onResize)
  // The iframe and the CRM share an origin, so we can tell when the editor navigates
  // somewhere else — its dashboard, or /app on a permission failure — and keep the user
  // inside the CRM instead of letting a second application take over the frame.
  watcher = setInterval(keepInsideEditor, 500)
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', onResize)
  clearInterval(watcher)
})

function keepInsideEditor() {
  const el = frame.value
  if (!el || !editorUrl.value) return
  let path
  try {
    path = el.contentWindow?.location?.pathname
  } catch (error) {
    // a cross-origin redirect (an SSO bounce, say) — nothing we can read, nothing to do
    return
  }
  if (!path) return
  if (path.startsWith(`/${editorPath.value}/page/`)) return
  if (path.startsWith(`/${editorPath.value}`)) {
    // Builder's own dashboard: the CRM already lists the pages, so go back to ours
    back()
    return
  }
  // anything else (e.g. /app after a permission bounce) means the editor gave up
  toast.error(__('The editor could not open this page.'))
  back()
}

function onFrameLoad() {
  // Builder saves and publishes on its own schedule; the strip's state comes from us.
  page.reload()
}

function back() {
  router.push({ name: 'Website' })
}

watch(
  () => route.params.name,
  () => page.reload(),
)
</script>
