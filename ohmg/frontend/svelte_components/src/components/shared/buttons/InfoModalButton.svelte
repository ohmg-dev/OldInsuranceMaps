<script>
  import Question from 'phosphor-svelte/lib/Question';

  import { openModal } from '../../base/Modal.svelte';

  export let modalId;
  export let size = '1em';
  export let title = 'More information';
</script>

<button
  {title}
  class="is-icon-link"
  on:click={() => {
    openModal(modalId);
  }}
  ><Question {size} />
</button>
