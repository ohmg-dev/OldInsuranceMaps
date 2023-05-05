<script>

import './css/shared.css';
import MapBrowse from './MapBrowse.svelte';
import RecentActivity from './RecentActivity.svelte';
import LatestAdditions from './LatestAdditions.svelte';

export let ITEM_API_URL;
export let SESSION_API_URL;
export let PLACES_GEOJSON_URL;
export let IS_MOBILE;
export let CSRFTOKEN;
export let OHMG_API_KEY;
export let NEWSLETTER_SLUG;
export let USER_SUBSCRIBED;
export let USER_EMAIL;
export let VIEWER_SHOWCASE;
export let PLACES_CT;
export let ITEMS_CT;

let showBrowseMap = !IS_MOBILE;
$: showBrowseMapBtnLabel = showBrowseMap ? "Hide map finder" : "Show map finder";
let showBRMap = !IS_MOBILE;
$: showBRMapBtnLabel = showBRMap ? "Hide example viewer (Baton Rouge)" : "Show example viewer (Baton Rouge)";
</script>

<main>
	<div>
		<h1>OldInsuranceMaps.net</h1>
		<p>A crowdsourcing site for creating and viewing georeferenced mosaics of historical fire insurance maps from the Library of Congress. <a href="https://ohmg.dev" target="_blank">Learn more &nearr;</a></p>
	</div>
	<div class="hero-banner">
		<div>
			<h2>Get Started</h2>
			<ul>
				<li><a href="/browse/">Find maps of your city &rarr;</a></li>
				<li><a href="/browse/#items">Browse all volumes &rarr;</a></li>
				<li><a href="/people">User list &rarr;</a></li>
				{#if NEWSLETTER_SLUG}
				<li><a href="#subscribe">Subscribe to newsletter &darr;</a></li>
				{/if}
				<li><a href="#support">Support this project &darr;</a></li>
			</ul>
			<h2>Recently Added Items</h2>
			<p>Check out the latest additions to the site below, or <a href="/browse/#items">browse all {ITEMS_CT} items</a>.</p>
			<LatestAdditions ITEM_API_URL={ITEM_API_URL} OHMG_API_KEY={OHMG_API_KEY}/>
			<span><em>If you or your organization would like to sponsor the addition of more items from the Library of Congress <a href="https://loc.gov/collections/sanborn-maps">Sanborn Map Collection</a>, please <a href="https://ohmg.dev/contact">get in touch</a>.</em></span>
		</div>
		<div>
			<h2>Featured Places</h2>
			<p>An interactive web viewer aggregates all georeferenced mosaics for a given city. Check out some featured places below, or <a href="/browse/#places">browse all {PLACES_CT} places</a>.
			<ul>
				<li><a href="/viewer/new-orleans-la?utm_source=index-top">New Orleans, La. (1885-1893) &rarr;</a></li>
				<li><a href="/viewer/baton-rouge-la?utm_source=index-top">Baton Rouge, La. (1885, 1891, 1898, 1903, 1908) &rarr;</a></li>
				<li><a href="/viewer/alexandria-la?utm_source=index-top">Alexandria, La. (1885, 1892, 1896, 1900, 1904, 1909) &rarr;</a></li>
				<li><a href="/viewer/plaquemine-la?utm_source=index-top">Plaquemine, La. (1885, 1891, 1896, 1900, 1906) &rarr;</a></li>
			</ul>
			<RecentActivity SESSION_API_URL={SESSION_API_URL} OHMG_API_KEY={OHMG_API_KEY} />
		</div>
	</div>
	<div class="map-container">
		{#if IS_MOBILE}<span><button class="link-btn" on:click="{() => {showBrowseMap = !showBrowseMap}}">{ showBrowseMapBtnLabel }</button></span>{/if}
		{#if showBrowseMap}
		<MapBrowse PLACES_GEOJSON_URL={PLACES_GEOJSON_URL} MAP_HEIGHT={'400'} OHMG_API_KEY={OHMG_API_KEY} EMBEDDED={true} />
		{/if}
	</div>

	<div>
		<h3>How it Works</h3>
		<div id="step-list">
			<div>
				<div><i class="i-volume i-volume-lg"></i></div>
				<p>
					Editions or volumes of Sanborn maps are available through the <a href="https://loc.gov/collections/sanborn-maps">Library of Congress</a> and are pulled into this site through their <a href="https://www.loc.gov/apis/json-and-yaml/requests/">JSON API</a>, generating a "Volume Summary" page here (see <a href="/loc/sanborn03275_001/?utm_source=index">Baton Rouge, 1885</a>).
				</p>
			</div>
			<div>
				<div><i class="i-document i-document-lg"></i></div>
				<p>
					Crowdsourcing participants <a href="/split/244/">prepare each sheet</a> in the volume individually, sometimes splitting a sheet into multiple documents, each of which must be georeferenced individually (see <a href="/resource/244?utm_source=index">Baton Rouge, 1885, page 1</a>).
				</p>
			</div>
			<div>
				<div><i class="i-layer i-layer-lg"></i></div>
				<p>
					Participants georeference each document by <a href="/georeference/387?utm_source=index">creating ground control points</a>, linking features on the old map with latitude/longitude coordinates and embedding this geographic information, creating a geospatial layer (see <a href="/resource/389?utm_source=index">Baton Rouge, 1885, page 1, part 3</a>).
				</p>
			</div>
			<div>
				<div><i class="i-webmap i-webmap-lg"></i></div>
				<p>
					As they are georeferenced, layers slowly build a collage of all the content from a given volume, and their overlapping margins <a href="/loc/trim/sanborn03275_001?utm_source=index">must be trimmed</a> to create a seamless mosaic.
				</p>
			</div>
			<div>
				<div><i class="i-pinmap i-pinmap-lg"></i></div>
				<p>
					Finally, all volume mosaics for a given place are automatically aggregated into a standard web viewer (see <a href="/viewer/baton-rouge-la?utm_source=index">Baton Rouge, 1885-1908</a>).
				</p>
			</div>
			<h4>Want to learn more? Head to the <a href="https://ohmg.dev/docs?utm_source=index">full documentation</a> for more information.</h4>
			<span><em>Icons by <a href="https://thenounproject.com/browse/creator/alex2900/icon-collections/?p=1">Alex Muravev</a> on the Noun Project.</em></span>
		</div>
	</div>

	{#if VIEWER_SHOWCASE}
	<div class="map-container">
		{#if IS_MOBILE}<button class="link-btn" on:click="{() => {showBRMap = !showBRMap}}">{ showBRMapBtnLabel }</button>{/if}
		{#if showBRMap}
		<iframe height={IS_MOBILE ? '600px' : '400px'} title="Viewer for {VIEWER_SHOWCASE.name}" style="width:100%; border:none;" src={VIEWER_SHOWCASE.url}></iframe>
		{/if}
		{#if IS_MOBILE}<a href={VIEWER_SHOWCASE.url}>View in fullscreen &rarr;</a>{/if}
		<div style="font-size:.9em;">
		<p style="margin-right:15px; margin-left:15px;"><em>If you would like to embed this viewer (or that of <a href="/browse">any city</a>) on your own website, please <a href="/#contact">get in touch</a> (it's really easy!).</em></p>
		</div>
	</div>
	{/if}

	<div>
		<h3>Get Involved</h3>
		<div id="getting-started-list">
			<div>
				<h4>Georeference content...</h4>
				<p><a href="/account/signup">Create an account</a> then head to <a href="https://ohmg.dev/docs/category/making-the-mosaics-1">Making the Mosaics</a> to learn more about the process. The <a href="/browse/#items">Browse</a> page is the best place to find content to work on.</p>
			</div>
			{#if NEWSLETTER_SLUG}
			<div>
				<h4 id="subscribe">Subscribe to the newsletter...</h4>
				<p>Use this form only if you want to subscribe without signing up for an account (creating an account will automatically subscribe you to the newsletter).</p>
				<form enctype="multipart/form-data"  method="post" action="/newsletter/{NEWSLETTER_SLUG}/subscribe/">
					<input type="hidden" name="csrfmiddlewaretoken" value={CSRFTOKEN}>
					<label for="id_email_field" style="margin-right:0;">E-mail:</label> <input type="email" name="email_field" required="" id="id_email_field" value="{USER_EMAIL}" disabled={USER_SUBSCRIBED}>
					{#if USER_SUBSCRIBED}
					<a href="/newsletter/{NEWSLETTER_SLUG}?utm_source=index">manage subscription</a>
					{:else}
					<button id="id_submit" name="submit" value="Subscribe" type="submit">Subscribe</button>
					{/if}
				</form>
				<p><a href="/newsletter/{NEWSLETTER_SLUG}/archive/">view newsletter archive</a></p>
			</div>
			{/if}
			<div>
				<h4 id="support">Support the project...</h4> 
				<p>You can donate to <a href="https://paypal.me/oldinsurancemaps">paypal.me/oldinsurancemaps</a> to help with this site's (relatively modest) hosting costs. To sponsor development on specific aspects of the site or the addition of more volumes, please get in touch through the methods described below.</p>
			</div>
			<div>
				<h4 id="contact">Get in touch...</h4>
				<p>
					Questions, concerns, or feedback &mdash; <a href="mailto:hello@oldinsurancemaps.net">hello@oldinsurancemaps.net</a><br>
					Bugs and technical discussion &mdash; <a href="https://github.com/mradamcox/ohmg">mradamcox/ohmg</a>
				</p>
			</div>
		</div>
	</div>

	<div>
		<h3 id="acknowledgements">Acknowledgments</h3>
		<div style="font-size:.9em;">
			<p>Thank you to all of our <a href="/people">crowdsourcing participants</a>. Over four months in early 2022, volunteers prepared and georeferenced 1,500 individual sheets from 270 different Sanborn atlases. You can read much more about that effort <a href="https://digitalcommons.lsu.edu/gradschool_theses/5641/" target="_blank">here</a>.</p>
			<p>This site is built from many different open source software components, so a big thank you is due to the developers behind <a href="https://geonode.org">GeoNode</a>, <a href="https://github.com/developmentseed/titiler">TiTiler</a>, <a href="https://mapserver.org/">MapServer</a>, <a href="https://postgres.org">Postgres</a>/<a href="https://postgis.net/">PostGIS</a>, <a href="https://www.djangoproject.com/">Django</a>, <a href="https://openlayers.org/">OpenLayers</a>, <a href="https://viglino.github.io/ol-ext/">ol-ext</a>, and <a href="https://svelte.dev/">Svelte</a>.
			</p>
			<p>All maps on this site are in the public domain, pulled from the Library of Congress <a href="https://loc.gov/collections/sanborn-maps">Sanborn Map Collection</a>.</p>
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

.hero-banner {
	display: flex;
	flex-direction: row;
	justify-content: space-between;
	background: linear-gradient(0deg, rgba(255 255 255 / 60%), rgba(255 255 255 / 60%)), url(/static/img/no-1885-snippet1-reduce-50qual.jpg);
	background-repeat: no-repeat;
	background-position: center;
	background-size: cover;
}

.hero-banner > div {
	background: rgba(255,255,255, .6);
	border: 2px solid black;
	border-radius: 4px;
	padding: 10px;
	width: 48%;
}

.hero-banner > div > ul {
	font-size: 1.25em;
	padding: 0;
	list-style: none;
}
.hero-banner > div > ul li {
	padding-left: 5px;
}
.map-container {
	padding: 0px;
}

.map-container > span {
	text-align:center;
}

#getting-started-list > div {
	padding-bottom: 5px;
	margin-bottom: 5px;
	border-bottom: dashed grey 1px;
}

#getting-started-list > div > p {
	font-size: 1.1em;
}

#getting-started-list > div:first-child {
	padding-top: 5px;
	border-top: dashed grey 1px;
}

#getting-started-list > div:last-child {
	border-bottom: none;
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

#contact, #support, #subscribe {
  scroll-margin-top: 50px;
}

button.link-btn {
	color: #2c689c;
	background: none;
	border: none;
	cursor: pointer;
	font-size: 1.25em;
}

@media only screen and (max-width: 480px) {
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
}

</style>
