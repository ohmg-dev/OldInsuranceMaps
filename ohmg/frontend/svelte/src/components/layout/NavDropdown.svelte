<script>
	import Link from '@components/base/Link.svelte';

    export let LINKS;
	export let RIGHT_POS = null;
</script>

<div class="dropdown" style={RIGHT_POS != null ? "right:"+RIGHT_POS : ""}>
    {#each LINKS as link}
	{#if link.href}
    <Link href={link.href} external={link.external} classes={["white"]} title={link.title}>{link.title}</Link>
	{:else}
    <span>{link.title}</span>
	{/if}
    {/each}
</div>

<style>
.dropdown {
	display: flex;
	flex-direction: column;
	align-items: baseline;
	position:fixed;
	top: 40px;
	background: #123B4F;
	padding: 10px 15px;
}

@media (max-width: 760px) {
	.dropdown {
		width: 100%;
		left: 0;
	}
}
</style>