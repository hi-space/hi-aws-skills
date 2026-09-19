import { defineConfig } from 'vitepress'
import container from 'markdown-it-container'
import { featuresA, featuresB } from './data/features'
import { readdirSync } from 'node:fs'
import { fileURLToPath } from 'node:url'
import { dirname, resolve } from 'node:path'

// ─────────────────────────────────────────────────────────────
// 이 골격은 기본으로 ko 단일 로케일만 활성화한다.
// en/ja 다국어가 필요하면: (1) STR 딕셔너리에 번역을 채우고
// (2) 아래 locales의 en/ja 블록 주석을 해제하면 makeThemeConfig 팩토리가
//    그대로 재사용된다(각 로케일 prefix만 다름).
// ─────────────────────────────────────────────────────────────

// 빌드 시 다운로드 폴더에서 로케일별 최신 demo_datasets*.zip(타임스탬프 파일명)을 찾아 링크에 사용.
// 폴더가 없으면 fallback을 반환하므로 골격 상태에서도 안전하다.
const __dir = dirname(fileURLToPath(import.meta.url))
function latestDatasetZips() {
  const fallback = { ko: '/downloads/demo_datasets.zip', en: '/downloads/demo_datasets_en.zip', ja: '/downloads/demo_datasets_ja.zip' }
  try {
    const dir = resolve(__dir, '../public/downloads')
    const files = readdirSync(dir)
    const pick = (re: RegExp, def: string) => {
      const matches = files.filter((f) => re.test(f)).sort()
      return matches.length ? `/downloads/${matches[matches.length - 1]}` : def
    }
    return {
      ko: pick(/^demo_datasets_(?!en_|ja_)\d+.*\.zip$/i, fallback.ko),
      en: pick(/^demo_datasets_en.*\.zip$/i, fallback.en),
      ja: pick(/^demo_datasets_ja.*\.zip$/i, fallback.ja),
    }
  } catch {
    return fallback
  }
}
const datasetZips = latestDatasetZips()

// 커스텀 콜아웃 컨테이너 (프롬프트 / 핵심 포인트)
function makeContainer(md: any, name: string, defaultTitle: string, icon: string) {
  md.use(container, name, {
    render(tokens: any[], idx: number) {
      const token = tokens[idx]
      const info = token.info.trim().slice(name.length).trim()
      if (token.nesting === 1) {
        const title = md.renderInline(info || defaultTitle)
        const lead = icon ? `${icon} ` : ''
        return `<div class="cb cb--${name}">\n<p class="cb__title">${lead}${title}</p>\n`
      }
      return `</div>\n`
    },
  })
}

const toItems = (arr: typeof featuresA, prefix: string) =>
  arr.map((f) => ({
    text: `${String(f.num).padStart(2, '0')}. ${f.title}`,
    link: `${prefix}/features/${f.id}`,
  }))

type L = 'ko' | 'en' | 'ja'

// 사이트 문구 딕셔너리. ko가 기본. en/ja는 다국어를 켤 때 채운다.
const STR: Record<string, Record<L, string>> = {
  siteTitle: { ko: '__SITE_TITLE__', en: '__SITE_TITLE__', ja: '__SITE_TITLE__' },
  description: { ko: '__SITE_DESCRIPTION__', en: '__SITE_DESCRIPTION__', ja: '__SITE_DESCRIPTION__' },
  home: { ko: '홈', en: 'Home', ja: 'ホーム' },
  gettingStarted: { ko: '시작하기', en: 'Getting Started', ja: 'はじめに' },
  scenarios: { ko: '시나리오', en: 'Scenarios', ja: 'シナリオ' },
  scenarioATitle: { ko: 'A · 예시 시나리오', en: 'A · Example Scenario', ja: 'A · サンプルシナリオ' },
  featureCatalog: { ko: '기능 카탈로그', en: 'Feature Catalog', ja: '機能カタログ' },
  appendix: { ko: '부록', en: 'Appendix', ja: '付録' },
  workshopOverview: { ko: '워크샵 개요', en: 'Workshop Overview', ja: 'ワークショップ概要' },
  demoSetup: { ko: '데모 사전 준비', en: 'Demo Setup', ja: 'デモ事前準備' },
  overview: { ko: '개요', en: 'Overview', ja: '概要' },
  aScene1: { ko: 'Scene 1 · 예시 장면', en: 'Scene 1 · Example', ja: 'Scene 1 · サンプル' },
  aScene2: { ko: 'Scene 2 · 예시 장면', en: 'Scene 2 · Example', ja: 'Scene 2 · サンプル' },
  fullIndex: { ko: '전체 인덱스', en: 'Full Index', ja: '全体インデックス' },
  featuresACount: { ko: '시나리오 A 기능', en: 'Scenario A Features', ja: 'シナリオA機能' },
  datasets: { ko: '데이터셋', en: 'Datasets', ja: 'データセット' },
  demoGuide: { ko: '데모 실행 가이드', en: 'Demo Run Guide', ja: 'デモ実行ガイド' },
  tips: { ko: '주목 포인트', en: 'Things to Notice', ja: '注目ポイント' },
  search: { ko: '검색', en: 'Search', ja: '検索' },
  showDetails: { ko: '상세 표시', en: 'Show details', ja: '詳細を表示' },
  resetSearch: { ko: '검색 초기화', en: 'Reset search', ja: '検索をリセット' },
  back: { ko: '뒤로', en: 'Back', ja: '戻る' },
  noResults: { ko: '검색 결과가 없습니다', en: 'No results found', ja: '検索結果がありません' },
  select: { ko: '선택', en: 'Select', ja: '選択' },
  navigate: { ko: '이동', en: 'Navigate', ja: '移動' },
  close: { ko: '닫기', en: 'Close', ja: '閉じる' },
  onThisPage: { ko: '이 페이지 내용', en: 'On this page', ja: 'このページの内容' },
  prev: { ko: '이전', en: 'Previous', ja: '前へ' },
  next: { ko: '다음', en: 'Next', ja: '次へ' },
  darkMode: { ko: '다크 모드', en: 'Dark Mode', ja: 'ダークモード' },
  toLight: { ko: '라이트 모드로 전환', en: 'Switch to light mode', ja: 'ライトモードに切り替え' },
  toDark: { ko: '다크 모드로 전환', en: 'Switch to dark mode', ja: 'ダークモードに切り替え' },
  menu: { ko: '메뉴', en: 'Menu', ja: 'メニュー' },
  toTop: { ko: '맨 위로', en: 'Back to top', ja: 'トップへ戻る' },
  lastUpdated: { ko: '마지막 수정', en: 'Last updated', ja: '最終更新' },
  footerCopy: { ko: '내부 인에이블먼트 자료', en: 'Internal enablement material', ja: '社内イネーブルメント資料' },
  promptTitle: { ko: '프롬프트', en: 'Prompt', ja: 'プロンプト' },
  talkTitle: { ko: '핵심 포인트', en: 'Key Points', ja: '重要ポイント' },
}
const s = (key: keyof typeof STR, locale: L) => STR[key][locale]

function makeThemeConfig(locale: L, prefix: string) {
  return {
    locale,
    datasetZips,
    logo: '/images/home/logo.png',
    siteTitle: s('siteTitle', locale),

    nav: [
      { text: s('home', locale), link: `${prefix}/` },
      { text: s('gettingStarted', locale), link: `${prefix}/start/overview` },
      { text: s('scenarioATitle', locale), link: `${prefix}/scenario-a/` },
      { text: s('featureCatalog', locale), link: `${prefix}/features/` },
      { text: s('appendix', locale), link: `${prefix}/reference/datasets` },
    ],

    sidebar: [
      {
        text: s('gettingStarted', locale),
        collapsed: false,
        items: [
          { text: s('workshopOverview', locale), link: `${prefix}/start/overview` },
          { text: s('demoSetup', locale), link: `${prefix}/start/setup` },
        ],
      },
      {
        text: s('scenarioATitle', locale),
        collapsed: false,
        items: [
          { text: s('overview', locale), link: `${prefix}/scenario-a/` },
          { text: s('aScene1', locale), link: `${prefix}/scenario-a/scene1` },
          { text: s('aScene2', locale), link: `${prefix}/scenario-a/scene2` },
        ],
      },
      {
        text: s('featureCatalog', locale),
        collapsed: false,
        items: [
          { text: s('fullIndex', locale), link: `${prefix}/features/` },
          {
            text: s('featuresACount', locale),
            collapsed: true,
            items: toItems(featuresA, prefix),
          },
        ],
      },
      {
        text: s('appendix', locale),
        collapsed: false,
        items: [
          { text: s('datasets', locale), link: `${prefix}/reference/datasets` },
          { text: s('demoGuide', locale), link: `${prefix}/reference/demo-guide` },
          { text: s('tips', locale), link: `${prefix}/reference/tips` },
        ],
      },
    ],

    search: {
      provider: 'local' as const,
      options: {
        translations: {
          button: { buttonText: s('search', locale), buttonAriaLabel: s('search', locale) },
          modal: {
            displayDetails: s('showDetails', locale),
            resetButtonTitle: s('resetSearch', locale),
            backButtonTitle: s('back', locale),
            noResultsText: s('noResults', locale),
            footer: {
              selectText: s('select', locale),
              navigateText: s('navigate', locale),
              closeText: s('close', locale),
            },
          },
        },
      },
    },

    outline: { label: s('onThisPage', locale), level: [2, 3] as [number, number] },
    docFooter: { prev: s('prev', locale), next: s('next', locale) },
    darkModeSwitchLabel: s('darkMode', locale),
    lightModeSwitchTitle: s('toLight', locale),
    darkModeSwitchTitle: s('toDark', locale),
    sidebarMenuLabel: s('menu', locale),
    returnToTopLabel: s('toTop', locale),
    lastUpdatedText: s('lastUpdated', locale),

    footer: {
      copyright: s('footerCopy', locale),
    },
  }
}

export default defineConfig({
  base: '/',
  lastUpdated: true,
  cleanUrls: true,
  ignoreDeadLinks: true,
  appearance: 'dark',

  markdown: {
    lineNumbers: false,
    config(md) {
      makeContainer(md, 'prompt', STR.promptTitle.ko, '')
      makeContainer(md, 'talk', STR.talkTitle.ko, '')
    },
  },

  head: [
    ['link', { rel: 'icon', type: 'image/png', href: '/images/home/logo.png' }],
    ['link', { rel: 'preconnect', href: 'https://cdn.jsdelivr.net' }],
    [
      'link',
      {
        rel: 'stylesheet',
        href: 'https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/static/pretendard.min.css',
      },
    ],
    ['meta', { name: 'theme-color', content: '__THEME_COLOR__' }],
  ],

  locales: {
    root: {
      label: '한국어',
      lang: 'ko-KR',
      title: s('siteTitle', 'ko'),
      description: s('description', 'ko'),
      themeConfig: makeThemeConfig('ko', ''),
    },
    // 다국어를 켤 때 아래 주석을 해제한다(STR 번역을 먼저 채울 것).
    // en: {
    //   label: 'English',
    //   lang: 'en-US',
    //   title: s('siteTitle', 'en'),
    //   description: s('description', 'en'),
    //   themeConfig: makeThemeConfig('en', '/en'),
    // },
    // ja: {
    //   label: '日本語',
    //   lang: 'ja-JP',
    //   title: s('siteTitle', 'ja'),
    //   description: s('description', 'ja'),
    //   themeConfig: makeThemeConfig('ja', '/ja'),
    // },
  },
})
