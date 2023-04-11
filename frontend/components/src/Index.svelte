<script>
import './css/shared.css';
import MapBrowse from './MapBrowse.svelte';
export let PLACES_GEOJSON_URL;
export let IS_MOBILE;
export let CSRFTOKEN;
export let OHMG_API_KEY;
export let NEWSLETTER_SLUG;
export let USER_SUBSCRIBED;
export let USER_EMAIL;
export let VIEWER_SHOWCASE;

let showBrowseMap = !IS_MOBILE;
$: showBrowseMapBtnLabel = showBrowseMap ? "Hide map finder" : "Show map finder";
let showBRMap = !IS_MOBILE;
$: showBRMapBtnLabel = showBRMap ? "Hide example viewer (Baton Rouge)" : "Show example viewer (Baton Rouge)";
</script>

<main>
	<div class="hero-banner">
		<div class="">
			<h1>Louisiana Sanborn Maps</h1>
			<p>All maps on this site are in the public domain, pulled from the Library of Congress 
			<a href="https://loc.gov/collections/sanborn-maps">Sanborn Map Collection</a>.</p>
			<p>Thank you to all of our <a href="/people">crowdsourcing participants</a>. Over four months in early 2022, 1,500 individual sheets from 270 different Sanborn atlases were georeferenced.</p>
			{#if NEWSLETTER_SLUG}
			<p><a href="#subscribe"><strong>Subscribe to updates</strong></a></p>
			{/if}
			<p><a href="#support"><strong>Support this project</strong></a></p>
		</div>
		<div class="link-panel">
			<p>Jump to some popular places</p>
			<ul>
				<li><a href="/viewer/new-orleans-la?utm_source=index-top">New Orleans (1885-1893) &rarr;</a></li>
				<li><a href="/viewer/baton-rouge-la?utm_source=index-top">Baton Rouge (1885, 1891, 1898, 1903, 1908) &rarr;</a></li>
				<li><a href="/viewer/alexandria-la?utm_source=index-top">Alexandria (1885, 1892, 1896, 1900, 1904, 1909) &rarr;</a></li>
				<li><a href="/viewer/plaquemine-la?utm_source=index-top">Plaquemine (1885, 1891, 1896, 1900, 1906) &rarr;</a></li>
			</ul>
			<p>or search through <a href="/browse">all volumes</a>.</p>
			<p>Currently, this site includes maps for about 140 different towns and cities across Louisiana. Want to get your hometown added? Check out our <a href="https://about.oldinsurancemaps.net/faq?utm_source=index">FAQ page</a>.</p>
		</div>
	</div>
	<div class="map-container">
		{#if IS_MOBILE}<span><button class="link-btn" on:click="{() => {showBrowseMap = !showBrowseMap}}">{ showBrowseMapBtnLabel }</button></span>{/if}
		{#if showBrowseMap}
		<MapBrowse PLACES_GEOJSON_URL={PLACES_GEOJSON_URL} MAP_HEIGHT={'400'} OHMG_API_KEY={OHMG_API_KEY} />
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
			<h4>Want to learn more? Head to the <a href="https://about.oldinsurancemaps.net/docs?utm_source=index">full documentation</a> for more information.</h4>
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
		<p style="margin-right:15px; margin-left:15px;"><em>If you would like to embed this viewer (or that of <a href="/browse">any city</a>) on your own website, please <a href="https://about.oldinsurancemaps.net/contact">get in touch</a> (it's really easy!).</em></p>
		</div>
	</div>
	{/if}

	<div>
		<h3 id="support">Support this project</h3>
		<div style="font-size:.9em;">
			<p>If you'd like to help with the (relatively modest) hosting costs and continued development of this site, you can do so here: <a href="https://paypal.me/oldinsurancemaps">paypal.me/oldinsurancemaps</a>. Be sure to add a note if you want to support development on specific aspects of the site, or sponsor the addition of more volumes. Thanks!</p>
		</div>
		<hr>
		<h3 id="support">Some thank yous...</h3>
		<div style="font-size:.9em;">
			<p>This site is built from many different open source software components, so a big thank you is due to the developers behind <a href="https://geonode.org">GeoNode</a>, <a href="https://github.com/developmentseed/titiler">TiTiler</a>, <a href="https://mapserver.org/">MapServer</a>, <a href="https://postgres.org">Postgres</a>/<a href="https://postgis.net/">PostGIS</a>, <a href="https://www.djangoproject.com/">Django</a>, <a href="https://openlayers.org/">OpenLayers</a>, <a href="https://viglino.github.io/ol-ext/">ol-ext</a>, and <a href="https://svelte.dev/">Svelte</a>.
			</p>
		</div>
		<hr>
		{#if NEWSLETTER_SLUG}
		<h3 id="subscribe">Subscribe to our newsletter</h3>
		<form enctype="multipart/form-data"  method="post" action="/newsletter/{NEWSLETTER_SLUG}/subscribe/">
			<input type="hidden" name="csrfmiddlewaretoken" value={CSRFTOKEN}>
			<label for="id_email_field" style="margin-right:0;">E-mail:</label> <input type="email" name="email_field" required="" id="id_email_field" value="{USER_EMAIL}" disabled={USER_SUBSCRIBED}>
			{#if USER_SUBSCRIBED}
			<a href="/newsletter/{NEWSLETTER_SLUG}?utm_source=index">manage subscription</a>
			{:else}
			<button id="id_submit" name="submit" value="Subscribe" type="submit">Subscribe</button>
			{/if}
		</form>
		{/if}
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
	justify-content: space-around;
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
	width: 45%;
}

.link-panel ul {
	padding: 0;
	list-style: none;
}
.link-panel ul li {
	padding-left: 5px;
}
.map-container {
	padding: 0px;
}

.map-container > span {
	text-align:center;
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
