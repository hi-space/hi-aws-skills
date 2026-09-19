<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { withBase } from 'vitepress'
import { useLocale } from '../i18n'

const { t } = useLocale()

const props = defineProps<{
  src: string
  poster?: string
  caption?: string
  autoplay?: boolean
  loop?: boolean
}>()

const error = ref(false)
const videoEl = ref<HTMLVideoElement | null>(null)
const resolved = computed(() => withBase(props.src))
const posterResolved = computed(() => (props.poster ? withBase(props.poster) : undefined))

onMounted(() => {
  // autoplay는 브라우저 정책상 muted가 필수 (Vue의 :muted 바인딩 버그 회피용 DOM 직접 설정)
  if (videoEl.value && props.autoplay) videoEl.value.muted = true
})
</script>

<template>
  <figure class="shot">
    <video
      v-if="!error"
      ref="videoEl"
      :src="resolved"
      :poster="posterResolved"
      class="shot__img"
      style="display:block;background:#000"
      controls
      playsinline
      preload="metadata"
      :autoplay="autoplay"
      :loop="loop"
      @error="error = true"
    />
    <div v-else class="shot__ph" role="img" :aria-label="t('video')">
      <img class="shot__ph-icon" :src="withBase('/images/icons/analyze.svg')" alt="" aria-hidden="true" />
      <div class="shot__ph-title">{{ t('video') }}</div>
      <div class="shot__ph-hint">
        {{ t('videoMissing') }} <code>docs/public{{ src }}</code>
      </div>
    </div>
    <figcaption v-if="caption" class="shot__cap">{{ caption }}</figcaption>
  </figure>
</template>
