import '../../static/css/site_base.css';
import Volumes from './Volumes.svelte';

const volumes = new Volumes({
	target: document.getElementById("volumes-target"),
	props: JSON.parse(document.getElementById("volumes-props").textContent),
});

export default volumes;