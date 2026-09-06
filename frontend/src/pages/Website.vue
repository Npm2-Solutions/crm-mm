<template>
  <LayoutHeader>
    <template #left-header>
      <Breadcrumbs
        :items="[{ label: __('Site'), route: { name: 'Website' } }]"
      />
    </template>
    <template #right-header>
      <Button
        v-if="status.data?.enabled && siteUrl"
        variant="ghost"
        :label="__('Open the site')"
        iconLeft="external-link"
        @click="openExternal(siteUrl)"
      />
      <Button
        variant="ghost"
        :label="__('Settings')"
        iconLeft="settings"
        @click="openWebsiteSettings"
      />
      <Button
        v-if="tab === 'pages' && ready"
        variant="solid"
        :label="__('New page')"
        iconLeft="plus"
        @click="startNewPage"
      />
    </template>
  </LayoutHeader>

  <div class="flex-1 overflow-y-auto px-3 py-4 sm:px-5">
    <div class="mx-auto flex w-full max-w-6xl flex-col gap-4">
      <!-- Builder missing: say what to run instead of showing an empty screen -->
      <div
        v-if="status.fetched && !status.data?.builder_installed"
        class="flex flex-col gap-3 rounded-xl border border-outline-gray-2 bg-surface-gray-1 px-5 py-4"
      >
        <div class="flex flex-col gap-1">
          <span class="text-p-base-medium text-ink-gray-8">
            {{ __('Frappe Builder is not installed on this site') }}
          </span>
          <span class="text-p-sm text-ink-gray-5">
            {{
              __(
                'The Site section builds pages with Builder. Install it once on the bench, then reload.',
              )
            }}
          </span>
        </div>
        <div
          class="rounded-lg bg-surface-gray-3 px-3 py-2 font-mono text-xs text-ink-gray-7"
        >
          bench get-app builder<br />
          bench --site {{ siteName }} install-app builder<br />
          bench --site {{ siteName }} migrate
        </div>
      </div>

      <!-- site switched off: one button, no lecture -->
      <div
        v-else-if="status.fetched && !status.data?.enabled"
        class="flex items-center justify-between gap-3 rounded-xl border border-outline-gray-2 bg-surface-gray-1 px-4 py-3"
      >
        <div class="flex flex-col">
          <span class="text-p-base-medium text-ink-gray-8">
            {{ __('The website is off') }}
          </span>
          <span class="text-p-sm text-ink-gray-5">
            {{
              __(
                'Turn it on to publish pages. Nothing goes live until you publish it.',
              )
            }}
          </span>
        </div>
        <Button
          variant="solid"
          :label="__('Turn on')"
          :loading="enabling"
          @click="enableSite"
        />
      </div>

      <template v-if="ready">
        <div class="flex items-center gap-1">
          <Button
            v-for="entry in tabs"
            :key="entry.value"
            :variant="tab === entry.value ? 'subtle' : 'ghost'"
            :label="entry.label"
            @click="tab = entry.value"
          />
        </div>

        <!-- ------------------------------------------------ pages -->
        <div v-if="tab === 'pages'" class="flex flex-col gap-3">
          <div
            v-if="pages.data?.length"
            class="divide-y divide-outline-gray-1 rounded-lg border border-outline-gray-2"
          >
            <div
              v-for="page in pages.data"
              :key="page.name"
              class="flex items-center gap-3 px-3 py-2.5 hover:bg-surface-gray-1"
            >
              <div class="min-w-0 flex-1">
                <div
                  class="flex items-center gap-2 truncate text-p-base-medium text-ink-gray-8"
                >
                  {{ page.page_title }}
                  <Badge
                    v-if="page.is_home"
                    :label="__('Home')"
                    theme="blue"
                    size="sm"
                  />
                </div>
                <div class="truncate font-mono text-p-sm text-ink-gray-5">
                  /{{ page.route }}
                </div>
              </div>
              <Badge
                v-if="page.has_draft"
                :label="__('Unpublished changes')"
                theme="orange"
                size="sm"
              />
              <Badge
                :label="page.published ? __('Published') : __('Draft')"
                :theme="page.published ? 'green' : 'gray'"
                size="sm"
              />
              <Button
                variant="subtle"
                :label="__('Design')"
                @click="design(page)"
              />
              <Dropdown :options="pageActions(page)" placement="right">
                <Button variant="ghost" icon="more-horizontal" />
              </Dropdown>
            </div>
          </div>
          <div
            v-else-if="!pages.loading"
            class="rounded-lg border border-dashed border-outline-gray-2 px-4 py-8 text-center"
          >
            <p class="text-p-base text-ink-gray-6">
              {{ __('No pages yet.') }}
            </p>
            <Button
              class="mt-3"
              variant="solid"
              :label="__('Create the first page')"
              @click="startNewPage"
            />
          </div>
        </div>

        <!-- ------------------------------------------------ showcase -->
        <div v-else class="flex flex-col gap-3">
          <div class="flex items-center gap-1">
            <Button
              v-for="entry in showcaseTabs"
              :key="entry.value"
              :variant="showcaseType === entry.value ? 'subtle' : 'ghost'"
              :label="entry.label"
              size="sm"
              @click="showcaseType = entry.value"
            />
            <span class="ml-2 text-p-sm text-ink-gray-5">
              {{ __('Only what you publish here appears on the site.') }}
            </span>
          </div>

          <div
            v-if="showcase.data?.length"
            class="divide-y divide-outline-gray-1 rounded-lg border border-outline-gray-2"
          >
            <div
              v-for="row in showcase.data"
              :key="row.name"
              class="flex items-center gap-3 px-3 py-2.5 hover:bg-surface-gray-1"
            >
              <img
                v-if="row.image"
                :src="row.image"
                alt=""
                class="size-9 shrink-0 rounded-md object-cover"
              />
              <div
                v-else
                class="size-9 shrink-0 rounded-md bg-surface-gray-3"
              />
              <div class="min-w-0 flex-1">
                <div class="truncate text-p-base-medium text-ink-gray-8">
                  {{ row.title }}
                </div>
                <div class="truncate text-p-sm text-ink-gray-5">
                  {{ row.short_description || __('No short description yet') }}
                </div>
              </div>
              <span
                v-if="row.publish_on_website && row.website_slug"
                class="shrink-0 font-mono text-p-sm text-ink-gray-5"
              >
                /{{
                  showcaseType === 'CRM Service' ? 'servizi' : 'prodotti'
                }}/{{ row.website_slug }}
              </span>
              <Button
                variant="ghost"
                :label="__('Edit card')"
                @click="editShowcase(row)"
              />
              <Switch
                size="sm"
                :modelValue="Boolean(row.publish_on_website)"
                @update:modelValue="(v) => togglePublish(row, v)"
              />
            </div>
          </div>
          <div
            v-else-if="!showcase.loading"
            class="rounded-lg border border-dashed border-outline-gray-2 px-4 py-8 text-center text-p-base text-ink-gray-6"
          >
            {{ __('Nothing to publish yet.') }}
          </div>
        </div>
      </template>
    </div>
  </div>

  <!-- new page -->
  <Dialog v-model="showNewPage" :options="{ title: __('New page') }">
    <template #body-content>
      <div class="flex flex-col gap-4">
        <FormControl
          v-model="newPage.title"
          type="text"
          :label="__('Page name')"
          :placeholder="__('Home, Services, About us…')"
          @input="syncRoute"
        />
        <FormControl
          v-model="newPage.route"
          type="text"
          :label="__('Address')"
          :description="
            routeCheck.reason || __('Where the page answers, after the domain.')
          "
        />
        <p v-if="routeCheck.reason" class="text-p-sm text-ink-red-4">
          {{ routeCheck.reason }}
          <button
            v-if="routeCheck.suggestion"
            class="underline"
            @click="newPage.route = routeCheck.suggestion"
          >
            {{ __('Use {0}', [routeCheck.suggestion]) }}
          </button>
        </p>
      </div>
    </template>
    <template #actions>
      <Button
        class="w-full"
        variant="solid"
        :label="__('Create and design')"
        :loading="creating"
        :disabled="!newPage.title || routeCheck.reason"
        @click="createPage"
      />
    </template>
  </Dialog>

  <!-- showcase card -->
  <Dialog
    v-model="showShowcase"
    :options="{ title: __('Website card'), size: '2xl' }"
  >
    <template #body-content>
      <div v-if="editing" class="flex flex-col gap-4">
        <div class="grid grid-cols-2 gap-3">
          <FormControl
            v-model="editing.website_slug"
            type="text"
            :label="__('Address')"
            :description="__('Filled in from the name when you publish it.')"
          />
          <FormControl
            v-model.number="editing.website_order"
            type="number"
            :label="__('Sort order')"
          />
        </div>
        <FormControl
          v-model="editing.short_description"
          type="textarea"
          :rows="2"
          :label="__('Short description')"
          :description="__('One or two lines, shown on the card.')"
        />
        <div class="flex flex-col gap-1.5">
          <span class="text-xs text-ink-gray-5">{{ __('Cover image') }}</span>
          <div class="flex items-center gap-3">
            <img
              v-if="editing.image"
              :src="editing.image"
              alt=""
              class="size-16 rounded-lg object-cover"
            />
            <FileUploader
              :fileTypes="['image/*']"
              :validateFile="validateImage"
              @success="(file) => (editing.image = file.file_url)"
            >
              <template #default="{ openFileSelector, uploading }">
                <Button
                  :loading="uploading"
                  :label="editing.image ? __('Replace') : __('Upload')"
                  @click="openFileSelector"
                />
              </template>
            </FileUploader>
            <Button
              v-if="editing.image"
              variant="ghost"
              :label="__('Remove')"
              @click="editing.image = ''"
            />
          </div>
        </div>
        <div class="grid grid-cols-2 gap-3">
          <FormControl
            v-model="editing.cta_type"
            type="select"
            :label="__('Button')"
            :options="ctaOptions"
          />
          <FormControl
            v-model="editing.cta_label"
            type="text"
            :label="__('Button label')"
          />
        </div>
        <Link
          v-if="showcaseType === 'CRM Service' && editing.cta_type === 'Book'"
          doctype="CRM Booking Calendar"
          :modelValue="editing.booking_calendar"
          :label="__('Booking calendar')"
          @update:modelValue="(v) => (editing.booking_calendar = v)"
        />
        <FormControl
          v-else-if="editing.cta_type !== 'None'"
          v-model="editing.cta_target"
          type="text"
          :label="__('Button target')"
          :description="__('A form route, or a full address.')"
        />
      </div>
    </template>
    <template #actions>
      <Button
        class="w-full"
        variant="solid"
        :label="__('Save')"
        :loading="savingCard"
        @click="saveShowcase"
      />
    </template>
  </Dialog>
</template>

<script setup>
import LayoutHeader from '@/components/LayoutHeader.vue'
import Link from '@/components/Controls/Link.vue'
import { showSettings, activeSettingsPage } from '@/composables/settings'
import { usersStore } from '@/stores/users'
import {
  createResource,
  Badge,
  Breadcrumbs,
  Dialog,
  Dropdown,
  FileUploader,
  FormControl,
  Switch,
  call,
  toast,
} from 'frappe-ui'
import { ref, reactive, computed, watch } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()
const { isManager } = usersStore()

const tab = ref('pages')
const showcaseType = ref('CRM Service')
const enabling = ref(false)
const creating = ref(false)
const savingCard = ref(false)
const showNewPage = ref(false)
const showShowcase = ref(false)
const editing = ref(null)

const tabs = computed(() => [
  { value: 'pages', label: __('Pages') },
  { value: 'showcase', label: __('Showcase') },
])
const showcaseTabs = computed(() => [
  { value: 'CRM Service', label: __('Services') },
  { value: 'CRM Product', label: __('Products') },
])
const ctaOptions = computed(() => [
  { label: __('Book'), value: 'Book' },
  { label: __('Form'), value: 'Form' },
  { label: __('Link'), value: 'Link' },
  { label: __('None'), value: 'None' },
])

const status = createResource({ url: 'crm.api.site.get_status', auto: true })

const ready = computed(
  () => status.data?.builder_installed && status.data?.enabled,
)
const siteUrl = computed(() => {
  const home = status.data?.home_page
  if (!status.data?.site_url) return ''
  return home ? `${status.data.site_url}/${home}` : status.data.site_url
})
const siteName = computed(() => window.location.hostname)

const pages = createResource({
  url: 'crm.api.site.list_pages',
  auto: false,
})

const showcase = createResource({
  url: 'crm.api.site.list_showcase',
  makeParams: () => ({ doctype: showcaseType.value }),
  auto: false,
})

// Load a tab's data the first time it is opened, and whenever the site becomes usable.
watch(
  [ready, tab, showcaseType],
  () => {
    if (!ready.value) return
    if (tab.value === 'pages') pages.reload()
    else showcase.reload()
  },
  { immediate: true },
)

function openWebsiteSettings() {
  activeSettingsPage.value = 'Website'
  showSettings.value = true
}

function openExternal(url) {
  window.open(url, '_blank', 'noopener')
}

async function enableSite() {
  if (!isManager()) return
  enabling.value = true
  try {
    await call('frappe.client.set_value', {
      doctype: 'CRM Website Settings',
      name: 'CRM Website Settings',
      fieldname: 'enabled',
      value: 1,
    })
    await status.reload()
  } finally {
    enabling.value = false
  }
}

// ---------------------------------------------------------------- pages

const newPage = reactive({ title: '', route: '' })
const routeCheck = reactive({ reason: '', suggestion: '' })
let routeTimer = null

function slugify(text) {
  return (text || '')
    .normalize('NFKD')
    .replace(/[̀-ͯ]/g, '')
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-+|-+$/g, '')
}

function startNewPage() {
  newPage.title = ''
  newPage.route = ''
  routeCheck.reason = ''
  routeCheck.suggestion = ''
  showNewPage.value = true
}

function syncRoute() {
  newPage.route = slugify(newPage.title)
}

// Validate against the server, which owns the reserved list — the client cannot know
// which routes other apps have claimed.
watch(
  () => newPage.route,
  (route) => {
    clearTimeout(routeTimer)
    routeCheck.reason = ''
    routeCheck.suggestion = ''
    if (!route) return
    routeTimer = setTimeout(async () => {
      const result = await call('crm.api.site.check_route', { route })
      if (!result.ok) {
        routeCheck.reason = result.reason
        routeCheck.suggestion = result.suggestion
      }
    }, 300)
  },
)

async function createPage() {
  creating.value = true
  try {
    const page = await call('crm.api.site.create_page', {
      title: newPage.title,
      route: newPage.route,
    })
    showNewPage.value = false
    pages.reload()
    design(page)
  } catch (error) {
    toast.error(error.messages?.[0] || __('Could not create the page'))
  } finally {
    creating.value = false
  }
}

function design(page) {
  router.push({ name: 'WebsitePage', params: { name: page.name } })
}

function pageActions(page) {
  return [
    {
      label: page.published ? __('Withdraw') : __('Publish'),
      icon: page.published ? 'eye-off' : 'upload-cloud',
      onClick: () => setPublished(page, !page.published),
    },
    {
      label: __('Open'),
      icon: 'external-link',
      condition: () => page.published,
      onClick: () => openExternal(page.url),
    },
    {
      label: __('Set as home page'),
      icon: 'home',
      condition: () => page.published && !page.is_home,
      onClick: () => setHome(page),
    },
    {
      label: __('Duplicate'),
      icon: 'copy',
      onClick: async () => {
        await call('crm.api.site.duplicate_page', { name: page.name })
        pages.reload()
      },
    },
    {
      label: __('Delete'),
      icon: 'trash-2',
      onClick: () => remove(page),
    },
  ].filter((action) => !action.condition || action.condition())
}

async function setPublished(page, published) {
  try {
    await call('crm.api.site.set_published', { name: page.name, published })
    toast.success(published ? __('Published') : __('Withdrawn'))
    pages.reload()
  } catch (error) {
    toast.error(error.messages?.[0] || __('Could not change the page'))
  }
}

async function setHome(page) {
  await call('crm.api.site.set_home_page', { route: page.route })
  toast.success(__('Home page updated'))
  status.reload()
  pages.reload()
}

async function remove(page) {
  if (!window.confirm(__('Delete {0}?', [page.page_title]))) return
  try {
    await call('crm.api.site.delete_page', { name: page.name })
    pages.reload()
  } catch (error) {
    toast.error(error.messages?.[0] || __('Could not delete the page'))
  }
}

// ---------------------------------------------------------------- showcase

function editShowcase(row) {
  editing.value = { ...row }
  showShowcase.value = true
}

function validateImage(file) {
  if (file.size > 5 * 1024 * 1024) return __('Images must be under 5 MB')
}

async function togglePublish(row, published) {
  row.publish_on_website = published ? 1 : 0
  try {
    const result = await call('crm.api.site.set_showcase_published', {
      doctype: showcaseType.value,
      name: row.name,
      published: published ? 1 : 0,
    })
    row.website_slug = result.slug
  } catch (error) {
    row.publish_on_website = published ? 0 : 1
    toast.error(error.messages?.[0] || __('Could not publish'))
  }
}

async function saveShowcase() {
  savingCard.value = true
  try {
    await call('crm.api.site.save_showcase_item', {
      doctype: showcaseType.value,
      name: editing.value.name,
      values: editing.value,
    })
    showShowcase.value = false
    showcase.reload()
  } catch (error) {
    toast.error(error.messages?.[0] || __('Could not save the card'))
  } finally {
    savingCard.value = false
  }
}
</script>
