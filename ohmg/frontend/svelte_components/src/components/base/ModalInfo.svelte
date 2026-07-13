<script>
  import Modal, { closeModal } from './Modal.svelte';

  export let id;
  export let buttonText = "Ok"
  export let buttonAction = () => {};

</script>

<Modal id={id}>
  <slot>
    <p>Information here</p>
  </slot>
  {#if buttonText}
  <button
    class="button is-success"
    title={buttonText}
    on:click={() => {
      buttonAction();
      closeModal(id);
    }}>{buttonText}</button
  >
  {/if}
</Modal>
