<script>
  import Modal, { getModal } from './BaseModal.svelte';
  import { submitPostRequest } from '../../lib/requests';

  export let CONTEXT;
  export let documentId;
  export let sessionId = null;
  export let processing;
  export let callback = null;

  function postNoSplit() {
    processing = true;
    submitPostRequest(
      `/split/${documentId}/`,
      CONTEXT.ohmg_post_headers,
      'no-split',
      {
        sessionId: sessionId,
      },
      callback,
    );
  }
</script>

<Modal id="modal-confirm-no-split">
  <p>Are you sure this document does not need to be split?</p>
  <button
    class="button is-success"
    title="Confirm no split needed"
    on:click={() => {
      postNoSplit();
      getModal('modal-confirm-no-split').close();
    }}>Yes - it only contains one map</button
  >
  <button
    class="button is-danger"
    title="Cancel preparation"
    on:click={() => {
      getModal('modal-confirm-no-split').close();
    }}>Cancel</button
  >
</Modal>
