<script setup lang="ts">
import { withBase } from 'vitepress'
import { useLocale } from '../i18n'

const { t } = useLocale()

const props = defineProps<{
  title: string
  desc?: string
  link: string
  tag?: string
  icon?: string
  cta?: string
}>()
</script>

<template>
  <a class="scard" :href="withBase(link)">
    <img class="scard__icon" :src="withBase(`/images/icons/${props.icon || 'connect'}.svg`)" alt="" aria-hidden="true" />
    <div class="scard__body">
      <div v-if="tag" class="scard__tag">{{ tag }}</div>
      <h3 class="scard__title">{{ title }}</h3>
      <p v-if="desc" class="scard__desc">{{ desc }}</p>
      <span class="scard__cta">{{ cta || t('seeMore') }} →</span>
    </div>
  </a>
</template>
