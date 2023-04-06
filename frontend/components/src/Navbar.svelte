<script>
export let USER;
</script>
<nav class="lahmg-nav">
	<div>
		<div>
			<a href="/" title="LaHMG">
				<img src="/static/img/noun_Map_heavy-colored-lite.png" alt="LaHMG" class="navbar-brand-new">
				&nbsp;&nbsp;
				<strong>Home</strong>
			</a>
		</div>
		<div>
			<a href="/browse" title="Browse">Browse</a>
		</div>
		<div>
			<a href="/people" title="People">People</a>
		</div>
		<div>
			<a href="/#support" title="Support this project">Support</a>
		</div>
		<div>
			<a href="https://about.oldinsurancemaps.net" title="Browse">About <i class="fa fa-external-link"></i></a>
		</div>
	</div>
	<div>
		{#if USER.is_authenticated }
		<div>
			<a href={USER.profile}>{USER.name}</a>
		</div>
		<div>
			<a href="/account/logout">Sign out</a>
		</div>
		{:else}
		<div>
			<a href="/account/login">Sign in</a>
		</div>
		<div>
			<a href="/account/signup">Sign up</a>
		</div>
		{/if}
	</div>
</nav>
