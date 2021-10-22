<script>
export let VOLUME;
</script>

<main>
	<div class="pane" style="test-align: left;">
		<h2>{VOLUME.title}</h2>
	</div>
</main>

<style>
	main {
		display: flex;
		flex-direction: row;
		color: black;
		font-size: 1.25em;
		padding: 1em;
		max-width: 240px;
		margin: 0 auto;
		/* background: #2c689c;
		background: #ffd78b; */

	}

	main a {
		color: #1647a4;
	}

	.pane {
		flex-grow: 1;
		width: 50%;
	}

	.pane + .pane {
		margin-left: 2%;
	}

	.select-menus {
		display: flex;
		flex-direction: column;
		align-items: center;
	}

	.select-item {
		width: 100%;
		margin-bottom: 20px;
	}

	h1, h2, h3 {
		/* color: #ff3e00; */
	}

	h1 {
		font-size: 4em;
		font-weight: 100;
		text-shadow: 2px 2px 2px rgba(0, 0, 0, 0.4);
	}

	h2, h3 {
		text-shadow: 1px 1px 1px rgba(0, 0, 0, 0.4);
	}

	@media (min-width: 640px) {
		main {
			max-width: none;
		}
	}

	select {
		color: rgb(59, 57, 57);
		width: 100%;
		height: 2em;
		font-size: 1.25em;
		font-weight: 700;
	}

	select:disabled {
		color: #acacac;
	}

	/* pure css loading bar */
	/* from https://loading.io/css/ */
	.lds-ellipsis {
		display: inline-block;
		position: relative;
		width: 80px;
		height: 80px;
	}
	.lds-ellipsis div {
		position: absolute;
		top: 33px;
		width: 13px;
		height: 13px;
		border-radius: 50%;
		background: #fff;
		animation-timing-function: cubic-bezier(0, 1, 1, 0);
	}
	.lds-ellipsis div:nth-child(1) {
		left: 8px;
		animation: lds-ellipsis1 0.6s infinite;
	}
	.lds-ellipsis div:nth-child(2) {
		left: 8px;
		animation: lds-ellipsis2 0.6s infinite;
	}
	.lds-ellipsis div:nth-child(3) {
		left: 32px;
		animation: lds-ellipsis2 0.6s infinite;
	}
	.lds-ellipsis div:nth-child(4) {
		left: 56px;
		animation: lds-ellipsis3 0.6s infinite;
	}
	@keyframes lds-ellipsis1 {
		0% {
			transform: scale(0);
		}
		100% {
			transform: scale(1);
		}
	}
	@keyframes lds-ellipsis3 {
		0% {
			transform: scale(1);
		}
		100% {
			transform: scale(0);
		}
		}
		@keyframes lds-ellipsis2 {
		0% {
			transform: translate(0, 0);
		}
		100% {
			transform: translate(24px, 0);
		}
	}
</style>