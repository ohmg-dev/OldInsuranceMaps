import Overview from './Overview.svelte';

const app = new Overview({
	target: document.getElementById("overview-target"),
	props: JSON.parse(document.getElementById("overview-props").textContent),
});

export default app;
