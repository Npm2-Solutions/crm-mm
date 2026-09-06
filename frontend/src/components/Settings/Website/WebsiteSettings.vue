<template>
  <div class="flex h-full flex-col gap-6 px-6 py-8 text-ink-gray-8">
    <div class="flex items-center justify-between px-2">
      <div class="flex flex-col gap-1">
        <h2 class="flex h-5 gap-2 text-2xl-semibold leading-none">
          {{ __('Website') }}
        </h2>
        <p class="text-p-base text-ink-gray-6">
          {{
            __(
              'Brand, menu, footer and tracking. Pages and the showcase live in the Site section.',
            )
          }}
        </p>
      </div>
      <Button
        variant="solid"
        :label="__('Save')"
        :loading="saving"
        @click="save"
      />
    </div>

    <div class="flex flex-1 flex-col gap-7 overflow-y-auto px-2">
      <!-- ------------------------------------------------ general -->
      <section class="flex flex-col gap-3">
        <div
          class="flex items-center justify-between rounded-lg border border-outline-gray-2 px-3 py-2.5"
        >
          <div class="flex flex-col">
            <span class="text-p-base-medium text-ink-gray-8">
              {{ __('Website enabled') }}
            </span>
            <span class="text-p-sm text-ink-gray-5">
              {{
                __(
                  'Adds the Site section to the sidebar. Pages stay as they are.',
                )
              }}
            </span>
          </div>
          <Switch v-model="form.enabled" size="sm" />
        </div>

        <div class="grid grid-cols-2 gap-3">
          <FormControl
            v-model="form.site_title"
            type="text"
            :label="__('Site title')"
          />
          <FormControl
            v-model="form.home_page"
            type="select"
            :label="__('Home page')"
            :options="homeOptions"
            :description="__('Only published pages can be the home page.')"
          />
        </div>
        <FormControl
          v-model="form.tagline"
          type="textarea"
          :rows="2"
          :label="__('Tagline')"
        />
        <div
          class="flex items-center justify-between rounded-lg border border-outline-gray-2 px-3 py-2.5"
        >
          <div class="flex flex-col">
            <span class="text-p-base-medium text-ink-gray-8">
              {{ __('Serve the home page at /') }}
            </span>
            <span class="text-p-sm text-ink-gray-5">
              {{
                __(
                  'The site answers at the domain root. The CRM stays at /crm either way.',
                )
              }}
            </span>
          </div>
          <Switch v-model="form.serve_at_root" size="sm" />
        </div>
      </section>

      <!-- ------------------------------------------------ brand -->
      <section class="flex flex-col gap-3">
        <h3 class="text-p-base-medium text-ink-gray-8">{{ __('Brand') }}</h3>
        <div class="flex items-start gap-6">
          <ImageField
            :label="__('Logo')"
            :url="form.logo"
            @update="(url) => (form.logo = url)"
          />
          <ImageField
            :label="__('Favicon')"
            :url="form.favicon"
            @update="(url) => (form.favicon = url)"
          />
        </div>
        <div class="grid grid-cols-2 gap-3">
          <FormControl
            v-model="form.primary_color"
            type="text"
            :label="__('Primary colour')"
            placeholder="#4C7EFF"
          />
          <FormControl
            v-model="form.font_family"
            type="text"
            :label="__('Font')"
            placeholder="Inter"
            :description="
              __('A Google Fonts family. Empty keeps the theme default.')
            "
          />
        </div>
      </section>

      <!-- ------------------------------------------------ menu -->
      <section class="flex flex-col gap-3">
        <div class="flex items-center justify-between">
          <h3 class="text-p-base-medium text-ink-gray-8">{{ __('Menu') }}</h3>
          <Button
            variant="ghost"
            iconLeft="plus"
            :label="__('Add item')"
            @click="addNavItem"
          />
        </div>
        <div
          v-if="form.nav_items.length"
          class="flex flex-col gap-2 rounded-lg border border-outline-gray-2 p-2"
        >
          <div
            v-for="(item, index) in form.nav_items"
            :key="index"
            class="flex items-center gap-2"
          >
            <FormControl
              v-model="item.label"
              type="text"
              class="w-40"
              :placeholder="__('Label')"
            />
            <FormControl
              v-model="item.link_type"
              type="select"
              class="w-32"
              :options="linkTypes"
            />
            <FormControl
              v-model="item.target"
              type="text"
              class="flex-1"
              :placeholder="targetHint(item.link_type)"
            />
            <Button
              variant="ghost"
              icon="chevron-up"
              :disabled="index === 0"
              @click="moveNavItem(index, -1)"
            />
            <Button
              variant="ghost"
              icon="chevron-down"
              :disabled="index === form.nav_items.length - 1"
              @click="moveNavItem(index, 1)"
            />
            <Button
              variant="ghost"
              icon="lucide-trash-2"
              @click="form.nav_items.splice(index, 1)"
            />
          </div>
        </div>
        <p v-else class="text-p-sm text-ink-gray-5">
          {{ __('No menu items yet.') }}
        </p>
      </section>

      <!-- ------------------------------------------------ footer -->
      <section class="flex flex-col gap-3">
        <h3 class="text-p-base-medium text-ink-gray-8">
          {{ __('Footer & legal') }}
        </h3>
        <div class="grid grid-cols-2 gap-3">
          <FormControl
            v-model="form.company_name"
            type="text"
            :label="__('Registered name')"
          />
          <FormControl
            v-model="form.vat_number"
            type="text"
            :label="__('VAT number')"
          />
        </div>
        <FormControl
          v-model="form.address"
          type="textarea"
          :rows="2"
          :label="__('Address')"
        />
        <div class="grid grid-cols-3 gap-3">
          <FormControl v-model="form.email" type="text" :label="__('Email')" />
          <FormControl v-model="form.phone" type="text" :label="__('Phone')" />
          <FormControl
            v-model="form.whatsapp_number"
            type="text"
            :label="__('WhatsApp')"
            placeholder="393331234567"
            :description="__('Digits only, with the country code.')"
          />
        </div>
        <FormControl
          v-model="form.footer_text"
          type="textarea"
          :rows="2"
          :label="__('Footer text')"
        />
        <div class="grid grid-cols-2 gap-3">
          <FormControl
            v-model="form.privacy_route"
            type="text"
            :label="__('Privacy page')"
          />
          <FormControl
            v-model="form.terms_route"
            type="text"
            :label="__('Terms page')"
          />
        </div>

        <div class="flex items-center justify-between">
          <span class="text-p-sm text-ink-gray-6">{{
            __('Social profiles')
          }}</span>
          <Button
            variant="ghost"
            iconLeft="plus"
            :label="__('Add')"
            @click="addSocial"
          />
        </div>
        <div
          v-if="form.social_links.length"
          class="flex flex-col gap-2 rounded-lg border border-outline-gray-2 p-2"
        >
          <div
            v-for="(link, index) in form.social_links"
            :key="index"
            class="flex items-center gap-2"
          >
            <FormControl
              v-model="link.platform"
              type="select"
              class="w-40"
              :options="platforms"
            />
            <FormControl
              v-model="link.url"
              type="text"
              class="flex-1"
              placeholder="https://"
            />
            <Button
              variant="ghost"
              icon="lucide-trash-2"
              @click="form.social_links.splice(index, 1)"
            />
          </div>
        </div>
      </section>

      <!-- ------------------------------------------------ seo -->
      <section class="flex flex-col gap-3">
        <h3 class="text-p-base-medium text-ink-gray-8">{{ __('SEO') }}</h3>
        <FormControl
          v-model="form.default_meta_title"
          type="text"
          :label="__('Default meta title')"
        />
        <FormControl
          v-model="form.default_meta_description"
          type="textarea"
          :rows="2"
          :label="__('Default meta description')"
        />
        <div class="flex items-start gap-6">
          <ImageField
            :label="__('Default sharing image')"
            :url="form.default_og_image"
            @update="(url) => (form.default_og_image = url)"
          />
          <div
            class="flex flex-1 items-center justify-between rounded-lg border border-outline-gray-2 px-3 py-2.5"
          >
            <div class="flex flex-col">
              <span class="text-p-base-medium text-ink-gray-8">
                {{ __('Allow search engines') }}
              </span>
              <span class="text-p-sm text-ink-gray-5">
                {{ __('Turn off while the site is still being built.') }}
              </span>
            </div>
            <Switch v-model="form.robots_indexable" size="sm" />
          </div>
        </div>
      </section>

      <!-- ------------------------------------------------ tracking -->
      <section class="flex flex-col gap-3 pb-6">
        <h3 class="text-p-base-medium text-ink-gray-8">
          {{ __('Tracking & consent') }}
        </h3>
        <p class="text-p-sm text-ink-gray-5">
          {{
            __(
              'Visits and form submissions already feed the CRM’s own lead attribution. These are the extra platform tags.',
            )
          }}
        </p>
        <div class="grid grid-cols-2 gap-3">
          <FormControl
            v-model="form.ga4_id"
            type="text"
            :label="__('GA4 measurement ID')"
            placeholder="G-XXXXXXX"
          />
          <FormControl
            v-model="form.meta_pixel_id"
            type="text"
            :label="__('Meta Pixel ID')"
          />
        </div>
        <div
          class="flex items-center justify-between rounded-lg border border-outline-gray-2 px-3 py-2.5"
        >
          <div class="flex flex-col">
            <span class="text-p-base-medium text-ink-gray-8">
              {{ __('Cookie banner') }}
            </span>
            <span class="text-p-sm text-ink-gray-5">
              {{
                __(
                  'Analytics and pixel tags only load after the visitor accepts.',
                )
              }}
            </span>
          </div>
          <Switch v-model="form.consent_banner" size="sm" />
        </div>
        <FormControl
          v-if="form.consent_banner"
          v-model="form.consent_text"
          type="textarea"
          :rows="2"
          :label="__('Banner text')"
        />
      </section>
    </div>
  </div>
</template>

<script setup>
import ImageField from '@/components/Settings/Website/ImageField.vue'
import { createResource, FormControl, Switch, call, toast } from 'frappe-ui'
import { ref, reactive, computed, onMounted } from 'vue'

const saving = ref(false)

const form = reactive({
  enabled: false,
  site_title: '',
  tagline: '',
  home_page: '',
  serve_at_root: false,
  logo: '',
  favicon: '',
  primary_color: '',
  font_family: '',
  nav_items: [],
  footer_text: '',
  company_name: '',
  vat_number: '',
  address: '',
  email: '',
  phone: '',
  whatsapp_number: '',
  social_links: [],
  privacy_route: '',
  terms_route: '',
  default_meta_title: '',
  default_meta_description: '',
  default_og_image: '',
  robots_indexable: true,
  ga4_id: '',
  meta_pixel_id: '',
  consent_banner: true,
  consent_text: '',
})

const linkTypes = [
  { label: __('Page'), value: 'Page' },
  { label: __('Service'), value: 'Service' },
  { label: __('External'), value: 'External' },
  { label: __('Anchor'), value: 'Anchor' },
]

const platforms = [
  'Facebook',
  'Instagram',
  'LinkedIn',
  'YouTube',
  'TikTok',
  'X',
  'WhatsApp',
].map((value) => ({ label: value, value }))

// Only published pages are offered: pointing the root at a draft would 404 the site.
const pages = createResource({ url: 'crm.api.site.list_pages', auto: false })

const homeOptions = computed(() => [
  { label: __('None'), value: '' },
  ...(pages.data || [])
    .filter((page) => page.published)
    .map((page) => ({
      label: `${page.page_title} — /${page.route}`,
      value: page.route,
    })),
])

onMounted(async () => {
  const data = await call('crm.api.site.get_settings')
  Object.keys(form).forEach((key) => {
    if (data[key] === undefined || data[key] === null) return
    if (Array.isArray(form[key]))
      form[key] = data[key].map((row) => ({ ...row }))
    else if (typeof form[key] === 'boolean') form[key] = Boolean(data[key])
    else form[key] = data[key]
  })
  if (data._builder_installed) pages.reload()
})

function addNavItem() {
  form.nav_items.push({
    label: '',
    link_type: 'Page',
    target: '',
    open_in_new: 0,
  })
}

function moveNavItem(index, delta) {
  const target = index + delta
  const [item] = form.nav_items.splice(index, 1)
  form.nav_items.splice(target, 0, item)
}

function addSocial() {
  form.social_links.push({ platform: 'Instagram', url: '' })
}

function targetHint(type) {
  if (type === 'Service') return __('service slug')
  if (type === 'External') return 'https://…'
  if (type === 'Anchor') return '#section'
  return __('page route')
}

async function save() {
  saving.value = true
  try {
    await call('crm.api.site.save_settings', { settings: { ...form } })
    toast.success(__('Saved'))
  } catch (error) {
    toast.error(error.messages?.[0] || __('Could not save the settings'))
  } finally {
    saving.value = false
  }
}
</script>
