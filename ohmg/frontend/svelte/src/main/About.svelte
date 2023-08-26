<script>
import '../css/shared.css';

import TitleBar from '../components/TitleBar.svelte';

</script>

<main>
	<TitleBar TITLE={"About OldInsuranceMaps.net"} SIDE_LINKS={[]} ICON_LINKS={[]}/>
	<h2>Overview</h2>
	<p>OldInsuranceMaps.net is a place where anyone can georeference historical Sanborn fire insurance maps and anyone else can explore them.</p>
	<ul>
		<li>To see what maps have already be georeferenced, checkout the <a href="/browse">Browse</a> page.</li>
		<li>To request a new map on the site, find it in the <a href="https://loc.gov/collections/sanborn-maps">LOC Sanborn Collection</a>, and then fill out <a href="https://forms.gle/9fNLTmRrVWV9dtff7">this form</a>.</li>
	</ul>
	<h2>Collaborations</h2>
	<div class="collab-tile">
		<div style="display:flex; justify-content:left; align-items:center;">
			<img height=30 width=30 src="https://www.openhistoricalmap.org/assets/osm_logo-796d69930b9f9f0fb3aa93152588ad4a2719ffd0b1e321d6045bf343a44e863e.png" />
			<h4><a href="https://www.openhistoricalmap.org">OpenHistoricalMap</a></h4>
		</div>
		<div>
			OHM is an OpenStreetMap-inspired project, where contributors can add historical features from anywhere in the world. Any georeferenced historical maps on OldInsuranceMaps.net can be easily integrated as basemaps in the OHM editor, so that features can be digitized directly from them.
		</div>
	</div>
</main>

<style>

main {
	display: flex;
	flex-direction: column;
}

.tab-row {
	display:flex;
	flex-direction: row;
}
.tab-row div {
	color: white;
	width: 50%;
	cursor: pointer;
	background-color: #123B4F;
	margin: 10px;
	border-radius: 10px;
	font-size: 1em;
	text-align: center;
}
.tab-row div h2 {
	font-size: 1.5em;
	margin: 10px 0px;
}
.tab-row div.active {
	background-color: #2c689c;
}
.tab-row div:hover {
	background-color: #2c689c;
}

@media (max-width: 640px) {
	/* main {
		max-width: none;
	} */
	.tab-row {
		flex-direction: column;
	}
	.tab-row div {
		width: 100%;
	}
}


</style>
