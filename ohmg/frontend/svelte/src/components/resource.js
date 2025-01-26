import '@/css/interface.css';
import Resource from './Resource.svelte';

const app = new Resource({
	target: document.getElementById("resource-target"),
	props: JSON.parse(document.getElementById("resource-props").textContent),
});

export default app;
