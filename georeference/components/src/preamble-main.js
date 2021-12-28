import './css/interface.css';
import Preamble from './Preamble.svelte';

const app = new Preamble({
	target: document.getElementById("preamble-target"),
	props: JSON.parse(document.getElementById("preamble-props").textContent),
});

export default app;
