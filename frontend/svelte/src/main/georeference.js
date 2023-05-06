import '../css/interface.css';
import '../js/ol-styles.js';
import '../js/ol-utils.js';
import Georeference from '../components/Georeference.svelte';
import '../css/ol-overrides.css'

const app = new Georeference({
	target: document.getElementById("georeference-target"),
	props: JSON.parse(document.getElementById("georeference-props").textContent),
});

export default app;
