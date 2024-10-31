<script>
    import Modal, {getModal} from '@components/base/Modal.svelte';
    import { makePostOptions } from "@lib/utils"

    export let CONTEXT;
    export let layerId;
    export let callback = null;

    function postUngeoreference() {
        const data = JSON.stringify({
            "operation": "ungeoreference",
            "payload": {},
        });
        const options = makePostOptions(CONTEXT.ohmg_post_headers, data)
        fetch(`/layer/${layerId}`, options)
        .then(response => response.json())
        .then(result => {
            if (result.success) {
              if (callback) {callback()}
            } else {
                alert("Error: " + result.message)
            }
        });
    }

</script>

<Modal id="modal-confirm-ungeoreference">
	<p>Are you sure you want to remove all georeferencing information for this layer? This operation cannot be reversed, and typically is only necessary if the preparation step for this document needs to be redone.</p>
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