import Trim from './Trim.svelte';

const app = new Trim({
	target: document.getElementById("trim-target"),
	props: JSON.parse(document.getElementById("trim-props").textContent),
});

export default app;
