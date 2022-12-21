import './css/shared.css';
import Index from './Index.svelte';

const index = new Index({
	target: document.getElementById("index-target"),
	props: JSON.parse(document.getElementById("index-props").textContent),
});

export default index;