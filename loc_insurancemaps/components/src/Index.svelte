<script>
import MapBrowse from './MapBrowse.svelte';
export let CSRFTOKEN;
export let PLACES_GEOJSON;
</script>

<main class="banner">
	<div class="hero-banner">
		<div class="">
			<h1>Louisiana Sanborn Maps</h1>
			<p>Explore historical fire insurance maps of Louisiana as georeferenced web maps overlays. All maps on this site are in the public domain, pulled from the Library of Congress 
			<a href="https://loc.gov/collections/sanborn-maps">Sanborn Map Collection</a>.</p>
			<p>These maps were georeferenced by about <a href="/people">70 participants</a> in early 2022&mdash;over four months, 1,500 individual sheets
				from 270 different Sanborn atlases were processed, resulting in these seamless mosaics.
		</div>
		<div class="link-panel">
			<p>Jump to some popular places</p>
			<ul>
				<li><a href="/viewer/new-orleans-la">New Orleans (1885-1893) &rarr;</a></li>
				<li><a href="/viewer/baton-rouge-la">Baton Rouge (1885, 1891, 1898, 1903, 1908) &rarr;</a></li>
				<li><a href="/viewer/alexandria-la">Alexandria (1885, 1892, 1896, 1900, 1904, 1909) &rarr;</a></li>
				<li><a href="/viewer/plaquemine-la">Plaquemine (1885, 1891, 1896, 1900, 1906) &rarr;</a></li>
			</ul>
			<p>or search through <a href="/browse">all volumes</a>.</p>
			<p>Currently, this site includes maps for about 140 different towns and cities across Louisiana. Want to get your hometown added? Check out our <a href="https://about.oldinsurancemaps.net/faq">FAQ page</a>.</p>
			<p>You can find out how this whole thing works in the <a href="https://about.oldinsurancemaps.net/blog">blog</a>.</p>
		</div>
	</div>
	<div class="map-container">
		<MapBrowse PLACES_GEOJSON={PLACES_GEOJSON} MAP_HEIGHT={'400'} />
	</div>
	<div class="map-link-panel">
		<h3><a href="/browse">Open Browsable Map</a></h3>
	</div>
	<!-- <div>
		<form enctype="multipart/form-data" method="post" action="/newsletter/news-oldinsurancemapsnet/subscribe/">
			<label for="id_email_field">E-mail:</label> <input type="email" name="email_field" required="" id="id_email_field">
			<button id="id_submit" name="submit" value="Subscribe" type="submit">Subscribe</button>
		</form>
	</div> -->
</main>
<style>

main {
	display: flex;
	flex-direction: column;
}

main > div {
	margin-top: 35px;
	background-color: rgba(255, 255, 255, .5);
	padding: 15px;
	border-top: 1px solid grey;
	border-bottom: 1px solid grey;
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

.map-link-panel {
	display: none;
	text-align: center;
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

	.map-container {
		display: none;
	}



	.map-link-panel {
		display: flex;
	}
}

</style>
