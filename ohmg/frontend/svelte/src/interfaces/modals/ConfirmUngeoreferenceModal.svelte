<script>
    import Modal, {getModal} from '@/base/Modal.svelte';
    import { submitPostRequest } from "@lib/utils";

    export let CONTEXT;
    export let layerId;
    export let processing;
    export let callback = null;

    function postUngeoreference() {
      processing = true
      submitPostRequest(
        `/layer/${layerId}`,
        CONTEXT.ohmg_post_headers,
        "ungeoreference",
        {},
        callback,
      )
    }
</script>

<Modal id="modal-confirm-ungeoreference">
	<p>Are you sure you want to remove all georeferencing information for this layer? This operation cannot be reversed, and is only necessary if the preparation step for this document needs to be redone.</p>
  <p>If you only need to improve the ground control points for this layer, click <strong>edit georeferencing</strong>.</p>
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