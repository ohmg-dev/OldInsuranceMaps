<script>
    export let newCol = false;
    export let numCol = false;
    export let tsCol = false;
    export let title = ""

    let classes = []
    if (newCol) {classes.push("new-col")}
    if (numCol) {classes.push("num-col")}
    if (tsCol) {classes.push("ts-col")}

    const attrs = {}
    if (classes) {attrs.class = classes.join(" ")}
    if (title) {attrs.title = title}
</script>

<td {...attrs}>
    <slot/>
</td>