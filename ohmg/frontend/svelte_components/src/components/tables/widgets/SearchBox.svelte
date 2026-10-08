<script>
  import X from 'phosphor-svelte/lib/X';

  export let searchTerm;

  let timer;

  function handleInput(event) {
    const target = event.target;

    clearTimeout(timer);

    timer = setTimeout(() => {
      searchTerm = target.value;
    }, 300);
  }

  function handleClear(event) {
    document.getElementById('search-input').value = "";
    searchTerm = "";
  }

</script>

<div class="wrapper">
  <input id="search-input" type="text" placeholder="Search (full words)..." on:input={handleInput} />
  {#if searchTerm}
  <button on:click={handleClear}><X/></button>
  {/if}
</div>

<style>
  /* mimic the input style from svelte-select */
  input {
    border: 1px solid #d8dbdf;
    border-radius: 6px;
    min-height: 42px;
    padding: 0 0 0 16px;
    width: 175px;
  }

  input:hover {
    border: 1px solid #b2b8bf;
  }
  input:focus, input:focus-visible {
    border: 1px solid #2c689c;
  }

  .wrapper {
    position: relative;
    width: min-content;
    display: flex;
    align-items: center;
  }

  button {
    position: absolute;
    right: 5px;
    display: flex;
  }
</style>