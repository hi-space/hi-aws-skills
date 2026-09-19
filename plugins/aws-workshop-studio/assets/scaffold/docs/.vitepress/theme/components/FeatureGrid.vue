<script setup lang="ts">
import { computed } from 'vue'
import { withBase } from 'vitepress'
import { featuresA, featuresB, allFeatures, taglineFor, type Feature } from '../../data/features'
import { useLocale } from '../i18n'

const props = defineProps<{
  scenario?: 'A' | 'B' | 'all'
}>()
const { locale, localePrefix } = useLocale()

const list = computed<Feature[]>(() => {
  if (props.scenario === 'A') return featuresA
  if (props.scenario === 'B') return featuresB
  return allFeatures
})
</script>

<template>
  <div class="fgrid">
    <a
      v-for="f in list"
      :key="f.id"
      class="fcard"
      :href="withBase(`${localePrefix}/features/${f.id}`)"
    >
      <div class="fcard__top">
        <img class="fcard__icon" :src="withBase(`/images/icons/${f.icon}.svg`)" alt="" aria-hidden="true" />
        <span :class="['fcard__scn', `fcard__scn--${f.scenario.toLowerCase()}`]">{{ f.scenario }}</span>
      </div>
      <div class="fcard__num">{{ String(f.num).padStart(2, '0') }}</div>
      <h3 class="fcard__title">{{ f.title }}</h3>
      <p class="fcard__tag">{{ taglineFor(f, locale) }}</p>
      <div class="fcard__scenes">{{ f.scenes }}</div>
    </a>
  </div>
</template>
