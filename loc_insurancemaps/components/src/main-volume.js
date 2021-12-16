import './css/shared.css';
import Volume from './Volume.svelte';

const volume = new Volume({
	target: document.getElementById("volume-target"),
	props: JSON.parse(document.getElementById("volume-props").textContent),
});

export default volume;