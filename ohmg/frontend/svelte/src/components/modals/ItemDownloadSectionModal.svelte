<script>
  import Modal from './BaseModal.svelte';
  import HowToUseXyz from '../overviews/sections/HowToUseXYZ.svelte';

  export let id;
</script>

<Modal {id}>
  <h3>Download & Web Services</h3>
  <p>After multiple pages have been georeferenced and a multimask has been created, a single mosaic can be generated from all of this item's layers. Once created, the mosaic can be downloaded as a GeoTIFF, or integrated as a web service into any common GIS or web GIS software via the <strong>XYZ tiles URL</strong>.</p>
  <HowToUseXyz />
</Modal>
