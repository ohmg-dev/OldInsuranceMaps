import '../../static/css/site_base.css';
import './css/shared.css';
import VolumeSearch from './VolumeSearch.svelte';

const volumes = new VolumeSearch({
	target: document.getElementById("volumesearch-target"),
	props: JSON.parse(document.getElementById("volumesearch-props").textContent),
});

export default volumes;