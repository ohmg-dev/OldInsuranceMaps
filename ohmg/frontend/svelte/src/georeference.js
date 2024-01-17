import '@src/css/interface.css';
import Georeference from '@src/lib/Georeference.svelte';
import '@src/css/ol-overrides.css'

const app = new Georeference({
	target: document.getElementById("georeference-target"),
	props: JSON.parse(document.getElementById("georeference-props").textContent),
});

export default app;
