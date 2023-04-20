<script>
export let USER;
</script>
<nav class="lahmg-nav">
	<div>
		<div>
			<a href="/" title="LaHMG">
				<img src="/static/img/colored-full-linework.png" alt="LaHMG" class="navbar-brand-new">
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

<style>
nav.lahmg-nav {
	display: flex;
	height: 60px;
	background:#123B4F;
	box-shadow: rgba(0, 0, 0, 0.1) 0px 1px 2px 0px;
    position: fixed;
    top: 0;
    right: 0;
    left: 0;
    z-index: 1030;
    display: flex;
    align-items: center;
    justify-content: space-between;
	padding: 0px 20px;
	color:white;
	font-weight: 500;
	overflow-x: auto;
}

nav.lahmg-nav a {
	color:white;
}

nav.lahmg-nav a:hover {
	color: #eee;
	text-decoration: none;
}

nav.lahmg-nav div {
	display: flex;
	align-items: center;
}

nav.lahmg-nav div div {
	padding: 4px 24px 4px 0px;
	white-space: nowrap;
}

.navbar-brand-new {
	height: 45px;
}
</style>
