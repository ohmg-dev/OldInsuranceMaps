<script>
  import Modal, { getModal } from '../base/Modal.svelte';

  export let id;
  export let yesButtonText = "Yes"
  export let noButtonText = "No"
  export let yesAction = () => {};
  export let noAction = () => {};

</script>

<Modal id={id} closable={false}>
  <slot>
    <p>"Confirm this action?"</p>
  </slot>
  <button
    class="button is-success"
    title={yesButtonText}
    on:click={() => {
      yesAction();
      getModal(id).close();
    }}>{yesButtonText}</button
  >
  <button
    class="button is-danger"
    title={noButtonText}
    on:click={() => {
      noAction()
      getModal(id).close();
    }}>{noButtonText}</button
  >
</Modal>
