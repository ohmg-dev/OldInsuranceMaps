<script>
import SessionList from './components/SessionList.svelte'
import TitleBar from './components/TitleBar.svelte';


export let SESSION_API_URL;
export let OHMG_API_KEY;

</script>
<main>
	<TitleBar TITLE={"All activity"} />
	<SessionList OHMG_API_KEY={OHMG_API_KEY} SESSION_API_URL={SESSION_API_URL} limit={"25"} showThumbs={true}/>
</main>

<style>
main { 
	margin-bottom: 10px;
}

</style>
