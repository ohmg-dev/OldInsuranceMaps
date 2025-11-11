import MapBrowse from './components/interfaces/MapBrowse.svelte';

export default new MapBrowse({
  target: document.getElementById('mapbrowse-target'),
  props: JSON.parse(document.getElementById('mapbrowse-props').textContent),
});
