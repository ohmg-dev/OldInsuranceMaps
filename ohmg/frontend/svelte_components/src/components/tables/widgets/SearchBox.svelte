<script>
  import X from 'phosphor-svelte/lib/X';
  import Spinner from 'phosphor-svelte/lib/Spinner';

  export let searchTerm;
  export let placeholder = "Search..."
  export let searching = false;

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
  <input id="search-input" type="text" {placeholder} on:input={handleInput} />
  <div class="icon-wrapper">
    {#if searching}
    <span class="spinner">
      <Spinner weight={'bold'}/>
    </span>
    {:else if searchTerm}
    <button on:click={handleClear}><X weight={'bold'}/></button>
    {/if}
  </div>
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

  span.spinner, button {
    display: flex;
    height: 1.25em;
  }

  .icon-wrapper {
    display: flex;
    align-items: center;
    height: 100%;
    position: absolute;
    right: 5px;
  }

  @-webkit-keyframes rotating /* Safari and Chrome */ {
    from {
      -webkit-transform: rotate(0deg);
      -o-transform: rotate(0deg);
      transform: rotate(0deg);
    }
    to {
      -webkit-transform: rotate(360deg);
      -o-transform: rotate(360deg);
      transform: rotate(360deg);
    }
  }
  @keyframes rotating {
    from {
      -ms-transform: rotate(0deg);
      -moz-transform: rotate(0deg);
      -webkit-transform: rotate(0deg);
      -o-transform: rotate(0deg);
      transform: rotate(0deg);
    }
    to {
      -ms-transform: rotate(360deg);
      -moz-transform: rotate(360deg);
      -webkit-transform: rotate(360deg);
      -o-transform: rotate(360deg);
      transform: rotate(360deg);
    }
  }
  .spinner {
    -webkit-animation: rotating 2s linear infinite;
    -moz-animation: rotating 2s linear infinite;
    -ms-animation: rotating 2s linear infinite;
    -o-animation: rotating 2s linear infinite;
    animation: rotating 2s linear infinite;
  }
</style>