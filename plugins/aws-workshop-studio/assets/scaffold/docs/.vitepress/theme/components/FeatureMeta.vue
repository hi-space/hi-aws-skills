<script setup lang="ts">
import { withBase } from 'vitepress'
import { useLocale } from '../i18n'

defineProps<{
  scenario?: string
  scenes?: string
  icon?: string
}>()

const { t } = useLocale()
</script>

<template>
  <div class="fmeta">
    <img v-if="icon" class="fmeta__icon" :src="withBase(`/images/icons/${icon}.svg`)" alt="" aria-hidden="true" />
    <span v-if="scenario" :class="['fmeta__badge', `fmeta__badge--${scenario.toLowerCase()}`]">
      {{ t('scenario') }} {{ scenario }}
    </span>
    <span v-if="scenes" class="fmeta__badge fmeta__badge--scene">{{ scenes }}</span>
  </div>
</template>
