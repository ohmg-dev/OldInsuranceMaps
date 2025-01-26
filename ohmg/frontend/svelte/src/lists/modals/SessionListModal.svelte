<script>
    import Modal from "@/base/Modal.svelte";

    export let id;

    let modalContent = `## Activity by sessions

When users complete a step in the georeferencing process, it is stored as a session, either a **Prep** (preparation) session or **Georef** (georeferencing) session. (For now, MultiMask trimming is not stored in sessions.) 

Each session is performed on a specific resource (document, region, or layer) within a map.

This panel allows you to view all sessions that have been performed on _OldInsuranceMaps.net_ since the project began in early 2022. You can filter by **map**, **type**, **date range**, and/or **username** to get a more specific picture of work completed.

Note that this session list appears in more than one place across the platform, so some filter methods and columns are hidden in certain contexts where they would be redundant.

If you are looking for a list of the most recently added items (volumes), go to the [items page](/search#items)</a> and sort the table by **Load date**.`
</script>

<Modal id={id} mdContent={modalContent} />
