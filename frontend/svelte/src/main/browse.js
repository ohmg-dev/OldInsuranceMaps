import '../css/shared.css';
import Browse from '../components/Browse.svelte';

const browse = new Browse({
	target: document.getElementById("browse-target"),
	props: JSON.parse(document.getElementById("browse-props").textContent),
});

export default browse;