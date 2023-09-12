<script>
import SvelteMarkdown from 'svelte-markdown'
import ArrowSquareOut from 'phosphor-svelte/lib/ArrowSquareOut'

import MapBrowse from './components/MapBrowse.svelte';
import LatestAdditions from './components/LatestAdditions.svelte';

import SessionList from './components/SessionList.svelte'

export let ITEM_API_URL;
export let SESSION_API_URL;
export let PLACES_GEOJSON_URL;
export let IS_MOBILE;
export let CSRFTOKEN;
export let OHMG_API_KEY;
export let NEWSLETTER_SLUG;
export let USER_SUBSCRIBED;
export let USER_EMAIL;
export let PLACES_CT;
export let ITEMS_CT;

let showBrowseMap = !IS_MOBILE;
$: showBrowseMapBtnLabel = showBrowseMap ? "Hide map finder" : "Show map finder";
let showBRMap = !IS_MOBILE;

const urlSegs = window.location.href.split('/')

if (urlSegs[urlSegs.length - 2] == 'about') {
	page = 'about'
}

</script>

<main>
	<div>
		<h1>OldInsuranceMaps.net</h1>
		<p>A crowdsourcing site for creating and viewing georeferenced mosaics of historical fire insurance maps from the Library of Congress. See <a href="/#how-it-works">how it works</a> or visit the <a href="/faq?utm_source=hero" target="_blank">about</a> or <a href="/faq?utm_source=hero" target="_blank">FAQ</a> pages to learn more.</p>
	</div>
	<div class="hero-banner img-bg-2">
		<div class="hero-banner-inner">
			<div>
			<h3>Recently Added Maps</h3>
			<LatestAdditions ITEM_API_URL={ITEM_API_URL} OHMG_API_KEY={OHMG_API_KEY}/>
		</div>
			<div id="link-list">
				<h3>Search All Maps</h3>
				<ul>
					<li><a href="/search/#map">By location ({PLACES_CT})</a></li>
					<li><a href="/search/#places">By place name ({PLACES_CT})</a></li>
					<li><a href="/search/#places">By item ({ITEMS_CT})</a></li>
				</ul>
				<span><em>To add more maps, <a href="https://docs.google.com/forms/d/e/1FAIpQLSeF6iQibKEsjIv4fiYIW4vVVxyimLL8sDLX4BLU7HSWsRBOFQ/viewform?usp=sf_link">fill out this form</a> or <a href="https://ohmg.dev/contact">get in touch</a>.</em></span>
			</div>
		</div>
		{#if NEWSLETTER_SLUG}
		<div>
			<form enctype="multipart/form-data"  method="post" action="/newsletter/{NEWSLETTER_SLUG}/subscribe/">
				<input type="hidden" name="csrfmiddlewaretoken" value={CSRFTOKEN}>
				<label for="id_email_field" style="margin-right:0; font-size: 1.15em;">Subscribe to the newsletter:</label> <input type="email" name="email_field" required="" id="id_email_field" value="{USER_EMAIL}" disabled={USER_SUBSCRIBED}>
				{#if USER_SUBSCRIBED}
				<a href="/newsletter/{NEWSLETTER_SLUG}?utm_source=index">manage subscription</a>
				{:else}
				<button id="id_submit" name="submit" value="Subscribe" type="submit">Subscribe</button>
				{/if}
			</form>
			<a href="/newsletter/{NEWSLETTER_SLUG}/archive/">newsletter archive</a>
		</div>
		{/if}
	</div>

	<div class="hero-banner2 img-bg-3">
		<div style="padding:0;">
			<div style="padding:5px;">
				<h3>Explore georeferenced maps from {PLACES_CT} locations...</h3>
				<p>Click a point to access the viewer for that locale, or <a href="/search/#places">search by place name</a>.
			</div>
			{#if IS_MOBILE}<span><button class="link-btn" on:click="{() => {showBrowseMap = !showBrowseMap}}">{ showBrowseMapBtnLabel }</button></span>{/if}
			{#if showBrowseMap}
			<MapBrowse PLACES_GEOJSON_URL={PLACES_GEOJSON_URL} MAP_HEIGHT={'400'} OHMG_API_KEY={OHMG_API_KEY} EMBEDDED={true} />
			{/if}
		</div>
	</div>

	<div id="how-it-works" class="hero-banner2 img-bg-1">
		<div>
			<h3>How it Works</h3>
			<div id="step-list">
				<div>
					<div><i class="i-volume i-volume-lg"></i></div>
					<p>
						Digital scans of Sanborn maps are available through the <a href="https://loc.gov/collections/sanborn-maps">Library of Congress</a> and are pulled into this site through the LOC <a href="https://www.loc.gov/apis/json-and-yaml/requests/">JSON API</a>, generating a "Volume Summary" page (<a href="/loc/sanborn03275_001/?utm_source=index">Baton Rouge, 1885</a>).
					</p>
				</div>
				<div>
					<div><i class="i-document i-document-lg"></i></div>
					<p>
						Contributors <a href="/split/244/">prepare each sheet</a> in the volume, sometimes splitting it into multiple documents, each to be georeferenced individually (<a href="/resource/244?utm_source=index">Baton Rouge, 1885, page 1</a>).
					</p>
				</div>
				<div>
					<div><i class="i-layer i-layer-lg"></i></div>
					<p>
						Next, each document must be georeferenced by <a href="/georeference/387?utm_source=index">creating ground control points</a>, linking features on the old map with latitude/longitude coordinates to create a geospatial layer (<a href="/resource/389?utm_source=index">Baton Rouge, 1885, page 1, part 3</a>).
					</p>
				</div>
				<div>
					<div><i class="i-webmap i-webmap-lg"></i></div>
					<p>
						As they are georeferenced, layers slowly build a collage of all the content from a given volume, and their overlapping margins <a href="/loc/sanborn03275_001?utm_source=index#multimask">must be trimmed</a> to create a seamless mosaic.
					</p>
				</div>
				<div>
					<div><i class="i-pinmap i-pinmap-lg"></i></div>
					<p>
						Finally, all volume mosaics for a given locale are automatically aggregated into a simple web viewer so you can easily compare different years and current maps (<a href="/viewer/baton-rouge-la?utm_source=index">Baton Rouge viewer</a>).
					</p>
				</div>
				<h4>Want to learn more? Visit the <a href="https://ohmg.dev/docs?utm_source=index" target="_blank">documentation site <ArrowSquareOut /></a>.</h4>
			</div>
		</div>
	</div>

	<div class="hero-banner2 img-bg-3">
		<div>
			<h3>Latest activity</h3>
			<p><a href="/activity">all activity</a></p>
			<SessionList SESSION_API_URL={SESSION_API_URL} OHMG_API_KEY={OHMG_API_KEY} limit={"10"} showThumbs={true} allowPagination={false} />
		</div>
	</div>

	<div class="hero-banner2" style="font-size:1.15em;">
		<div>
			<SvelteMarkdown source={`OldInsuranceMaps.net is funded in part by the National Institutes of Health (National Institute on Aging: [R01AG080401](https://reporter.nih.gov/search/bCrnkRo-rkWJJXyXqsj44g/project-details/10582012)) through a partnership with University of Michigan [Institute for Social Research](https://isr.umich.edu/), University of Richmond [Digital Scholarship Lab](https://dsl.richmond.edu/), and the [National Community Reinvestment Coalition](https://ncrc.org). Read more in the [ISR press release](https://isr.umich.edu/news-events/news-releases/grant-to-enable-creation-of-new-data-resources-for-studying-structural-racism/).

---

Many thanks also to our individual sponsors: Kevin H., Andrew M., and Peter M. To donate: [paypal.me/oldinsurancemaps](https://paypal.me/oldinsurancemaps)
`} />
		</div>
	</div>
</main>
<style>

main {
	display: flex;
	flex-direction: column;
	margin-right: -15px;
	margin-left: -15px;
}

main > div {
	margin-top: 35px;
	background-color: rgba(255, 255, 255, .5);
	padding: 15px;
	border-top: 1px solid grey;
	border-bottom: 1px solid grey;
}

main p {
	font-size:1.25em;
}

#how-it-works {
	scroll-margin-top: 60px;
}

#link-list {
	text-align: center;
}

.img-bg-1 {
	background: linear-gradient(0deg, rgba(255 255 255 / 60%), rgba(255 255 255 / 60%)), url(/static/img/no-1885-snippet1-reduce-50qual.jpg);
}

.img-bg-2 {
	background: linear-gradient(0deg, rgba(255 255 255 / 60%), rgba(255 255 255 / 60%)), url(/static/img/no-1885-snippet1-reduce-50qual.jpg) -700px -200px;
}

.img-bg-3 {
	background: linear-gradient(0deg, rgba(255 255 255 / 60%), rgba(255 255 255 / 60%)), url(/static/img/no-1885-snippet1-reduce-50qual.jpg) -700px -400px;
}

.img-bg-4 {
	background: linear-gradient(0deg, rgba(255 255 255 / 60%), rgba(255 255 255 / 60%)), url(/static/img/no-1885-snippet1-reduce-50qual.jpg) -700px -600px;
}

.hero-banner2 > div {
	background: rgba(255,255,255, .7);
	border: 2px solid black;
	border-radius: 4px;
	padding: 10px;
	margin-bottom: 10px;
	width: 100%
}

.hero-banner {
	display: flex;
	flex-direction: column;
	justify-content: space-between;
	background-repeat: no-repeat;
	background-position: center;
	background-size: cover;
}

.hero-banner > div {
	background: rgba(255,255,255, .6);
	border: 2px solid black;
	border-radius: 4px;
	padding: 10px;
	margin-bottom: 10px;
}

.hero-banner-inner {
	display:flex;
	flex-direction:row;
	justify-content: space-between;
}

.hero-banner-inner > div > ul {
	font-size: 1.25em;
	padding: 0;
	list-style: none;
}
.hero-banner-inner > div > ul li {
	padding-left: 5px;
}

#step-list > div {
	display: flex;
	align-items: center;
	padding-bottom: 5px;
	margin-bottom: 5px;
	border-bottom: dashed grey 1px;
}

#step-list > div:first-child {
	padding-top: 5px;
	border-top: dashed grey 1px;
}

#step-list div > div {
	min-width: 85px;
}

#step-list div > p {
	font-size: 1.1em;
	margin-bottom: 0px;
}

button.link-btn {
	color: #2c689c;
	background: none;
	border: none;
	cursor: pointer;
	font-size: 1.25em;
}

@media only screen and (max-width: 760px) {
	main {
		max-width: none;
	}

	.hero-banner {
		flex-direction: column;
	}

	.hero-banner > div {
		width: 100%;
	}

	.hero-banner > div.link-panel {
		margin-top: 15px;
	}

	.hero-banner-inner {
		flex-direction: column-reverse;
	}

	#link-list {
		width: 100%;
	}
}

</style>
