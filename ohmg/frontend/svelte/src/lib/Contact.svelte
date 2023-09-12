<script>
import MarkdownPage from './components/MarkdownPage.svelte'

const source = `
<br>

Questions, concerns, or feedback: [hello@oldinsurancemaps.net](mailto:hello@oldinsurancemaps.net)

Bugs and technical discussion: [mradamcox/ohmg](https://github.com/mradamcox/ohmg)
`

</script>

<MarkdownPage source={source} title={"Contact"} makeToc={false}/>
