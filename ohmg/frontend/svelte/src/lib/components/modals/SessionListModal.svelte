<script>
    import Modal from "./Base.svelte";

    export let id;

    let modalContent = `When contributors complete a step in the georeferencing process, it is stored as a session, either a "preparation" session (P) or "georeference" sessions (G). (MultiMask trimming is not stored in sessions, for now.)

If you are looking for a list of the most recently added items (volumes), go to the [items page](/search#items)</a> and sort the table by **Load date**.

*More sophisticated filter and sort capabilities for this list are in the works. This data is also accessible via the [beta API](/api/beta/docs). Please [get in touch](/contact) if you would like a key for the API.*`
</script>

<Modal id={id} mdContent={modalContent} />
