import Footer from '@components/shared/Footer.svelte';

const footer = new Footer({
	target: document.getElementById("footer-target"),
	props: JSON.parse(document.getElementById("footer-props").textContent),
});

export default footer;