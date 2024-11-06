<script>
    import Modal, {getModal} from '@components/base/Modal.svelte';
    import LoadingMask from '../../base/LoadingMask.svelte';
    import { makePostOptions } from "@lib/utils";

    export let CONTEXT;
    export let layerId;
    export let callback = null;

    let processing = false

    function postUngeoreference() {
        processing = true;
        const data = JSON.stringify({
            "operation": "ungeoreference",
            "payload": {},
        });
        const options = makePostOptions(CONTEXT.ohmg_post_headers, data)
        fetch(`/layer/${layerId}`, options)
        .then(response => response.json())
        .then(result => {
            processing = false;
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
<Modal id="modal-confirm-ungeoreference">
	<p>Are you sure you want to remove all georeferencing information for this layer? This operation cannot be reversed, and typically is only necessary if the preparation step for this document needs to be redone.</p>
  <p>Use "edit georferencing" if you only need to improve the ground control points for this layer.</p>
  <button class="button is-success"
    on:click={() => {
      postUngeoreference();
      getModal('modal-confirm-ungeoreference').close()
    }}>Yes</button>
  <button class="button is-danger"
    on:click={() => {
      getModal('modal-confirm-ungeoreference').close()}
    }>Cancel</button>
</Modal>