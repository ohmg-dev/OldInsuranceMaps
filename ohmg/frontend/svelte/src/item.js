import '@src/css/shared.css';
import '@src/css/interface.css';

import Item from '@src/lib/components/overviews/Item.svelte';
import '@src/css/ol-overrides.css'

const item = new Item({
	target: document.getElementById("item-target"),
	props: JSON.parse(document.getElementById("item-props").textContent),
});

export default item;