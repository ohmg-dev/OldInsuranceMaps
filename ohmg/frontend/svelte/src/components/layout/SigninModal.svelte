<script>
    import Modal from '@components/base/Modal.svelte';
    import Link from '@components/base/Link.svelte';

    export let csrfToken;
    export let showForm = "signin";

    const currentUrl = window.location.href;
    let agreementCheck = true;
</script>

<Modal id="signin-modal">
    {#if showForm == "signin"}
    <h2>Sign in</h2>
    <p>If you have not yet created an account, then please <button class="is-text-link" on:click={() => {showForm = 'signup'}}>sign up</button> first.</p>
    <form class="login" method="POST" action="/account/login/">
        <input type="hidden" name="csrfmiddlewaretoken" value={csrfToken}>
        <input type="hidden" name="next" value={currentUrl}>
        <p><label for="id_login">Username:</label> <input type="text" name="login" placeholder="Username" autocomplete="username" maxlength="150" required="" id="id_login"></p>
        <p><label for="id_password">Password:</label> <input type="password" name="password" placeholder="Password" autocomplete="current-password" required="" id="id_password"></p>
        <p><label for="id_remember">Remember me:</label> <input type="checkbox" name="remember" id="id_remember"> | <Link href="/account/password/reset/">Forgot Password?</Link></p>
        <button class="button is-primary" type="submit">Sign In</button>
    </form>
    {:else if showForm == 'signup'}
    <h2>Sign up</h2>
    <p>If you already have an account, please <button class="is-text-link" on:click={() => {showForm = 'signin'}}>sign in</button>.</p>
    <form id="signup_form" method="post" action="/account/signup/">
        <input type="hidden" name="csrfmiddlewaretoken" value={csrfToken}>
        <p><label for="id_username">Username:</label> <input type="text" name="username" placeholder="Username" autocomplete="username" minlength="1" maxlength="150" required="" id="id_username"></p>
        <p><label for="id_email">E-mail:</label> <input type="email" name="email" placeholder="E-mail address" autocomplete="email" required="" id="id_email"></p>
        <p><label for="id_password1">Password:</label> <input type="password" name="password1" placeholder="Password" autocomplete="new-password" required="" id="id_password1"></p>
        <p><label for="id_password2">Password (again):</label> <input type="password" name="password2" placeholder="Password (again)" autocomplete="new-password" required="" id="id_password2"></p>
        <!-- <p><label style="width:100%;"> I understand that all work I perform on this site will be licensed <a href="https://creativecommons.org/licenses/by/4.0/deed.en">CC BY 4.0</a>.<input type="checkbox" bind:value={agreementCheck} /></label></p> -->
        <button class="button is-primary" type="submit" disabled={!agreementCheck}>Sign Up</button>
    </form>
    {/if}
</Modal>

<style>
    form {
        display: flex;
        flex-direction: column;
    }
    label {
        width: 150px;
        display: inline-block;
        text-align: right;
    }
</style>