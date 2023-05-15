import '../css/shared.css';
import '../css/interface.css';

import Volume from './Volume.svelte';
import '../css/ol-overrides.css'

const volume = new Volume({
	target: document.getElementById("volume-target"),
	props: JSON.parse(document.getElementById("volume-props").textContent),
});

export default volume;