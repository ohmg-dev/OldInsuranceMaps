import MapBrowse from './components/search/MapBrowse.svelte';

export default new MapBrowse({
  target: document.getElementById('mapbrowse-target'),
  props: JSON.parse(document.getElementById('mapbrowse-props').textContent),
});
