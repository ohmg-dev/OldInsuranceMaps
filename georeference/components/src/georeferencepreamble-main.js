import './css/interface.css';
import GeoreferencePreamble from './GeoreferencePreamble.svelte';

const app = new GeoreferencePreamble({
	target: document.getElementById("georeferencepreamble-target"),
	props: JSON.parse(document.getElementById("georeferencepreamble-props").textContent),
});

export default app;
