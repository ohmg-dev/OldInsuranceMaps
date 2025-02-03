import '@/css/interface.css';
import Split from '@/components/Split.svelte';
import '@/css/ol-overrides.css'

const app = new Split({
	target: document.getElementById("split-target"),
	props: JSON.parse(document.getElementById("split-props").textContent),
});

export default app;
