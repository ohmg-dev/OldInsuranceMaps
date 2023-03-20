import './css/interface.css';
import InfoPanel from './InfoPanel.svelte';

const app = new InfoPanel({
	target: document.getElementById("infopanel-target"),
	props: JSON.parse(document.getElementById("infopanel-props").textContent),
});

export default app;
