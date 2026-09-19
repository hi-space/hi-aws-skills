// ─────────────────────────────────────────────────────────────
// 기능 메타데이터 — 단일 출처 (config 사이드바 + FeatureGrid 공유)
// icon: /images/icons/<key>.svg 에 대응하는 아이콘 키
// title은 앱 UI 명칭이면 로케일 공통으로 두기도 함
// tagline만 로케일별로 분리(ko 기본 + en/ja)
//
// ▼ 골격 예시: 시나리오 A에 기능 2개만 넣어 두었다. 실제 워크샵에서는
//   이 배열을 청사진(blueprint)의 기능 목록으로 교체한다.
// ─────────────────────────────────────────────────────────────
export interface Feature {
  id: string // 페이지 slug (예: a-01-example)
  num: number
  title: string
  scenario: 'A' | 'B'
  scenes: string
  icon: string // 아이콘 키 (docs/public/images/icons/<icon>.svg)
  tagline: string
  taglineEn: string
  taglineJa: string
  img: string // 스크린샷 경로 (docs/public 기준)
}

export const featuresA: Feature[] = [
  {
    id: 'a-01-example',
    num: 1,
    title: 'Example Feature One',
    scenario: 'A',
    scenes: 'Scene 1',
    icon: 'notify',
    tagline: '첫 번째 예시 기능 — 이 자리에 한 줄 설명이 들어갑니다',
    taglineEn: 'First example feature — a one-line description goes here',
    taglineJa: '最初のサンプル機能 — ここに一行の説明が入ります',
    img: '/images/scenario_a/01_example.png',
  },
  {
    id: 'a-02-example',
    num: 2,
    title: 'Example Feature Two',
    scenario: 'A',
    scenes: 'Scene 2',
    icon: 'analyze',
    tagline: '두 번째 예시 기능 — 분석·시각화 계열의 예시',
    taglineEn: 'Second example feature — an analysis/visualization example',
    taglineJa: '2番目のサンプル機能 — 分析・可視化系の例',
    img: '/images/scenario_a/02_example.png',
  },
]

export const featuresB: Feature[] = []

export const allFeatures: Feature[] = [...featuresA, ...featuresB]

export function taglineFor(f: Feature, locale: string): string {
  if (locale === 'en') return f.taglineEn
  if (locale === 'ja') return f.taglineJa
  return f.tagline
}
