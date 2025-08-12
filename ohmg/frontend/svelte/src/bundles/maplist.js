import '../css/shared.css';
import '../css/interface.css';

import MapList from '../components/lists/MapList.svelte';
import '../css/ol-overrides.css';

const map = new MapList({
  target: document.getElementById('maplist-target'),
  props: JSON.parse(document.getElementById('maplist-props').textContent),
});

export default map;
