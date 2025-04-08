<script>
  import Modal from './BaseModal.svelte';
  export let id;
</script>

<Modal {id}>
  <h3>Georeferenced</h3>
  <p>
    The <strong>Georeferenced</strong> section holds all content that has been spatially rectified, though you can still
    edit the control points for any layer whose georeferencing should be improved.
  </p>
  <p>
    Use the <strong>Classify Layers</strong> button to sort layers into different categories, if applicable. For example,
    if a Key Map is present, classify it here so other interfaces will treat it appropriately.
  </p>
</Modal>
