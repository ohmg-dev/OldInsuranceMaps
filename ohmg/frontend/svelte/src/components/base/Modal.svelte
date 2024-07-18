<script context="module" lang="ts">
	let onTop   //keeping track of which open modal is on top
	const modals={}  //all modals get registered here for easy future access
	
	// 	returns an object for the modal specified by `id`, which contains the API functions (`open` and `close` )
	export function getModal(id=''){
		return modals[id]
	}
</script>

<script lang="ts">
import {onDestroy} from 'svelte'

import SvelteMarkdown from 'svelte-markdown';

import '@src/css/ol-overrides.css';
	
let topDiv
let visible=false
let prevOnTop
let closeCallback

export let id=''
export let mdContent = ''
export let full = false

function keyPress(ev){
	//only respond if the current modal is the top one
	if(ev.key=="Escape" && onTop==topDiv) close('') //ESC
}

/**  API **/
function open(callback){
	closeCallback=callback
	if(visible) return
	prevOnTop=onTop
	onTop=topDiv
	window.addEventListener("keydown",keyPress)
	
	//this prevents scrolling of the main window on larger screens
	document.body.style.overflow="hidden" 

	visible=true
	//Move the modal in the DOM to be the last child of <BODY> so that it can be on top of everything
	document.body.appendChild(topDiv)
}
	
function close(retVal){
	if(!visible) return
	window.removeEventListener("keydown",keyPress)
	onTop=prevOnTop
	if(onTop==null) document.body.style.overflow=""
	visible=false
	if(closeCallback) closeCallback(retVal)
}
	
//expose the API
modals[id]={open,close}
	
onDestroy(()=>{
	delete modals[id]
	window.removeEventListener("keydown",keyPress)
})

</script>

<!-- this modal works fine with keyboard interaction, disabling a11y warnings -->
<!-- svelte-ignore a11y-click-events-have-key-events -->
<div id="topModal" class:visible bind:this={topDiv} on:click={()=>close('')}>
	<!-- svelte-ignore a11y-click-events-have-key-events -->
	<div id='modal' class={full ? 'full-modal' : ''} on:click|stopPropagation={()=>{}}>
		<!-- svelte-ignore a11y-click-events-have-key-events -->
		<svg id="close" on:click={()=>close('')} viewBox="0 0 12 12">
			<circle cx=6 cy=6 r=6 />
			<line x1=3 y1=3 x2=9 y2=9 />
			<line x1=9 y1=3 x2=3 y2=9 />
		</svg>
		<div id='modal-content' class={full ? 'full-modal-content' : ''}>
			{#if mdContent}
			<SvelteMarkdown source={mdContent} />
			{:else}
			<slot></slot>
			{/if}
		</div>
	</div>
</div>

<style>
	#topModal {
		visibility: hidden;
		z-index: 9999;
		position: fixed;
		top: 0;
		left: 0;
		right: 0;
		bottom: 0;
		background: #4448;
		display: flex;
		align-items: center;
		justify-content: center;
	}
	#modal {
		position: relative;
		border-radius: 6px;
		border: 2px solid gray;
		background: var(--primary-background-color);
		color: #333333;
		filter: drop-shadow(5px 5px 5px #555);
		padding: 1em;
		margin: 1em;
		max-height: 100vh;
	}

	:global(#modal img) {
		max-height: calc(100vh - 2em);
	}

	.visible {
		visibility: visible !important;
	}

	#close {
		position: absolute;
		top:-12px;
		right:-12px;
		width:24px;
		height:24px;
		cursor: pointer;
		fill:#F44;
		/* transition: transform 0.3s; */
	}	

	#close:hover {
		/* transform: scale(2); */
	}

	#close line {
		stroke:#FFF;
		stroke-width:2;
	}
	#modal-content {
		max-width: calc(100vw - 20px);
		max-height: calc(100vh - 20px);
		overflow: auto;
	}
	.full-modal {
		width: 100%;
		height: calc(100vh - 45px);
	}

	.full-modal-content {
		width: 100%;
		height: 100%;
	}

	/* mimic the .container widths */
	@media (max-width: 767px) {
		#modal-content {
			min-width: unset;
		}
	}
	@media (min-width: 768px) {
		#modal {
			max-width: 700px;
		}
		#modal-content {
			min-width: 500px;
		}
	}
	@media (min-width: 992px) {
		#modal {
			max-width: 700px;
		}
	}
	@media (min-width: 1200px) {
		#modal {
			max-width: 700px;
		}
	}
</style>

