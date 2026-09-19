// ─────────────────────────────────────────────────────────────
// 시나리오별 기능 연결 흐름 (장면 → 기능 순서)
// id가 있으면 해당 기능 페이지로 링크되는 칩으로 렌더
// label은 대부분 기능명이라 로케일 공통. 한글 라벨만 labelEn/labelJa로 오버라이드.
//
// ▼ 골격 예시: 시나리오 A에 2개 씬, 각 씬에 예시 기능 1개씩 매핑.
//   flowB는 빈 배열 — 시나리오 B를 쓸 때 채운다.
// ─────────────────────────────────────────────────────────────
export interface FlowStep {
  label: string
  labelEn?: string
  labelJa?: string
  id?: string
}
export interface FlowScene {
  scene: string
  steps: FlowStep[]
}

export const flowA: FlowScene[] = [
  { scene: 'Scene 1', steps: [
    { label: 'Example Feature One', id: 'a-01-example' },
  ] },
  { scene: 'Scene 2', steps: [
    { label: 'Example Feature Two', id: 'a-02-example' },
  ] },
]

export const flowB: FlowScene[] = []

export function labelFor(step: FlowStep, locale: string): string {
  if (locale === 'en' && step.labelEn) return step.labelEn
  if (locale === 'ja' && step.labelJa) return step.labelJa
  return step.label
}
