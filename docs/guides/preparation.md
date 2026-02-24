# Preparing documents

## Background

Sometimes an old map document will cover discontiguous areas, especially when the mapmakers were trying to
fit a lot of content into a single page. In these cases, each separate area in the original document must be split into
its own new region, so that each area can be georeferenced separately. Typically, you'll find
**strong black lines** delineating different parts of the map. The document must be split along those lines.

<div markdown="span" style="display:flex; flex-direction:row;">
	<figure markdown="span" style="width:33%; padding:5px;">
		![This map must be split into four new documents.](../images/split-example-p1-anno.jpg)
		<figcaption>This map must be split into four new documents.</figcaption>
	</figure>
	<figure markdown="span" style="width:33%; padding:5px;">
		![This map must be split into two new documents.](../images/split-example-p2-anno.jpg)
		<figcaption>This map must be split into two new documents.</figcaption>
	</figure>
	<figure markdown="span" style="width:33%; padding:5px;">
		![This map shows only one part of town, so it should not be split.](../images/split-example-p3-anno.jpg)
		<figcaption>This map shows only one part of town, so it should not be split.</figcaption>
	</figure>
</div>

The examples above show two documents that need to be split, and one that contains only one map and does not need to be split.

## No split needed

For documents that do not need to be split, you need only click the **no split needed** button, and the document will be prepared. If there are many documents like this within the map you are working on, you can click the **Bulk prepare documents** button, check the box for each document you want to process, and click submit.

![Three documents to be prepared, showing the buttons for marking "no split" and "split" actions](../images/new-iberia-to-prepare.png)

## Using the splitting interface

If a document needs to be in order to be prepared, then click the **split this document** button, and you'll be taken to the splitting interface.

Here is an example of what it looks like to use the splitting interface to cut a document into three separate regions. *It is kind of a sloppy example, please be a bit more exact that this if you can!*

![The splitting interface, ready to split this document into three new documents.](../images/alex-split.gif)

### Defining the split regions

- Use the interface to create as many cut-lines as are needed to fully split this document.
- Once you have one or more valid cut-lines, a preview will appear showing how the image will be split.
- Click the scissors icon when you are ready.
- You will be redirected to the map overview page, while the split process runs in the background.
- If you split the document incorrectly, you can undo the process from the map summary page.

### Creating cut-lines

- In **Draw** mode, click once to start or continue a line, and double-click to finish it.
- Press **Esc** to cancel an in-progress drawing.
- Switch to **Modify** mode to change a cut-line.
- Click the "refresh" button to erase all lines and start over.

Understanding cut-lines:

- Once you have a valid cut-line, a preview will appear showing you how the document will be split.
- Only cut-lines that fully cross a segment of the document will be used&mdash;all others will safely be ignored.
- Cut-lines can intersect or extend from each other to handle complex shapes.
