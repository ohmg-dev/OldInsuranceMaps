<script>
  import Modal, { closeModal } from './Modal.svelte';

  export let id;
  export let yesButtonText = "Yes"
  export let yesButtonEnabled = true;
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
    disabled={!yesButtonEnabled}
    on:click={() => {
      yesAction();
      closeModal(id);
    }}>{yesButtonText}</button
  >
  <button
    class="button is-danger"
    title={noButtonText}
    on:click={() => {
      noAction()
      closeModal(id);
    }}>{noButtonText}</button
  >
</Modal>
