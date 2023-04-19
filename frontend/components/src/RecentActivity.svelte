<script>
import {onMount} from 'svelte';

export let SESSION_API_URL;
export let OHMG_API_KEY;

let loadingSessions = false;
let recentSessions = [];

function getInitialResults() {
	loadingSessions = true;
	fetch(SESSION_API_URL+"?limit=15", {
		headers: {
			'X-API-Key': OHMG_API_KEY,
		}
	})
	.then(response => response.json())
	.then(result => {
		recentSessions = result.items;
		console.log(recentSessions[0])
		loadingSessions = false;
	});
}
getInitialResults()

// onMount(async function() {

// 	const response = await fetch(SESSION_API_URL+"?limit=20", {
// 		headers: {
// 			'X-API-Key': OHMG_API_KEY,
// 		},
//     }).then((r) => (recentSessions = r.json()))
// 	recentSessions = await response.json()
// 	console.log(recentSessions)
// });


</script>
<div>
	<h2>Recent Activity</h2>
	<div style="height: 300px; overflow-y:auto; border:1px solid grey; border-radius:4px; background:white;">
		{#if loadingSessions}
		<div class='lds-ellipsis'><div></div><div></div><div></div><div></div></div>
		{:else}
		{#each recentSessions as s}
		<div style="display:flex; padding: 10px 0px; border-bottom:1px dashed grey;">
			<div style="margin: 0px 15px;">
				{#if s.type === "p"}
				<a href="{s.doc.detail_url}" title="{s.doc.title}">
					<img style="max-height:50px; border: 1px solid grey;" src={s.doc.thumb_url} alt=""/>
				</a>
				{:else if s.type === "g" || s.type === "t"}
				<a href="{s.lyr.detail_url}" title="{s.lyr.title}">
					<img style="max-height:50px; border: 1px solid grey;" src={s.lyr.thumb_url} alt=""/>
				</a>
				{/if}
			</div>
			<div style="display:flex; flex-direction:column;">
				{#if s.type === "p"}
				<div>
					<a href="{s.doc.detail_url}" title="{s.doc.title}">{s.doc.title}</a>
				</div>
				<div>
					{s.date_created} &mdash; prepared by <a href="{s.user.profile_url}">{s.user.username}</a>
				</div>
				{:else if s.type === "g" || s.type === "t"}
				<div>
					<a href="{s.lyr.detail_url}" title="{s.lyr.title}">{s.lyr.title}</a>
				</div>
				<div>
					{s.date_created} &mdash; georeferenced by <a href="{s.user.profile_url}">{s.user.username}</a>
				</div>
				{/if}
			</div>
		</div>
		{/each}
		{/if}
	</div>
</div>
<style>

</style>
