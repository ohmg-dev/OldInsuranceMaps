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
  <div class="info-bar">
    <span>Check: Does this image need to be split before it can be georeferenced?</span>
    <div>
      <a href="#" on:click={() => setPanel("background")}>More info &darr;</a>
      <a href="#" on:click={() => setPanel("guide")}>Guide &darr;</a>
      <a href="#" on:click={() => setPanel("tips")}>Tips &darr;</a>
      <a href="#" on:click={() => setPanel("video")}>Just show me! &darr;</a>
    </div>
  </div>
  {#if showBackground}
  <div transition:slide class="help-panel">
    <h4><strong>Background</strong> <a href="#" on:click={() => setPanel("none")}><i class="fa fa-close"></i></a></h4>
    <p>Sometimes an old map document will cover discontiguous areas, especially when the mapmakers were trying to 
      fit a lot of content into a single page. In these cases, each separate area in the original document must be split into
      its own new document, so that each area can be georeferenced on its own. Typically, you'll find
      <strong>strong black lines</strong> delineating different parts of the map. The document must be split along those lines.
    </p>
    <div style="display:flex; flex-direction:row;">
        <figure style="width:33%; padding:10px; text-align:center;">
            <img width="100%" src="/static/img/split-example-p1-anno.jpg" />
            <figcaption>This map must be split into four new documents.</figcaption>
        </figure>
        <figure style="width:33%; padding:10px; text-align:center;">
            <img width="100%" src="/static/img/split-example-p2-anno.jpg" />
            <figcaption>This map must be split into two new documents.</figcaption>
        </figure>
        <figure style="width:33%; padding:10px; text-align:center;">
            <img width="100%" src="/static/img/split-example-p3-anno.jpg" />
            <figcaption>This map shows only one part of town, so it should not be split.</figcaption>
        </figure>
    </div>
    <hr>
    <p><em>
        Note: This evaluation is a very important initial step that should only be done once,
        so if you want to skip this step and jump right into georeferencing, start with documents
        that are already prepared.
        </em>
    </p>
  </div>
  {/if}
  {#if showGuide}
  <div transition:slide class="help-panel">
    <h4><strong>Using the Interface</strong></h4>
    <p>If this document <strong>does not</strong> to be split:</p>
    <ul>
        <li>Click <code>No Split Needed</code>.</li>
        <li>You will be redirected to the document detail page, from which you can continue the georeferencing process.</li>
        <li>If you chose this by mistake, you can undo the designation in the document detail page.</li>
    </ul>
    <p>If this document <strong>does</strong> need to be split</p>
    <ul>
        <li>Use the interface to create as many cut-lines as are needed to fully split this document.</li>
        <li>Once you have one or more valid cut-lines, a preview will appear showing how the image will be split.</li>
        <li>Click <code>Split</code> when you are ready.</li>
        <li>You will be redirected to the document detail page, while the split process runs in the background.</li>
        <li>If you split the document incorrectly, you can undo the process in the document detail page.</li>
    </ul>
    <p>Fixing an incorrect determination:</p>
    <ul>
        <li>In the document detail page, you can undo this operation as long no georeferencing has been performed.</li>
        <li>Look for the undo <i class="fa fa-undo"></i> button under the <code>Preparation</code> heading.</li>
        <li>If the button is disabled but you believe the split process was performed incorrectly, please contact an admin.</li>
    </ul>
    <p>Creating cut-lines:</p>
    <ul>
        <li>In <code>Draw</code> mode, click once to start or continue a line, and double-click to finish it.</li>
        <li>Press <code>Esc</code> to cancel an in-progress drawing.</li>
        <li>Switch to <code>Modify</code> mode to change a cut-line.</li>
        <li>Click <i class="fa fa-refresh"></i> to erase all lines and start over.</li>
    </ul>
    <p>Understanding cut-lines:</p>
    <ul>
        <li>Once you have a valid cut-line, a preview will appear showing you how the document will be split.</li>
        <li>Only cut-lines that fully cross a segment of the document will be used&mdash;all others will safely be ignored.</li>
        <li>Cut-lines can intersect or extend from each other to handle complex shapes.</li>
    </ul>
  </div>
  {/if}
  {#if showTips}
  <div transition:slide class="help-panel">
    <h4><strong>Tips</strong></h4>
    <ul>
      <li>Use <code>Esc</code> to abort a line you are in the middle of drawing.</li>
      <li>You don't need to be exact with where the lines end: they can extend across the border of the image.</li>
    </ul>
  </div>
  {/if}
  {#if showVideo}
  <div transition:slide class="help-panel">
    <a href="https://youtu.be/GpAdj3hymkA?t=824" target="_blank"><h4>View <i class="fa fa-external-link"></i></h4></a>
  </div>
  {/if}
</main>

<style>

main {
  display: flex;
  flex-direction: column;
  border-radius: 5px;
  margin-bottom: 10px;
}

figcaption {
  font-style: italic;
  font-size: .85em;
}

.info-bar {
  display:flex;
  justify-content: space-between;
  font-size: 1.2em;
}

.help-panel {
  font-size: 1.25em;
  border-radius: 7px;
  background: lightgrey;
  padding: 0px 15px 15px 15px;
  margin-bottom: 20px;
}

</style>
