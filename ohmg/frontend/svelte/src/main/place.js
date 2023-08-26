import '../../../static/css/site_base.css';
import '../css/shared.css';
import Place from './Place.svelte';

const place = new Place({
	target: document.getElementById("place-target"),
	props: JSON.parse(document.getElementById("place-props").textContent),
});

export default place;