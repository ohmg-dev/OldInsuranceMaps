<script>
    import Modal, {getModal} from '@/base/Modal.svelte';
    import { submitPostRequest } from "@lib/utils"

    export let CONTEXT;
    export let documentId;
    export let processing;
    export let callback = null;

    function postNoSplit() {
      processing = true
      submitPostRequest(
        `/document/${documentId}`,
        CONTEXT.ohmg_post_headers,
        "no-split",
        {},
        callback,
      )
    }
</script>

<Modal id="modal-confirm-no-split">
	<p>Are you sure this document does not need to be split?</p>
  <button class="button is-success"
    on:click={() => {
      postNoSplit();
      getModal('modal-confirm-no-split').close()
    }}>Yes - it only contains one map</button>
  <button class="button is-danger"
    on:click={() => {
      getModal('modal-confirm-no-split').close()}
    }>Cancel</button>
</Modal>