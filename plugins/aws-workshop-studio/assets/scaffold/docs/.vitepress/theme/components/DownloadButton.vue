<script setup lang="ts">
import { computed } from 'vue'
import { withBase, useData } from 'vitepress'
import { useLocale } from '../i18n'

const props = defineProps<{
  file?: string
  label?: string
  note?: string
}>()

const { theme } = useData()
const { t, locale } = useLocale()
// file이 명시되면 그걸, 아니면 빌드 시 로케일별로 주입된 최신 타임스탬프 ZIP을 사용
const href = computed(() => {
  if (props.file) return withBase(props.file)
  const zips = (theme.value as any).datasetZips || {}
  return withBase(zips[locale.value] || zips.ko || '/downloads/demo_datasets.zip')
})
</script>

<template>
  <a class="dl-btn" :href="href" download>
    <svg class="dl-btn__icon" viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <path d="M12 3v12m0 0l-4-4m4 4l4-4M4 20h16" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" />
    </svg>
    <span class="dl-btn__body">
      <span class="dl-btn__label">{{ label || t('download') }}</span>
      <span v-if="note" class="dl-btn__note">{{ note }}</span>
    </span>
  </a>
</template>
