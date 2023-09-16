import Index from '../lib/Index.svelte';

const app = new Index({
	target: document.getElementById("index-target"),
	props: JSON.parse(document.getElementById("index-props").textContent),
});

export default app;