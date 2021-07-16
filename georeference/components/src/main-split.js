import Split from './Split.svelte';

const app = new Split({
	target: document.getElementById("split-target"),
	props: JSON.parse(document.getElementById("split-props").textContent),
});

export default app;
