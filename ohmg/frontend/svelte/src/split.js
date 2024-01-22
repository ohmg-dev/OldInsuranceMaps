import '@src/css/interface.css';
import Split from '@src/lib/pages/Split.svelte';
import '@src/css/ol-overrides.css'

const app = new Split({
	target: document.getElementById("split-target"),
	props: JSON.parse(document.getElementById("split-props").textContent),
});

export default app;
