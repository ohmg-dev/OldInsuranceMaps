import './css/interface.css';
import SplitPreamble from './SplitPreamble.svelte';

const app = new SplitPreamble({
	target: document.getElementById("splitpreamble-target"),
	props: JSON.parse(document.getElementById("splitpreamble-props").textContent),
});

export default app;
