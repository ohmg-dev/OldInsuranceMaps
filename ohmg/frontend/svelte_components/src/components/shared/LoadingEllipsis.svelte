<script>
  export let color = 'black';
  export let size = 'large';
  export let centered = true;
</script>

<div class="lds-ellipsis {size}{centered ? ' centered' : ''}">
  <div style:background={color}></div>
  <div style:background={color}></div>
  <div style:background={color}></div>
  <div style:background={color}></div>
</div>
