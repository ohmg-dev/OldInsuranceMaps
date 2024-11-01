<script>
    import Modal, {getModal} from '@components/base/Modal.svelte';
    import LoadingMask from '../../base/LoadingMask.svelte';
    import { makePostOptions } from "@lib/utils"

    export let CONTEXT;
    export let documentId;
    export let callback = null;

    let processing = false;

    function postNoSplit() {
      processing = true
      const data = JSON.stringify({
          "operation": "no-split",
          "payload": {},
      });
      const options = makePostOptions(CONTEXT.ohmg_post_headers, data)
      fetch(`/document/${documentId}`, options)
      .then(response => response.json())
      .then(result => {
          processing = false
          if (result.success) {
            if (callback) {callback()}
          } else {
              alert("Error: " + result.message)
          }
      });
    }

</script>

{#if processing}
<LoadingMask />
{/if}
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