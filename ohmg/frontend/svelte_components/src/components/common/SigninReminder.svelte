<script>
  export let msg;
  export let next;
</script>

<div class="notification is-light signin-reminder">
  <em>
    <a href={`/account/login/${next ? '?next=' + next : ''}`}>Sign in</a> or <a href="/account/signup">sign up</a> to work on
    this content.{msg ? ` ${msg}` : ""}</em>
</div>

<style>
  .signin-reminder {
    text-align: center;
    padding: 5px;
    margin: 5px;
    border-radius: 4px;
  }
</style>
