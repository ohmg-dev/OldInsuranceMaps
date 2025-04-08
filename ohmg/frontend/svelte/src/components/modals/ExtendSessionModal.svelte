<script>
  import Modal, { getModal } from './BaseModal.svelte';
  import { submitPostRequest } from '../../lib/requests';

  export let CONTEXT;
  export let sessionId;
  export let callback = null;
  export let countdown;

  function postExtendSession() {
    submitPostRequest(`/session/${sessionId}/`, CONTEXT.ohmg_post_headers, 'extend', {}, callback);
  }
</script>

<Modal id="modal-extend-session" closable={false}>
  <p>This session is expiring, and you will be redirected back to the map overview page.</p>
  <div style="display:flex; align-items:center;">
    <button
      class="button is-success"
      on:click={() => {
        postExtendSession();
        getModal('modal-extend-session').close();
      }}>Give me more time!</button
    >
    <span style="margin-left: 10px;"><em>Redirecting in {countdown}...</em></span>
  </div>
</Modal>
