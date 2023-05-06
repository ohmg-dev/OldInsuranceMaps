import '../css/shared.css';
import '../css/ol-overrides.css';
import Viewer from '../components/Viewer.svelte';

const viewer = new Viewer({
	target: document.getElementById("viewer-target"),
	props: JSON.parse(document.getElementById("viewer-props").textContent),
});

export default viewer;