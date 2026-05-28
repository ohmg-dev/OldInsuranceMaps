# Creating an account

All you need to do to begin contributing on _OldInsuranceMaps.net_ is [create an account](https://oldinsurancemaps.net/account/signup/).

## Sign up with email

Choose a **username**, **password**, and valid **email address**. Your username will be publicly visible, so you cannot use your email address as a username.

!!! note 
    You must agree that any contributions you make will be licensed [CC0](https://creativecommons.org/public-domain/cc0/) ("No Rights Reserved"), meaning that your work is effectively in the public domain. See the [Data Agreement](https://oldinsurancemaps.net/data-agreement) for more details about this.

## Sign up via 3rd-party authentication

You can optionally use a 3rd-party identity provider. Currently, only **OpenStreetMap** (OSM) is supported, but more identity providers will be configured in the future.

### Creating a new account

1. On the signup screen, click the OpenStreetMap logo and follow the prompts
    - You will be redirected to `openstreetmap.org` to sign into your OSM account
    - You will need to grant OldInsuranceMaps.net limited privileges on your OSM account
2. You will then be redirected back to OldInsuranceMaps.net to complete the creation of your account
    - Your username will be prepopulated with your OSM username
    - You will still need to enter an e-mail address
    - You will not create a password, because OSM is (effectively) now your password!

Now, whenever you login to OldInsuranceMaps.net, just click the OSM icon and you'll be logged in automatically.

### Link an existing account

If you already have an OldInsuranceMaps.net account, but would like to be able to login with a 3rd-party identity provider, you can easily create a linkage between the accounts.

1. In your OldInsuranceMaps.net account (https://oldinsurancemaps.net/account/), go to **Account Connections**
2. Click the OpenStreetMap logo and follow the prompts
    - You will be redirected to `openstreetmap.org` to sign into your OSM account
    - You will need to grant OldInsuranceMaps.net limited privileges on your OSM account

Now, whenever you login to OldInsuranceMaps.net, just click the OSM icon and you'll be logged in automatically.

### Unlink your account

You can unlink your OIM account with any 3rd-party identity provider at any time&mdash;this has no affect on your OIM account but you will just not be able to login through that provider any more.

To remove a connection to OpenStreetMap you will need to:

1. In your OldInsuranceMaps.net account (https://oldinsurancemaps.net/account/), go to **Account Connections**, select the OSM connection and click **Remove**.
    - If your account does not yet have a password set (which would be the case if you intially created the account through the 3rd-party provider as described above) use the **Change password** form to set a password before trying to remove the connection.
2. In your OpenStreetMap account (https://www.openstreetmap.org/account), go to **OAuth 2 Authorizations** and then click **Revoke Access** for the `OldInsuranceMaps.net` entry.
