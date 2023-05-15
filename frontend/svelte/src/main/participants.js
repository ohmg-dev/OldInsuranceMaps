import '../css/shared.css';
import Participants from './Participants.svelte';

const participants = new Participants({
	target: document.getElementById("participants-target"),
	props: JSON.parse(document.getElementById("participants-props").textContent),
});

export default participants;