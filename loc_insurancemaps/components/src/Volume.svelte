<script>
export let VOLUME;
export let POST_URL;
export let CSRFTOKEN;

function initializeVolume() { postOperation("initialize") }
function refreshSummary() { postOperation("refresh") }

function postOperation(operation) {
	const data = JSON.stringify({
      "operation": operation,
    });
	fetch(POST_URL, {
		method: 'POST',
		headers: {
          'Content-Type': 'application/json;charset=utf-8',
          'X-CSRFToken': CSRFTOKEN,
        },
		body: data,
	})
	.then(response => response.json())
	.then(result => {
		VOLUME = result;
	});
}
</script>

<main>
	<div class="title-bar"><h2>{VOLUME.title}</h2><hr style="border-top-color:rgb(149, 149, 149);"></div>
	<h3 style="display:inline">Summary of Progress</h3>
	{#if VOLUME.status == "initializing..." || VOLUME.status == "started"}
	<button id="refresh-button" title="refresh summary" on:click={refreshSummary}><em>refresh</em> <i class="fa fa-refresh" /></button>
	{/if}
	{#if VOLUME.status == "not started"}
	<p>Work on this volume has not yet begun. Load the volume to get started!</p>
	<button on:click={initializeVolume}>Load Volume</button>
	{/if}
	{#if VOLUME.status == "initializing..."}
	<p>{VOLUME.items_ct}/{VOLUME.sheet_ct} sheet{#if VOLUME.sheet_ct != 1}s{/if} loaded...</p>
	<div class='lds-ellipsis'><div></div><div></div><div></div><div></div></div>
	{/if}
	
	{#if VOLUME.status == "started"}
	<div class="documents-box">
		{#if VOLUME.items.unprepared.length > 0}
		<h4>Unprepared ({VOLUME.items.unprepared.length})</h4>
		<div class="documents-column">
			{#each VOLUME.items.unprepared as document}
			<div class="document-item">
				<p>
					<a href={document.urls.detail} title={document.title}>detail page &rarr;</a><br>
					<a href={document.urls.split} title="prepare this document">prepare &rarr;</a>
				</p>
				<img src={document.urls.thumbnail} alt={document.title}>
			</div>
			{/each}
		</div>
		{/if}
		{#if VOLUME.items.prepared.length > 0}
		<h4>Prepared ({VOLUME.items.prepared.length})</h4>
		<div class="documents-column">
			{#each VOLUME.items.prepared as document}
			<div class="document-item">
				<p>
					<a href={document.urls.detail} title={document.title}>detail page &rarr;</a><br>
					<a href={document.urls.georeference} title="georeference this document">georeference &rarr;</a>
				</p>
				<img src={document.urls.thumbnail} alt={document.title}>
			</div>
			{/each}
		</div>
		{/if}
		{#if VOLUME.items.layers.length > 0}
		<h4>Georeferenced ({VOLUME.items.layers.length})</h4>
		<div class="documents-column">
			{#each VOLUME.items.layers as layer}
			<div class="document-item">
				<p>
					<a href={layer.urls.detail} title={layer.title}>detail page &rarr;</a><br>
					<a href={layer.urls.georeference} title="edit georeferencing">edit georeferencing &rarr;</a><br>
					<a href={layer.urls.trim} title="trim this layer">trim &rarr;</a>
				</p>
				<img src={layer.urls.thumbnail} alt={layer.title}>
			</div>
			{/each}
		</div>
		{/if}
	</div>
	{/if}
</main>



<style>
	main {
		font-size: 1.25em;
		padding: 1em;
		/* background: #2c689c;
		background: #ffd78b; */
	}

	.documents-box {
		
	}

	.documents-column {
		display: flex;
		flex-direction: row;
		gap: 20px;
	}

	.document-item {
		padding: 20px;
		border: 1px solid gray;
		background: white;
	}

	.document-item img {
		max-height: 200px;
		max-width: 200px;
	}

	.pane {
		flex-grow: 1;
		/* width: 33%; */
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

	#refresh-button {
		background: unset;
		border: none;
	}

	#refresh-button i {
		font-size: .75em;
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

	@media screen and (max-width: 768px){

		main {
			max-width: none;
		}

		.documents-column {
			flex-direction: column;
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
		background: #000;
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