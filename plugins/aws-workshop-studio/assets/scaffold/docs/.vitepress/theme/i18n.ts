import { computed } from 'vue'
import { useData } from 'vitepress'

export type Locale = 'ko' | 'en' | 'ja'

const dict = {
  screenshot: { ko: '스크린샷', en: 'Screenshot', ja: 'スクリーンショット' },
  screenshotMissing: {
    ko: '여기에 스크린샷을 추가하세요 →',
    en: 'Add a screenshot here →',
    ja: 'ここにスクリーンショットを追加してください →',
  },
  video: { ko: '영상', en: 'Video', ja: '動画' },
  videoMissing: {
    ko: '여기에 영상을 추가하세요 →',
    en: 'Add a video here →',
    ja: 'ここに動画を追加してください →',
  },
  download: { ko: '다운로드', en: 'Download', ja: 'ダウンロード' },
  checklistHint: {
    ko: '항목을 클릭해 체크 · 진행 상태는 이 브라우저에 저장됩니다',
    en: 'Click an item to check it off · progress is saved in this browser',
    ja: '項目をクリックしてチェック · 進行状況はこのブラウザに保存されます',
  },
  required: { ko: '필수', en: 'Required', ja: '必須' },
  optional: { ko: '선택', en: 'Optional', ja: '任意' },
  scenario: { ko: '시나리오', en: 'Scenario', ja: 'シナリオ' },
  seeMore: { ko: '자세히 보기', en: 'Learn more', ja: '詳しく見る' },
} as const

export type DictKey = keyof typeof dict

export function useLocale() {
  const { theme } = useData()
  const locale = computed<Locale>(() => (theme.value as any).locale || 'ko')
  const localePrefix = computed(() => (locale.value === 'ko' ? '' : `/${locale.value}`))
  function t(key: DictKey): string {
    return dict[key][locale.value]
  }
  return { locale, localePrefix, t }
}
