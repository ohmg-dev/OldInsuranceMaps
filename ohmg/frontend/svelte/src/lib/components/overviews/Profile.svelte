<script>
	import ConditionalDoubleChevron from './buttons/ConditionalDoubleChevron.svelte';
	import Link from '@components/base/Link.svelte';

	import SessionList from '@components/lists/SessionList.svelte'

	export let CURRENT_USERNAME;
	export let PROFILE_USER;
	export let CHANGE_AVATAR_URL;
	export let SESSION_API_URL;
	export let OHMG_API_KEY;
	export let USER_API_KEYS = [];

	let myProfile = CURRENT_USERNAME === PROFILE_USER.username;

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
				<li><Link href="{CHANGE_AVATAR_URL}" title="Change profile picture">Change my profile picture</Link></li>
				<li><Link href="/account/logout">Sign out</Link></li>
			</ul>
			{#if USER_API_KEYS.length > 0}
			<h4>Api Keys</h4>
			{#each USER_API_KEYS as key}
			<pre>key</pre>
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
		<SessionList OHMG_API_KEY={OHMG_API_KEY} SESSION_API_URL={SESSION_API_URL} FILTER_PARAM={sessionFilterParam} showUser={false}/>
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

button.section-toggle-btn, a {
	text-decoration: none;
}

button.section-toggle-btn:hover {
	color: #1b4060;
}

button.section-toggle-btn:disabled, button.section-toggle-btn:disabled > a {
	color: grey;
}

@media screen and (max-width: 768px){
	main {
		max-width: none;
	}
}

</style>