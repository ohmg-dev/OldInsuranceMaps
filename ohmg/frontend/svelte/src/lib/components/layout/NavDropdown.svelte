<script>
	import IconContext from 'phosphor-svelte/lib/IconContext';
    import { iconProps } from "@helpers/utils"
    import ArrowSquareOut from "phosphor-svelte/lib/ArrowSquareOut";

    export let LINKS;
	export let RIGHT_POS = null;
</script>

<IconContext values={iconProps}>
<div class="dropdown" style={RIGHT_POS != null ? "right:"+RIGHT_POS : ""}>
    {#each LINKS as link}
	{#if link.href}
    <a href={link.href} target={link.external ? "_blank" : ""}>{link.title}{#if link.external} <ArrowSquareOut />{/if}</a>
	{:else}
    <span>{link.title}</span>
	{/if}
    {/each}
</div>
</IconContext>

<style>
.dropdown {
	display: flex;
	flex-direction: column;
	align-items: baseline;
	position:fixed;
	top: 60px;
	background: #123B4F;
	padding: 10px 15px;
}
.dropdown a {
	color: white;
	margin: 2px 0px;
}

@media (max-width: 760px) {
	.dropdown {
		width: 100%;
		left: 0;
	}
}
</style>