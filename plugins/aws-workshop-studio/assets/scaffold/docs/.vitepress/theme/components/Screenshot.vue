<script setup lang="ts">
import { ref, computed } from 'vue'
import { withBase } from 'vitepress'
import { useLocale } from '../i18n'

const props = defineProps<{
  src: string
  alt?: string
  caption?: string
}>()

const { t } = useLocale()
const error = ref(false)
const resolved = computed(() => withBase(props.src))
const label = computed(() => props.alt || t('screenshot'))
</script>

<template>
  <figure class="shot">
    <img
      v-if="!error"
      :src="resolved"
      :alt="label"
      loading="lazy"
      decoding="async"
      class="shot__img"
      @error="error = true"
    />
    <div v-else class="shot__ph" role="img" :aria-label="label">
      <img class="shot__ph-icon" :src="withBase('/images/icons/analyze.svg')" alt="" aria-hidden="true" />
      <div class="shot__ph-title">{{ label }}</div>
      <div class="shot__ph-hint">
        {{ t('screenshotMissing') }} <code>docs/public{{ src }}</code>
      </div>
    </div>
    <figcaption v-if="caption" class="shot__cap">{{ caption }}</figcaption>
  </figure>
</template>
