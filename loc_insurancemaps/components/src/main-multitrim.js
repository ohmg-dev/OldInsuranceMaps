import './css/interface.css';
import './js/ol-styles.js';
import './js/ol-utils.js';
import MultiTrim from './MultiTrim.svelte';
import './css/ol-overrides.css'

const app = new MultiTrim({
	target: document.getElementById("multitrim-target"),
	props: JSON.parse(document.getElementById("multitrim-props").textContent),
});

export default app;
