<script>
export let VOLUME;
export let POST_URL;
export let CSRFTOKEN;
export let USER_TYPE;

let pagesLoading = VOLUME.status == "initializing...";
// let loadedBy = VOLUME.loaded_by;

function initializeVolume() {
	postOperation("initialize")
	
}
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
		pagesLoading = VOLUME.status == "initializing...";
		// loadedBy = VOLUME.loaded_by;
		// force pagesLoading = true here because async operations may not
		// yet have changed the actual VOLUME status.
		if (operation == "initialize") { pagesLoading = true; }
	});
}
</script>

<main>
	<div class="title-bar">
		<h2>{VOLUME.title}</h2>
		<p><a href={VOLUME.loc_url} target="_blank">View in Library of Congress <i class="fa fa-external-link"></i></a></p>
	</div>
	<hr style="border-top-color:rgb(149, 149, 149);">
	{#if USER_TYPE == 'anonymous' }
	<div class="sign-in-reminder">
	<p><em>
		<a href="#" data-toggle="modal" data-target="#SigninModal" role="button" >sign in</a> or
		<a href="/account/register">sign up</a> to work on this volume
	</em></p>
	</div>
	{/if}
	<h3 style="">Georeferencing Overview <button id="refresh-button" title="refresh overview" on:click={refreshSummary}><i class="fa fa-refresh" /></button></h3>
	<div class="pages-status-bar">
		{#if VOLUME.loaded_by != "" && !pagesLoading}
			<p><em>pages loaded by <a href={VOLUME.loaded_by_url}>{VOLUME.loaded_by}</a></em></p>
		{/if}
		{#if VOLUME.items_ct == 0 && USER_TYPE != 'anonymous' && !pagesLoading}
			<!-- <p><em>no pages loaded</em></p> -->
			<button on:click={initializeVolume}>load pages</button>
		{/if}
		{#if pagesLoading}
			<p style="float:left;"><em>{VOLUME.items_ct}/{VOLUME.sheet_ct} page{#if VOLUME.sheet_ct != 1}s{/if} loaded...</em></p>
			<div class='lds-ellipsis' style="float:right;"><div></div><div></div><div></div><div></div></div>
		{/if}
	</div>
	<div class="documents-box">
		<h4>Unprepared ({VOLUME.items.unprepared.length})</h4>
		<div class="documents-column">
			{#each VOLUME.items.unprepared as document}
			<div class="document-item">
				<div><p>page {document.page_str}</p></div>
				<img src={document.urls.thumbnail} alt={document.title}>
				<div>
					<ul>
						{#if USER_TYPE != "anonymous"}
						<li><a href={document.urls.split} title="prepare this document">prepare &rarr;</a></li>
						{/if}
						<li><a href={document.urls.detail} title={document.title}>document detail &rarr;</a></li>
					</ul>
				</div>
			</div>
			{/each}
		</div>
		<h4>Prepared ({VOLUME.items.prepared.length})</h4>
		<div class="documents-column">
			{#each VOLUME.items.prepared as document}
			<div class="document-item">
				<div><p>page {document.page_str}</p></div>
				<img src={document.urls.thumbnail} alt={document.title}>
				<div>
					<ul>
						{#if USER_TYPE != "anonymous"}
						<li><a href={document.urls.georeference} title="georeference this document">georeference &rarr;</a></li>
						{/if}
						<li><a href={document.urls.detail} title={document.title}>document detail &rarr;</a></li>
					</ul>
				</div>
			</div>
			{/each}
		</div>
		<h4>Georeferenced ({VOLUME.items.layers.length})</h4>
		<div class="documents-column">
			{#each VOLUME.items.layers as layer}
			<div class="document-item">
				<div><p>page {layer.page_str}</p></div>
				<img src={layer.urls.thumbnail} alt={document.title}>
				<div>
					<ul>
						{#if USER_TYPE != "anonymous"}
						<li><a href={layer.urls.georeference} title="edit georeferencing">edit georeferencing &rarr;</a></li>
						<li><a href={layer.urls.trim} title="trim this layer">trim &rarr;</a></li>
						{/if}
						<li><a href={layer.urls.detail} title={layer.title}>layer detail &rarr;</a></li>
					</ul>
				</div>
			</div>
			{/each}
		</div>
	</div>
</main>



<style>

	.pages-status-bar {
		width: 100%;
		display: inline-block;
		vertical-align: middle;
		font-size: .9em;
	}

	.pages-status-bar p {
		margin: 0px;
	}

	.sign-in-reminder {
		background: #e6e6e6;
		text-align: center;
		padding: 5px;
		margin: 5px;
	}

	.sign-in-reminder p {
		margin: 0px;
	}

	.documents-box {		
	}

	.documents-column {
		display: flex;
		flex-direction: row;
		flex-wrap: wrap;
		gap: 20px;
	}

	.document-item {
		/* padding: 20px; */
		display: flex;
		flex-direction: column;
		justify-content: space-between;
		border: 1px solid gray;
		background: white;

	}

	.document-item img {
		margin: 15px;
		max-height: 200px;
		max-width: 200px;
	}

	.document-item div:first-child {
		text-align: center;
	}

	.document-item div:first-child, .document-item div:last-child {
		padding: 10px;
		background: #e6e6e6;
		width: 100%;
	}

	.document-item p, .document-item ul {
		margin: 0px;
	}

	.document-item ul {
		list-style-type: none;
		padding: 0;
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
		float: right;
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

	.rotate{
    -moz-transition: all 2s linear;
    -webkit-transition: all 2s linear;
    transition: all 2s linear;
}

.rotate.down{
    -ms-transform: rotate(180deg);
    -moz-transform: rotate(180deg);
    -webkit-transform: rotate(180deg);
    transform: rotate(180deg);
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
		height: 20px;
	}
	.lds-ellipsis div {
		position: absolute;
		top: 10px;
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