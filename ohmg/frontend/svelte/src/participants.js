import './css/interface.css';
import Participants from './components/lists/Participants.svelte';

export default new Participants({
  target: document.getElementById('participants-target'),
  props: JSON.parse(document.getElementById('participants-props').textContent),
});
