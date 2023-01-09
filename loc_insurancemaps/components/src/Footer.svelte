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
			</ul>
		</div>
		<div>
			<h4>Learn More</h4>
			<ul>
				<li><a href="https://about.oldinsurancemaps.net/faq">FAQ</a></li>
				<li><a href="https://about.oldinsurancemaps.net/docs">Documentation</a></li>
				<li><a href="https://about.oldinsurancemaps.net/docs/category/sanborn-maps-1">About Sanborn Maps</a></li>
			</ul>
		</div>
		<div>
			<h4>Get in touch!</h4>
			<ul>
				<li><a href="mailto:hello@oldinsurancemaps.net" >hello@oldinsurancemaps.net</a></li>
				<li><a href="https://github.com/mradamcox/loc-insurancemaps">GitHub</a></li>
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
