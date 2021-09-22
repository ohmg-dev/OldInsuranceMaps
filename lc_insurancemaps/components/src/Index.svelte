<script>
export let STATE_CHOICES;

let currentState = "louisiana";
let cityOptions = [];
let currentCity;
let volumes = [];

$: {
	if (currentState == "louisiana") {
		cityOptions = ["Baton Rouge", "New Orleans"]
	} else {
		cityOptions = []
	}
}

</script>

<main>
	<h1>Hello!</h1>
	<p>Visit the <a href="https://svelte.dev/tutorial">Svelte tutorial</a> to learn how to build Svelte apps.</p>
	<select bind:value={currentState}>
	{#each STATE_CHOICES as state}
		<option value={state[0]} disabled={state[0] != "louisiana"}>{state[1]}</option>
		<!-- <option value={state[0]}>{state[1]}</option> -->
	{/each}
	</select>

	<select class="gcp-select" bind:value={currentCity}>
	{#each cityOptions as city}
		<option value={city}>{city}</option>
	{/each}
	</select>

	<ul>
	{#each volumes as volume}
		<li>volume</li>
	{/each}
	</ul>
</main>

<style>
	main {
		text-align: center;
		padding: 1em;
		max-width: 240px;
		margin: 0 auto;
	}

	h1 {
		color: #ff3e00;
		text-transform: uppercase;
		font-size: 4em;
		font-weight: 100;
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
		margin: 10px; 
	}
</style>