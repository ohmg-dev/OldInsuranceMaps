<script>
    import Modal, {getModal} from './BaseModal.svelte';
    import { submitPostRequest } from '../../lib/requests';

    export let CONTEXT;
    export let sessionId;
    export let callback = null;

    function postExtendSession() {
      submitPostRequest(
        `/session/${sessionId}/`,
        CONTEXT.ohmg_post_headers,
        "extend",
        {},
        callback,
      )
    }
</script>

<Modal id="modal-extend-session">
  <p>This session is expiring, and you will be redirected back to the map overview page in a moment.</p>
  <button class="button is-success" on:click={() => {
    postExtendSession();
    getModal('modal-extend-session').close()}
    }>Give me more time!</button>
</Modal>