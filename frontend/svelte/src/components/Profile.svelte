<script>
import {TableSort} from 'svelte-tablesort';
import TitleBar from './TitleBar.svelte';

export let CURRENT_USERNAME;
export let PROFILE_USER;
export let CHANGE_AVATAR_URL;
export let SESSION_API_URL;
export let OHMG_API_KEY;

let myProfile = CURRENT_USERNAME === PROFILE_USER.username;

let sessions = [];
let sessions_next_url;
let sessions_previous_url;
let loadingSessions = false;
let showSessions = true;
let showSummary = false;

let currentOffset = 0;
let sessionTotal = 0
let apiLimit = 25

let urlBaseSessions = SESSION_API_URL + `?username=${PROFILE_USER.username}&limit=${apiLimit}`

const apiHeaders = {
	"X-API-Key": OHMG_API_KEY,
}

function getInitialResults() {
	loadingSessions = true;
	fetch(urlBaseSessions + `&offset=${currentOffset}`, { headers: apiHeaders })
		.then(response => response.json())
		.then(result => {
			sessions = result.items;
			sessionTotal = result.count;
			loadingSessions = false;
		});
}
getInitialResults()

function getNextResults() {
	loadingSessions = true;
	fetch(urlBaseSessions + `&offset=${currentOffset+apiLimit}`, { headers: apiHeaders })
		.then(response => response.json())
		.then(result => {
			sessions = result.items;
			currentOffset += apiLimit;
			loadingSessions = false;
		});
}

function getPreviousResults() {
	loadingSessions = true;
	fetch(urlBaseSessions + `&offset=${currentOffset-apiLimit}`, { headers: apiHeaders })
		.then(response => response.json())
		.then(result => {
			sessions = result.items;
			currentOffset -= apiLimit;
			loadingSessions = false;
		});
}
</script>
<main>

	<TitleBar IMG_URL={PROFILE_USER.image_url} TITLE={PROFILE_USER.username} SIDE_LINKS={[]} ICON_LINKS={[]}/>
	{#if myProfile}
	<section>
		<div class="section-title-bar">
			<a class="no-link"><h2 style="margin-right:10px">My Account</h2></a>
		</div>
		<div class="section-content">
			<a href="/account/password/change/" title="Change password">change my password</a>
			<a href="{CHANGE_AVATAR_URL}" title="Change profile picture">change my profile picture</a>
		</div>
	</section>
	{/if}
	<!--
	<section>
		<div class="section-title-bar">
			<button class="section-toggle-btn"
				on:click={() => {showSummary = !showSummary}}>
				<a id="preview"><h2 style="margin-right:10px">
					{#if myProfile}My {/if}Content Summary
				</h2></a>
				<i class="header fa {showSummary == true ? 'fa-angle-double-down' : 'fa-angle-double-right'}"></i>
			</button>
		</div>
		{#if showSummary}
		<div class="section-content">
		</div>
		{/if}
	</section>
	-->
	<section>
		<div class="section-title-bar">
			<button class="section-toggle-btn"
				on:click={() => {showSessions = !showSessions}}>
				<a id="preview"><h2 style="margin-right:10px">
					{#if myProfile}My {/if}Session History
				</h2></a>
				<i class="header fa {showSessions == true ? 'fa-angle-double-down' : 'fa-angle-double-right'}"></i>
			</button>
		</div>
		{#if showSessions}
		<div class="section-content">
			<div>
				<button disabled={currentOffset < apiLimit || loadingSessions} on:click={getPreviousResults}>
					<i class="fa fa-angle-double-left"></i>
					newer
				</button>
				{currentOffset} - {currentOffset + apiLimit < sessionTotal ? currentOffset + apiLimit : sessionTotal} ({sessionTotal})
				<button disabled={currentOffset + apiLimit >= sessionTotal || loadingSessions} on:click={getNextResults}>
					older
					<i class="fa fa-angle-double-right"></i>
				</button>
			</div>
			{#if loadingSessions}
			<div class='lds-ellipsis'><div></div><div></div><div></div><div></div></div>
			{:else}
			<TableSort items={sessions}>
				<tr slot="thead">
					<!-- <th data-sort="username" style="max-width:300px;" title="Name of mapped location"></th> -->
					<!-- <th data-sort="username" style="max-width:300px;" title="Name of mapped location">Username</th> -->
					<th title="Session Id">Id</th>
					<th title="Session type">Type</th>
					<th>Resource</th>
					<th>Status</th>
					<!-- <th data-sort="psesh_ct" style="width:25px; text-align:center; border-left: 1px solid gray;" title="Number of prep sessions">Prep Sessions</th> -->
					<!-- <th data-sort="gsesh_ct" style="width:25px; text-align:center;" title="Number of georeferencing sessions">Georef. Sessions</th> -->
					<!-- <th data-sort="total_ct" style="width:25px; text-align:center; border-left:1px solid gray;" title="Percent complete - G/(U+P+G)">Total Sessions</th> -->
					<th title="Session result note">Result</th>
					<!-- <th title="Ground control points created">Seconds</th> -->
					<th title="Date">Date</th>
				</tr>
				<tr slot="tbody" let:item={s} style="height:38px; vertical-align:center;">
					<td>{s.id}</td>
					<td>
						{#if s.type === "p"}
						<span title="Preparation">{s.type.toUpperCase()}</span>
						{:else if s.type === "g"}
						<span title="Georeference">{s.type.toUpperCase()}</span>
						{:else if s.type === "t"}
						<span title="Trim">{s.type.toUpperCase()}</span>
						{/if}
					</td>
					<td>
						{#if s.type === "p"}
						<a href="{s.doc.detail_url}" title="{s.doc.title}">
							{s.doc.title}
							<img style="max-height:50px;" src={s.doc.thumb_url} alt=""/>
						</a>
						{:else if s.type === "g" || s.type === "t"}
						<a href="{s.lyr.detail_url}" title="{s.lyr.title}">
							{s.lyr.title}
							<img style="max-height:50px;" src={s.lyr.thumb_url} alt=""/>
						</a>
						{/if}
					</td>
					<td>{s.status}</td>
					<td>{s.note}</td>
					<!-- <td>{s.user_input_duration}</td> -->
					<td>{s.date_created}</td>
				</tr>
			</TableSort>
			{/if}
		</div>
		{/if}
	</section>
	
</main>
<style>

a.no-link {
	color:unset;
	text-decoration:unset;
}

main { 
	margin-bottom: 10px;
}

h2 {
	font-size: 1.6em;
}

section {
	border-bottom: 1px solid rgb(149, 149, 149);
}


tr th {
	vertical-align: middle;
}
tr td {
	vertical-align: middle;
}

td > a {
	display: flex;
	justify-content: space-between;
	align-items: center;
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
i.header {
	font-size: 1.5em;
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