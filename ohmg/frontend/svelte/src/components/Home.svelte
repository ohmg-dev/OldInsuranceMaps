<script>
	import SvelteMarkdown from 'svelte-markdown'

	import Link from '@components/base/Link.svelte';
	import SVGIcon from '@components/base/SVGIcon.svelte';
	import MapBrowse from '@components/interfaces/MapBrowse.svelte';

	import LatestAdditions from '@components/lists/LatestAdditions.svelte';
	import SessionList from '@components/lists/SessionList.svelte'

	export let CONTEXT;
	export let NEWSLETTER_SLUG;
	export let USER_SUBSCRIBED;
	export let PLACES_CT;
	export let MAP_CT;

	let showBrowseMap = !CONTEXT.on_mobile;
	$: showBrowseMapBtnLabel = showBrowseMap ? "Hide map finder" : "Show map finder";

	const urlSegs = window.location.href.split('/')

</script>

<main>
	<div>
		<h1>OldInsuranceMaps.net</h1>
		<p>A crowdsourcing site for creating and viewing georeferenced mosaics of historical fire insurance maps from the Library of Congress. See <Link href="/#how-it-works">how it works</Link> or visit the <Link href="/about?utm_source=hero" external={true}>about</Link> or <Link href="/faq?utm_source=hero">FAQ</Link> pages to learn more.</p>
	</div>

	<div class="hero-banner2 img-bg-3">
		<div style="padding:0;">
			<div style="padding:5px;">
				<h3>Explore georeferenced maps from {PLACES_CT} locations...</h3>
				<p>Click a point to access maps of that locale, or <Link href="/united-states">search by place name</Link>.
			</div>
			{#if CONTEXT.on_mobile}<span><button class="link-btn" on:click="{() => {showBrowseMap = !showBrowseMap}}">{ showBrowseMapBtnLabel }</button></span>{/if}
			{#if showBrowseMap}
			<MapBrowse {CONTEXT} MAP_HEIGHT={'400'} EMBEDDED={true} />
			{/if}
		</div>
	</div>

	<div class="hero-banner img-bg-2">
		<div class="hero-banner-inner">
			<div>
			<h3>Recently Added Maps</h3>
			<LatestAdditions {CONTEXT}/>
			<span><em>Want to see more? View <Link href="/search/#items">all items</Link> and sort by <strong>Load date</strong>.</em></span>
		</div>
			<div id="link-list">
				<h3>Search All Maps</h3>
				<ul>
					<li><Link href="/search/#map">By location ({PLACES_CT})</Link></li>
					<li><Link href="/search/#places">By place name ({PLACES_CT})</Link></li>
					<li><Link href="/search/#places">By item ({MAP_CT})</Link></li>
				</ul>
				<span><em>To request more maps, <Link href="https://docs.google.com/forms/d/e/1FAIpQLSeF6iQibKEsjIv4fiYIW4vVVxyimLL8sDLX4BLU7HSWsRBOFQ/viewform?usp=sf_link" external={true}>fill out this form</Link> or <Link href="/contact">get in touch</Link>.</em></span>
			</div>
		</div>
		{#if NEWSLETTER_SLUG}
		<div>
			<form enctype="multipart/form-data"  method="post" action="/newsletter/{NEWSLETTER_SLUG}/subscribe/">
				<input type="hidden" name="csrfmiddlewaretoken" value={CONTEXT.csrf_token}>
				<label for="id_email_field" style="margin-right:0; font-size: 1.15em;">Subscribe to the newsletter:</label> <input type="email" name="email_field" required="" id="id_email_field" value="{CONTEXT.user.email}" disabled={USER_SUBSCRIBED}>
				{#if USER_SUBSCRIBED}
				<Link href="/newsletter/{NEWSLETTER_SLUG}?utm_source=index">manage subscription</Link>
				{:else}
				<button id="id_submit" name="submit" value="Subscribe" type="submit">Subscribe</button>
				{/if}
			</form>
			<Link href="/newsletter/{NEWSLETTER_SLUG}/archive/">newsletter archive</Link>
		</div>
		{/if}
	</div>

	<div id="how-it-works" class="hero-banner2 img-bg-1">
		<div>
			<h3>How it Works</h3>
			<div id="step-list">
				<div>
					<div>
						<SVGIcon icon="volume" size="lg" />
					</div>
					<p>
						Digital scans of Sanborn maps are available through the <Link href="https://loc.gov/collections/sanborn-maps" external={true}>Library of Congress</Link> and are pulled into this site through the LOC <Link href="https://www.loc.gov/apis/json-and-yaml/requests/" external={true}>JSON API</Link>, generating a "Volume Summary" page (<Link href="/map/sanborn03275_001/?utm_source=index">Baton Rouge, 1885</Link>).
					</p>
				</div>
				<div>
					<div>
						<SVGIcon icon="document" size="lg" />
					</div>
					<p>
						Contributors <Link href="/split/244/">prepare each sheet</Link> in the volume, sometimes splitting it into multiple documents, each to be georeferenced individually (<Link href="/resource/244?utm_source=index">Baton Rouge, 1885, page 1</Link>).
					</p>
				</div>
				<div>
					<div>
						<SVGIcon icon="layer" size="lg" />
					</div>
					<p>
						Next, each document must be georeferenced by <Link href="/georeference/387?utm_source=index">creating ground control points</Link>, linking features on the old map with latitude/longitude coordinates to create a geospatial layer (<Link href="/resource/389?utm_source=index">Baton Rouge, 1885, page 1, part 3</Link>).
					</p>
				</div>
				<div>
					<div>
						<SVGIcon icon="webmap" size="lg" />
					</div>
					<p>
						As they are georeferenced, layers slowly build a collage of all the content from a given volume, and their overlapping margins <Link href="/map/sanborn03275_001?utm_source=index#multimask">must be trimmed</Link> to create a seamless mosaic.
					</p>
				</div>
				<div>
					<div>
						<SVGIcon icon="pinmap" size="lg" />
					</div>
					<p>
						Finally, all volume mosaics for a given locale are automatically aggregated into a simple web viewer so you can easily compare different years and current maps (<Link href="/viewer/baton-rouge-la?utm_source=index">Baton Rouge viewer</Link>).
					</p>
				</div>
				<h4>Want to learn more? Visit the <Link href="https://docs.oldinsurancemaps.net?utm_source=index" external={true}>documentation site</Link>.</h4>
			</div>
		</div>
	</div>

	<div class="hero-banner2 img-bg-3">
		<div>
			<h3>Latest activity</h3>
			<p><Link href="/activity">all activity</Link></p>
			<SessionList {CONTEXT} limit={"10"} showThumbs={true} paginate={false} />
		</div>
	</div>

	<div class="hero-banner2" style="font-size:1.15em;">
		<div>
			<SvelteMarkdown source={`OldInsuranceMaps.net is funded in part by the National Institutes of Health (National Institute on Aging: [R01AG080401](https://reporter.nih.gov/search/bCrnkRo-rkWJJXyXqsj44g/project-details/10582012)) through a partnership with University of Michigan [Institute for Social Research](https://isr.umich.edu/), University of Richmond [Digital Scholarship Lab](https://dsl.richmond.edu/), and the [National Community Reinvestment Coalition](https://ncrc.org). Read more in the [ISR press release](https://isr.umich.edu/news-events/news-releases/grant-to-enable-creation-of-new-data-resources-for-studying-structural-racism/).

Many thanks also to our individual sponsors: Kevin H., Andrew M., Peter M., and Pete Z.

To donate: [paypal.me/oldinsurancemaps](https://paypal.me/oldinsurancemaps)
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
	scroll-margin-top: 40px;
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

.hero-banner2 > div {
	background: rgba(255,255,255, .7);
	border: 2px solid black;
	border-radius: 4px;
	padding: 10px;
	margin-bottom: 10px;
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

	.hero-banner-inner {
		flex-direction: column-reverse;
	}

	#link-list {
		width: 100%;
	}
}

</style>
