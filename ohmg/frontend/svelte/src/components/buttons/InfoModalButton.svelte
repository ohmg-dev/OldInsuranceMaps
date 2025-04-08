<script>
  import Question from 'phosphor-svelte/lib/Question';

  import { getModal } from '../modals/BaseModal.svelte';

  export let modalId;
  export let size = '1em';
  export let title = 'More information';
</script>

<button
  {title}
  class="is-icon-link"
  on:click={() => {
    getModal(modalId).open();
  }}
  ><Question {size} />
</button>
