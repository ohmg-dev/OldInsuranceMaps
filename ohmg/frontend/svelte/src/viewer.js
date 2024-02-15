import PlaceViewer from '@components/interfaces/PlaceViewer.svelte';

const viewer = new PlaceViewer({
	target: document.getElementById("viewer-target"),
	props: JSON.parse(document.getElementById("viewer-props").textContent),
});

export default viewer;