<script>
	import ConditionalDoubleChevron from '../buttons/ConditionalDoubleChevron.svelte';
	import Link from '../common/Link.svelte';

	import SessionList from '../lists/SessionList.svelte'

	export let CONTEXT;
	export let PROFILE_USER;
	export let MAP_FILTER_LIST;

	let myProfile = CONTEXT.user.username === PROFILE_USER.username;

	let showSessions = true;

	const sessionFilterParam = `username=${PROFILE_USER.username}`

</script>

<main>
	{#if myProfile}
	<section>
		<div class="section-title-bar">
			<h2>My Account</h2>
		</div>
		<div class="section-content">
			<ul>
				<li><Link href="/account/password/change/" title="Change password">Change my password</Link></li>
				<li><Link href="{CONTEXT.change_avatar_url}" title="Change profile picture">Change my profile picture</Link></li>
				<li><Link href="/account/logout">Sign out</Link></li>
			</ul>
			{#if CONTEXT.user.api_keys.length > 0}
			<h4>Api Keys</h4>
			{#each CONTEXT.user.api_keys as key}
			<pre>{key}</pre>
			{/each}
			{/if}
		</div>
	</section>
	{/if}
	<section>
		<div class="section-title-bar">
			<button class="section-toggle-btn"
				on:click={() => {showSessions = !showSessions}}>
				<ConditionalDoubleChevron down={showSessions} size="md" />
				<h2 style="margin-right:10px">
					{#if myProfile}My {/if}Session History
				</h2>
			</button>
		</div>
		{#if showSessions}
		<SessionList {CONTEXT} {MAP_FILTER_LIST} showUser={false} userFilter={{id: PROFILE_USER.username}}/>
		{/if}
	</section>
</main>
<style>

main { 
	margin-bottom: 10px;
}

h2 {
	font-size: 1.6em;
}

section {
	border-bottom: 1px solid rgb(149, 149, 149);
}

button.section-toggle-btn {
	display: flex;
	justify-content: space-between;
	align-items: baseline;
	background: none;
	border: none;
	color: #2c689c;
	padding: 0;
}

button.section-toggle-btn {
	text-decoration: none;
}

button.section-toggle-btn:hover {
	color: #1b4060;
}

button.section-toggle-btn:disabled {
	color: grey;
}

@media screen and (max-width: 768px){
	main {
		max-width: none;
	}
}

</style>