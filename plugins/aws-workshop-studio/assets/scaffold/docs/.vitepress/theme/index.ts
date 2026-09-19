import DefaultTheme from 'vitepress/theme'
import type { Theme } from 'vitepress'
import { h } from 'vue'
import './custom.css'

import Screenshot from './components/Screenshot.vue'
import Video from './components/Video.vue'
import FeatureMeta from './components/FeatureMeta.vue'
import ScenarioCard from './components/ScenarioCard.vue'
import FeatureGrid from './components/FeatureGrid.vue'
import FeatureLinks from './components/FeatureLinks.vue'
import FlowMap from './components/FlowMap.vue'
import DownloadButton from './components/DownloadButton.vue'
import Checklist from './components/Checklist.vue'

export default {
  extends: DefaultTheme,
  // Attribution: every page carries the source of this workshop (layout-bottom shows on all pages,
  // unlike the default footer which only renders on pages without a sidebar). Do not remove.
  Layout() {
    return h(DefaultTheme.Layout, null, {
      'layout-bottom': () =>
        h('div', { class: 'built-with' }, [
          'Built with ',
          h(
            'a',
            { href: 'https://github.com/netsgo0319/workshop-scaffold', target: '_blank', rel: 'noreferrer' },
            'workshop-scaffold'
          ),
        ]),
    })
  },
  enhanceApp({ app }) {
    app.component('Screenshot', Screenshot)
    app.component('Video', Video)
    app.component('FeatureMeta', FeatureMeta)
    app.component('ScenarioCard', ScenarioCard)
    app.component('FeatureGrid', FeatureGrid)
    app.component('FeatureLinks', FeatureLinks)
    app.component('FlowMap', FlowMap)
    app.component('DownloadButton', DownloadButton)
    app.component('Checklist', Checklist)
  },
} satisfies Theme
