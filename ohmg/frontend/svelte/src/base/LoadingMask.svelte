<script>
    import LoadingEllipsis from "./LoadingEllipsis.svelte";
</script>

<div class="loading-mask-container">
	<div class="loading-mask"></div>
	<div class="loading-ellipsis-container">
		<LoadingEllipsis />
	</div>
</div>

<style>
.loading-mask-container {
	position: fixed;
	height: 100vh;
	width: 100vw;
	z-index: 9998;
	bottom: 0;
	left: 0;
	right: 0;
	top: 0;
}

.loading-mask {
  /* position: fixed; */
  height: 100%;
  width: 100%; 
  background-color: #ffffff;
  opacity: 0.4;
}

.loading-ellipsis-container {
	position: fixed;
	top: 50vh;
	left: 50vw;
}
</style>