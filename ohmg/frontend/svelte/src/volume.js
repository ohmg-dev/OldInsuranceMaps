import '@src/css/shared.css';
import '@src/css/interface.css';

import Volume from '@src/lib/Volume.svelte';
import '@src/css/ol-overrides.css'

const volume = new Volume({
	target: document.getElementById("volume-target"),
	props: JSON.parse(document.getElementById("volume-props").textContent),
});

export default volume;