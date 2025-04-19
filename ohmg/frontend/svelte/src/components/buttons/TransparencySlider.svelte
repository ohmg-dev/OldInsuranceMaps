<script>
  export let opacity;

  function getClass(n) {
    if (n == 100) {
      return 'full-circle';
    } else if (n == 0) {
      return 'empty-circle';
    } else {
      return 'half-circle';
    }
  }

  function toggleTransparency(inTrans) {
    let outTrans;
    if (inTrans == 100) {
      outTrans = 0;
    } else if (inTrans == 0) {
      outTrans = 50;
    } else {
      outTrans = 100;
    }
    return outTrans;
  }
</script>

<div style="display:flex; align-items:center;">
  <input class="slider" type="range" bind:value={opacity} min="0" max="100" />
  <button
    title="Toggle transparency"
    class="transparency-toggle"
    on:click={() => {
      opacity = toggleTransparency(opacity);
    }}
  >
    <i class={getClass(opacity)} />
  </button>
</div>
