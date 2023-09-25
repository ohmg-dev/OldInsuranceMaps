import Viewer from '../lib/Viewer.svelte';

const viewer = new Viewer({
	target: document.getElementById("viewer-target"),
	props: JSON.parse(document.getElementById("viewer-props").textContent),
});

export default viewer;