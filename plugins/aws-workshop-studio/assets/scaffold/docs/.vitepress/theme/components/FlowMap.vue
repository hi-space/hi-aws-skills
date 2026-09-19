<script setup lang="ts">
import { computed } from 'vue'
import { withBase } from 'vitepress'
import { flowA, flowB, labelFor, type FlowScene } from '../../data/flows'
import { useLocale } from '../i18n'

const props = defineProps<{ scenario: 'A' | 'B' }>()
const scenes = computed<FlowScene[]>(() => (props.scenario === 'A' ? flowA : flowB))
const { locale, localePrefix } = useLocale()
</script>

<template>
  <div class="flowmap">
    <div v-for="s in scenes" :key="s.scene" class="flowrow">
      <span class="flowrow__scene">{{ s.scene }}</span>
      <div class="flowrow__steps">
        <template v-for="(step, i) in s.steps" :key="step.label + i">
          <a
            v-if="step.id"
            class="flowchip flowchip--link"
            :href="withBase(`${localePrefix}/features/${step.id}`)"
          >{{ labelFor(step, locale) }}</a>
          <span v-else class="flowchip">{{ labelFor(step, locale) }}</span>
          <span v-if="i < s.steps.length - 1" class="flowarrow" aria-hidden="true">→</span>
        </template>
      </div>
    </div>
  </div>
</template>
