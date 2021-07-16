import Georeference from './Georeference.svelte';

const app = new Georeference({
	target: document.getElementById("georeference-target"),
	props: JSON.parse(document.getElementById("georeference-props").textContent),
});

export default app;
