<script>
import SessionList from './components/SessionList.svelte'
import TitleBar from './components/TitleBar.svelte';


export let SESSION_API_URL;
export let OHMG_API_KEY;

const source = 'Work on this site is recorded as sessions, either preparation sessions (P) or georeference sessions (G). You can view information on each session below. More sophisticated filter and sort capabilities are in the works...'

</script>
<main>
	<!-- <MarkdownPage title={"All activity"} source={source} makeToc={false} /> -->
	<TitleBar TITLE={"All activity"} />
	<SessionList OHMG_API_KEY={OHMG_API_KEY} SESSION_API_URL={SESSION_API_URL} limit={"25"}/>
</main>

<style>
main { 
	margin-bottom: 10px;
}

</style>