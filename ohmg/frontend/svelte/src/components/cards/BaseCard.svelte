<div class="card-item">
  <div class="card-top">
    <slot name="card-top" />
  </div>
  <div class="card-middle">
    <slot name="card-middle" />
  </div>
  <div class="card-bottom">
    <slot name="card-bottom" />
  </div>
</div>

<style>
  .card-item {
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    border: 1px solid gray;
    background: white;
  }
  .card-top {
    text-align: center;
  }
  .card-middle {
    display: flex;
    flex-direction: column;
    justify-content: start;
    height: 100%;
  }
  .card-top,
  .card-bottom {
    padding: 10px;
    background: #e6e6e6;
    width: 100%;
  }
</style>
