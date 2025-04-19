<script>
  import Modal from './BaseModal.svelte';
  export let id;
</script>

<Modal {id}>
  <h3>Skipping "ungeoreferenceable" content</h3>
  <p>
    The <strong>Skipped</strong> section holds small map pieces that have limited geographic coverage and are exceedingly
    difficult, or impossible, to find control points for.
  </p>
  <p>
    In the future, improvements in the georeferencing interface may make it possible to place such items but in the
    meantime, this section allows these pieces to be removed from the overall process without being left behind.
  </p>
</Modal>
