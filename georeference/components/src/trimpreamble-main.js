import './css/interface.css';
import TrimPreamble from './TrimPreamble.svelte';

const app = new TrimPreamble({
	target: document.getElementById("trimpreamble-target"),
	props: JSON.parse(document.getElementById("trimpreamble-props").textContent),
});

export default app;
