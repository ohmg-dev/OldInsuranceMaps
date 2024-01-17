import '@src/css/interface.css';
import Resource from '@src/lib/Resource.svelte';

const app = new Resource({
	target: document.getElementById("resource-target"),
	props: JSON.parse(document.getElementById("resource-props").textContent),
});

export default app;
