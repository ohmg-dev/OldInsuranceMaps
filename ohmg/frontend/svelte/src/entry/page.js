import Page from '../lib/Page.svelte';

export default new Page({
	target: document.getElementById("page-target"),
	props: JSON.parse(document.getElementById("page-props").textContent),
});