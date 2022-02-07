<script>
import { slide } from 'svelte/transition';

let showBackground = false;
let showGuide = false;
let showVideo = false;
let showTips = false;

function setPanel(show) {

  if (show == "background") {
    showBackground = !showBackground;
    showGuide = false;
    showTips = false;
    showVideo = false;
  } else if (show == "guide") {
    showBackground = false;
    showGuide = !showGuide;
    showTips = false;
    showVideo = false;
  } else if (show == "tips") {
    showBackground = false;
    showGuide = false;
    showTips = !showTips;
    showVideo = false;
  } else if (show == "video") {
    showBackground = false;
    showGuide = false;
    showTips = false;
    showVideo = !showVideo;
  } else if (show == "none") {
    showBackground = false;
    showGuide = false;
    showTips = false;
    showVideo = false;
  }
}

</script>

<main>
  <h4>Create a mask to trim the edges of this layer.</h4>
  <h4>
      <a href="#" on:click={() => setPanel("background")}>Background &darr;</a>
      <a href="#" on:click={() => setPanel("guide")}>Guide &darr;</a>
      <a href="#" on:click={() => setPanel("tips")}>Tips &darr;</a>
      <a href="#" on:click={() => setPanel("video")}>Video &darr;</a>
      {#if showGuide || showVideo || showTips || showBackground}
        &nbsp;
        <a href="#" on:click={() => setPanel("none")}><i class="fa fa-close"></i></a>
      {/if}
  </h4>
  {#if showBackground}
  <div transition:slide class="help-panel">
    <h4><strong>Background</strong></h4>
    <p>To use our georeferenced layers most effectively, we can combine them in web maps to create a seamless mosaic. However, this often causes adjacent images to overlap and obscure each other. Consider the example below, where the layer on the left covers up the edge of the layer on the right.</p>
    <figure style="padding:10px; text-align:center;">
      <img width="100%" src="/static/img/alex-untrim-example.jpg" />
      <figcaption>Two georeferenced layers are shown on top of an aerial imagery basemap. The left layer overlaps the right layer.</figcaption>
    </figure>
    <p>To reduce this overlap, we can trim the edges of the left layer by creating a mask. This is just a shape that will cause everything outside of it to be clipped away. The result can look like this:</p>
    <figure style="padding:10px; text-align:center;">
      <img width="100%" src="/static/img/alex-trim-example.jpg" />
      <figcaption>The left layer has been trimmed to create a seamless mosaic.</figcaption>
    </figure>
    <p>The mask polygon is stored as a new trim style for the layer, and set as the default style. The layer itself is not changed, however, so don't worry about altering any underlying data through this process.</p>
  </div>
  {/if}
  {#if showGuide}
  <div transition:slide class="help-panel">
    <h4><strong>Using the Interface</strong></h4>
    <p>Creating a new mask:</p>
    <ul>
      <li>Click on a corner of the layer to begin creating the polygon.</li>
      <li>Click again at each corner to continue.</li>
      <li>Double-click on the final corner to finish the polygon.</li>
      <li>The layer will be automatically be clipped when the polygon is finished.</li>
    </ul>
    <p>Adjusting the mask:</p>
    <ul>
      <li>Click and drag anywhere on the polygon to modify it.</li>
      <li>Click <i class="fa fa-refresh" title="Reset interface"></i> to reset the polygon.</li>
    </ul>
    <p>Altering an existing mask:</p>
    <ul>
      <li>If someone else has already created a mask for this layer, but it needs to be changed, go for it&mdash;this is meant to be an iterative process.</li>
      <li>Click <i class="fa fa-refresh" title="Reset interface"></i> to restore the mask to how you found it.</li>
      <li>Click <i class="fa fa-trash" title="Remove mask"></i> to remove the mask altogether from this layer.</li>
    </ul>
  </div>
  {/if}
  {#if showTips}
  <div transition:slide class="help-panel">
    <h4><strong>Tips</strong></h4>
    <ul>
      <li>It may be easiest to outline the layer first and then zoom in to make more subtle changes.</li>
      <li>The live clipping preview may leave some extraneous piece of the layer outside the mask. You can disregard this.</li>
      <li>When viewing a trimmed layer in a Web Map you may see a <code style="color:red;">!</code> next to the layer name. This can be ignored.</li>
    </ul>
  </div>
  {/if}
  {#if showVideo}
  <div transition:slide class="help-panel">
    <h4><em>coming soon!</em></h4>
  </div>
  {/if}
</main>

<style>

main {
  display: flex;
  flex-direction: column;
}

figcaption {
  font-style: italic;
  font-size: .85em;
}

.help-panel {
  font-size: 1.25em;
  background: lightgray;
  border-radius: 7px;
  padding: 20px;
  margin-top: 20px;
  margin-bottom: 20px;
}

</style>
