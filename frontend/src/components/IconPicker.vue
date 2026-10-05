<!--
  Modifications copyright (c) 2026, NPM2 Solutions Srl
-->
<template>
  <Popover transition="default" @open="carica">
    <template #target="{ togglePopover, isOpen }">
      <slot v-bind="{ isOpen, togglePopover }">
        <span class="text-base"> {{ modelValue || '' }} </span>
      </slot>
    </template>
    <template #body="{ togglePopover }">
      <!--
        The six quick reactions, each a button the size of what it shows: they
        were 20px boxes round a 24px emoji, and on a phone a finger took the one
        beside it. Where nothing hovers each is 40px.
      -->
      <div
        v-if="reaction"
        class="flex items-center justify-center gap-1 rounded-full bg-surface-elevation-2 px-1.5 py-1 shadow-2xl ring-1 ring-black ring-opacity-5 focus:outline-none [@media(hover:none)]:gap-0.5 [@media(hover:none)]:p-1"
      >
        <button
          v-for="r in reactionEmojis"
          :key="r"
          class="grid size-8 place-items-center rounded-full text-2xl leading-none hover:bg-surface-gray-2 [@media(hover:none)]:size-10 [@media(hover:none)]:active:bg-surface-gray-3"
          @click="() => (emoji = r) && togglePopover()"
        >
          {{ r }}
        </button>
        <Button
          class="rounded-full [@media(hover:none)]:!size-10"
          icon="lucide-plus"
          :aria-label="__('More reactions')"
          @click.stop="() => (reaction = false)"
        />
      </div>
      <!--
        On a phone the whole picker is a sheet from the bottom (`data-foglio`,
        telefono.css), eight 40px columns across the screen (the style below):
        as a box of twelve columns it was 440px wide, off a 360px screen on both
        sides with its search field above the top.
      -->
      <div
        v-else
        class="tutte my-3 max-w-max transform bg-surface-base px-4 sm:px-0"
      >
        <div
          data-foglio
          class="relative max-h-96 pb-3 overflow-y-auto min-w-40 rounded-lg bg-surface-elevation-2 shadow-2xl ring-1 ring-black ring-opacity-5 focus:outline-none"
        >
          <div class="flex gap-2 px-3 pb-1 pt-3">
            <div class="flex-1">
              <FormControl
                v-model="search"
                type="text"
                :placeholder="__('Search by keyword')"
                :debounce="300"
              />
            </div>
            <Button @click="setRandom">{{ __('Random') }}</Button>
          </div>
          <div class="spazio w-96"></div>
          <div v-for="(emojis, group) in emojiGroups" :key="group" class="px-3">
            <div
              class="sticky top-0 bg-surface-elevation-2 pb-2 pt-3 text-sm text-ink-gray-7"
            >
              {{ nomeDelGruppo(group) }}
            </div>
            <div class="griglia grid w-96 grid-cols-12 place-items-center">
              <button
                v-for="_emoji in emojis"
                :key="_emoji.description"
                class="h-8 w-8 rounded-md p-1 text-3xl hover:bg-surface-gray-2 focus:outline-none focus:ring focus:ring-blue-200"
                :title="_emoji.nome"
                :aria-label="_emoji.nome"
                @click="() => (emoji = _emoji.emoji) && togglePopover()"
              >
                {{ _emoji.emoji }}
              </button>
            </div>
          </div>
        </div>
      </div>
    </template>
  </Popover>
</template>
<script setup>
import { caricaLeParole, paroleDi, testoDiRicerca, trova } from '@/utils/emoji'
import { Popover } from 'frappe-ui'
import { ref, computed, shallowRef } from 'vue'

// the emoji database (gemoji, 320 KB) comes when the picker opens: imported at
// the top, it was in the first download of every person's page, whose writing
// boxes carry this picker. With it, for a reader in Italian, the emoji's
// Italian words (Unicode's): «sorriso» or «grazie» find them as «smile» does,
// and each says its Italian name
const gemoji = shallowRef([])
let caricamento = null
function carica() {
  caricamento ||= Promise.all([import('gemoji'), caricaLeParole()]).then(
    ([modulo, parole]) => {
      gemoji.value = modulo.gemoji.map((voce) => ({
        ...voce,
        nome: paroleDi(parole, voce.emoji).nome || voce.description,
        cerca: testoDiRicerca(
          [voce.description, ...voce.names, ...voce.tags],
          parole,
          voce.emoji,
        ),
      }))
    },
  )
  return caricamento
}

const search = ref('')
const emoji = defineModel({ type: String, default: '' })
const reaction = defineModel('reaction', { type: Boolean })

const reactionEmojis = ref(['👍', '❤️', '😂', '😮', '😢', '🙏'])

// gemoji's groups, in the reader's language: they were drawn as gemoji names
// them, «Smileys & Emotion» on an Italian screen
function nomeDelGruppo(gruppo) {
  const nomi = {
    'Smileys & Emotion': __('Smileys & Emotion', null, 'Emoji group'),
    'People & Body': __('People & Body', null, 'Emoji group'),
    'Animals & Nature': __('Animals & Nature', null, 'Emoji group'),
    'Food & Drink': __('Food & Drink', null, 'Emoji group'),
    'Travel & Places': __('Travel & Places', null, 'Emoji group'),
    Activities: __('Activities', null, 'Emoji group'),
    Objects: __('Objects', null, 'Emoji group'),
    Symbols: __('Symbols', null, 'Emoji group'),
    Flags: __('Flags', null, 'Emoji group'),
    'No results': __('No results'),
  }
  return nomi[gruppo] || gruppo
}

const emojiGroups = computed(() => {
  let groups = {}
  for (let _emoji of gemoji.value) {
    if (!trova(_emoji.cerca, search.value)) continue

    let group = groups[_emoji.category]
    if (!group) {
      groups[_emoji.category] = []
      group = groups[_emoji.category]
    }
    group.push(_emoji)
  }
  // nothing yet while the emoji arrive: «No results» is for a search
  if (!Object.keys(groups).length && gemoji.value.length) {
    groups['No results'] = []
  }
  return groups
})

async function setRandom() {
  await carica()
  let total = gemoji.value.length
  let index = randomInt(0, total - 1)
  emoji.value = gemoji.value[index].emoji
}

function randomInt(min, max) {
  return Math.floor(Math.random() * (max - min + 1) + min)
}

defineExpose({ setRandom })
</script>

<style scoped>
@media (max-width: 767px), (max-height: 499px) and (pointer: coarse) {
  .tutte {
    max-width: none;
    margin: 0;
    padding: 0;
  }
  .tutte > [data-foglio] {
    border-radius: 1.25rem 1.25rem 0 0;
    box-shadow: none;
  }
  .spazio {
    display: none;
  }
  .griglia {
    width: 100%;
    grid-template-columns: repeat(8, minmax(0, 1fr));
  }
  .griglia > button {
    width: 2.5rem;
    height: 2.5rem;
  }
}
</style>
