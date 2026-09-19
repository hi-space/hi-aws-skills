<script setup lang="ts">
import { computed } from 'vue'
import { withBase } from 'vitepress'
import { allFeatures, taglineFor, type Feature } from '../../data/features'
import { useLocale } from '../i18n'

const props = defineProps<{ ids: string }>()
const { locale, localePrefix } = useLocale()

const list = computed<Feature[]>(() =>
  props.ids
    .split(',')
    .map((s) => s.trim())
    .map((id) => allFeatures.find((f) => f.id === id))
    .filter((f): f is Feature => Boolean(f))
)
</script>

<template>
  <div class="flinks">
    <a
      v-for="f in list"
      :key="f.id"
      class="flink"
      :href="withBase(`${localePrefix}/features/${f.id}`)"
    >
      <img class="flink__icon" :src="withBase(`/images/icons/${f.icon}.svg`)" alt="" aria-hidden="true" />
      <span class="flink__body">
        <span class="flink__title">{{ f.title }}</span>
        <span class="flink__tag">{{ taglineFor(f, locale) }}</span>
      </span>
      <span class="flink__arrow">→</span>
    </a>
  </div>
</template>
