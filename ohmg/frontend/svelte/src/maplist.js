import MapList from './components/lists/MapList.svelte';

export default new MapList({
  target: document.getElementById('maplist-target'),
  props: JSON.parse(document.getElementById('maplist-props').textContent),
});
