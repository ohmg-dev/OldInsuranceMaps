<script>
    import SigninModal from "./SigninModal.svelte";
    import OpenModalButton from "../base/OpenModalButton.svelte";

    export let csrfToken;
</script>

<SigninModal {csrfToken} />
<div class="signin-reminder">
    <p><em>
        <OpenModalButton modalId="signin-modal" style="link" icon="none"><em>sign in</em></OpenModalButton> to work on this content
    </em></p>
</div>

<style>
    .signin-reminder {
        background: #e6e6e6;
        text-align: center;
        padding: 5px;
        margin: 5px;
        border-radius: 4px;
    }

    .signin-reminder p {
        margin: 0px;
    }
</style>