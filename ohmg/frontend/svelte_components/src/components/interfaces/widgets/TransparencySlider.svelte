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

<style>
  button.transparency-toggle {
    display: flex;
    border: none;
    background: none;
  }
  button.transparency-toggle > i {
    display: inline-block;
    cursor: pointer;
    color: #2c689c;
  }
  button.transparency-toggle:hover > i {
    color: #1b4060;
  }

  .full-circle {
    background: #2c689c;
    height: 15px;
    width: 15px;
    border: solid #2c689c 3px;
    border-radius: 15px;
  }
  .full-circle:hover {
    background: #1b4060;
    border-color: #1b4060;
  }
  .half-circle {
    background: linear-gradient(to right, #2c689c 0%, #2c689c 50%, white 50%, white 100%);
    height: 15px;
    width: 15px;
    border: solid #2c689c 3px;
    border-radius: 15px;
  }
  .half-circle:hover {
    background: linear-gradient(to right, #1b4060 0%, #1b4060 50%, white 50%, white 100%);
    border-color: #1b4060;
  }
  .empty-circle {
    background: white;
    height: 15px;
    width: 15px;
    border: solid #2c689c 3px;
    border-radius: 15px;
  }
  .empty-circle {
    border-color: #1b4060;
  }
</style>
