<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useLocale } from '../i18n'

type Item = string | { text: string; tag?: string }
const props = defineProps<{ items: Item[]; id?: string }>()
const { t } = useLocale()
const REQUIRED_TAGS = new Set(['필수', 'Required', '必須'])
const norm = computed(() =>
  props.items.map((it) => (typeof it === 'string' ? { text: it, tag: undefined } : it))
)
const storeKey = 'ws-checklist:' + (props.id || 'default')
const checked = ref<boolean[]>(props.items.map(() => false))
const doneCount = computed(() => checked.value.filter(Boolean).length)

onMounted(() => {
  try {
    const s = localStorage.getItem(storeKey)
    if (s) {
      const arr = JSON.parse(s)
      checked.value = props.items.map((_, i) => !!arr[i])
    }
  } catch {}
})

function toggle(i: number) {
  checked.value[i] = !checked.value[i]
  try {
    localStorage.setItem(storeKey, JSON.stringify(checked.value))
  } catch {}
}
</script>

<template>
  <div class="chk">
    <div class="chk__bar">
      <span class="chk__count">{{ doneCount }} / {{ norm.length }}</span>
      <span class="chk__hint">{{ t('checklistHint') }}</span>
    </div>
    <ul class="chk__list">
      <li
        v-for="(it, i) in norm"
        :key="i"
        :class="['chk__item', { 'is-done': checked[i] }]"
        role="checkbox"
        :aria-checked="checked[i]"
        tabindex="0"
        @click="toggle(i)"
        @keydown.enter.prevent="toggle(i)"
        @keydown.space.prevent="toggle(i)"
      >
        <span class="chk__box" aria-hidden="true"></span>
        <span class="chk__text">{{ it.text }}</span>
        <span
          v-if="it.tag"
          :class="['chk__tag', REQUIRED_TAGS.has(it.tag || '') ? 'chk__tag--req' : 'chk__tag--opt']"
          >{{ it.tag }}</span
        >
      </li>
    </ul>
  </div>
</template>
