<script>
  import Modal, { getModal } from './BaseModal.svelte';
  import { submitPostRequest } from '../../lib/requests';

  export let CONTEXT;
  export let bulkPrepareList;
  export let processing;
  export let callback = null;

  function postBulkNoSplit() {
    processing = true;
    submitPostRequest(
      `/split/`,
      CONTEXT.ohmg_post_headers,
      'bulk-no-split',
      {
        bulkNoSplitIds: bulkPrepareList,
      },
      callback,
    );
  }
</script>

<Modal id="modal-confirm-bulk-no-split">
  <p>
    Are you sure {bulkPrepareList.length > 1 ? `these ${bulkPrepareList.length} documents do` : 'this document does'} not
    need to be split?
  </p>
  <button
    class="button is-success"
    title="Confirm preparation"
    on:click={() => {
      postBulkNoSplit();
      getModal('modal-confirm-bulk-no-split').close();
    }}>Yes - {bulkPrepareList.length > 1 ? `each one only contains` : 'it only contains'} one map</button
  >
  <button
    class="button is-danger"
    title="Cancel preparation"
    on:click={() => {
      getModal('modal-confirm-bulk-no-split').close();
    }}>Cancel</button
  >
</Modal>
