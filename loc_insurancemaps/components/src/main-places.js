import '../../static/css/site_base.css';
import './css/shared.css';
import Places from './Places.svelte';

const places = new Places({
	target: document.getElementById("places-target"),
	props: JSON.parse(document.getElementById("places-props").textContent),
});

export default places;