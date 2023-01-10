<script>
export let USER;
</script>
<nav class="lahmg-footer">
	<div class="main-row">
		<div>
			<h4>Content</h4>
			<ul>
				<li><a href="/browse">Browse Maps</a></li>
				<li><a href="/people">Participants</a></li>
				<li><a href="https://github.com/mradamcox/loc-insurancemaps">GitHub <i class="fa fa-external-link"></i></a></li>
			</ul>
		</div>
		<div>
			<h4>Learn More</h4>
			<ul>
				<li><a href="https://about.oldinsurancemaps.net/faq">FAQ <i class="fa fa-external-link"></i></a></li>
				<li><a href="https://about.oldinsurancemaps.net/docs">Documentation <i class="fa fa-external-link"></i></a></li>
				<li><a href="https://about.oldinsurancemaps.net/docs/category/sanborn-maps-1">About Sanborn Maps <i class="fa fa-external-link"></i></a></li>
			</ul>
		</div>
		<div>
			<h4>News & Updates</h4>
			<ul>
				<li><a href="/newsletter/lahmg-news/archive" >Newsletter Archive</a></li>
				<li><a href="https://about.oldinsurancemaps.net/blog" >Blog <i class="fa fa-external-link"></i></a></li>
				<li><a href="https://about.oldinsurancemaps.net/contact" >Contact <i class="fa fa-external-link"></i></a></li>
			</ul>
		</div>
	</div>
	<div style="color:lightgrey; text-align:right;">
		<p>Copyright © 2023</p>
	</div>
</nav>
<style>
	nav.lahmg-footer {
		display: flex;
		flex-direction: column;
		background:#123B4F;
		color: white;
		padding: 20px;
		font-weight: 500;
		min-height: 190px;
	}
	.main-row {
		display: flex;
		flex-direction: row;
		justify-content: space-around;
	}
	nav.lahmg-footer a {
		color: white;
		text-decoration: none;
	}

	nav.lahmg-footer > div {
		margin: 0px 10px;
	}

	ul {
		padding: 0;
		margin: 0;
		list-style: none;
	}

	@media only screen and (max-width: 480px) {
		.main-row {
			flex-direction: column;
		}
	}
</style>
