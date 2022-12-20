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
		</div>
		<div class="link-panel">
			<div>
				<p><a href="/browse">Browse all</a></p>
				<p><a href="https://about.oldinsurancemaps.net">Learn more</a></p>
			</div>
			<div class="featured-panel">
				<p>Popular Locations</p>
				<ul>
					<li><a href="/viewer/new-orleans-la">New Orleans (1885-1893)</a> ~ <a href="/loc/sanborn03376_004">detail</a></li>
					<li><a href="/viewer/baton-rouge-la">Baton Rouge (1885, 1891, 1898, 1903, 1908)</a> (<a href="/loc/sanborn03275_001/">detail</a>)</li>
					<li><a href="/viewer/alexandria-la">Alexandria (1885, 1892, 1896, 1900, 1904, 1909)</a> (<a href="/loc/sanborn03267_001/">detail</a>)</li>
					<li><a href="/viewer/plaquemine-la">Plaquemine (1885, 1891, 1896, 1900, 1906)</a> (<a href="/loc/sanborn03386_001/">detail</a>)</li>
				</ul>
			</div>
		</div>
	</div>
	<div class="map-container">
		<MapBrowse PLACES_GEOJSON={PLACES_GEOJSON} MAP_HEIGHT={'400'} />
	</div>
	<div class="map-link-panel">
		<h3><a href="/browse">Open Browsable Map</a></h3>
	</div>
	<div class="">
		<p>The content on this website is the result of a crowdsourcing pilot project that took place in early 2022. About
			70 people signed up, and over half of them helped to process the maps in some way--splitting, georeferencing, or trimming them. Over four months, 1,500 individual sheets
			from 270 different Sanborn atlases were processed, resulting in <a href="/browse">seamless mosaics</a> of 130 towns and cities across Louisiana.
		</p>
		<p>
		You can read a bit more in the <a href="https://about.oldinsurancemaps.net">about</a>
		page, or a <em>lot</em> more in my thesis, <a href="https://digitalcommons.lsu.edu/gradschool_theses/5641/">
		"Creating a Public Space for Georeferencing Sanborn Maps"</a>. Thanks!
		</p>
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
	margin-top: 45px;
	background-color: rgba(255, 255, 255, .5);
	padding: 15px;
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

.map-container {
	padding: 0px;
	border-top: 1px solid grey;
	border-bottom: 1px solid grey;
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
