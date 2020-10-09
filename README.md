# Webauth

## Background 

This project demonstrates how to utilize identity providers on the web for
authentication, on devices which is not itself a web service. Instead of
asking a user for a password when logging into a computer it's
possible to exploit that a user can authenticate with Google, Facebook,
or other identity providers over the web. Using single sign-on reduces
the amount of passwords to manage, for both users and system administrators.

## Overview

This project utilizes OpenID to delegate user authentications, instead of depend
on local identity and credential databases. Below is a typical use case:

1. A user logging into the webauth server using a 3rd party identity provider,
   example Google and establishes a web session.
2. When the user login on a computer the authentication is dispatched over
   to the web session, instead of locally prompting for a password.
3. The user get notified over the authenticated web session and can choose
   to approve or reject the request.

Using a web-service for authenticate other devices has the advantage of being
agnostic. You can use any device with a web-browser available to authenticate. 
Even if the authentication is dispatched over the web it's still required
to physically be present near the computer where a user request to login, which
makes this authentication flow resistant for phishing.

*During the development i've preliminary targeted linux machines, see project
<https://github.com/1nfiniteloop/pam-http>. This server could certainly work
with any device with some other plugin on the client-side.


Below is an overview of the authorization flow: 

```text
     ┌──────┐                               ┌───────┐                                                        ┌──────────┐
     │Device│                               │Webauth│                                                        │Webbrowser│
     └──┬───┘                               └───┬───┘                                                        └────┬─────┘
        │HTTP POST "service", "unix_account_id"┌┴┐                                                                │      
        │ ────────────────────────────────────>│ │                                                                │      
        │                                      │ │                                                                │      
        │                                      │ │────┐                                                           │      
        │                                      │ │    │ Get "CommonName" in client certificate which is "host_id" │      
        │                                      │ │<───┘                                                           │      
        │                                      │ │                                                                │      
        │                                      │ │────┐                                                           │      
        │                                      │ │    │ Check Host and Unix account exist in database             │      
        │                                      │ │<───┘                                                           │      
        │                                      │ │                                                                │      
        │                                      │ │────┐                                                           │      
        │                                      │ │    │ User web session exist                                    │      
        │                                      │ │<───┘                                                           │      
        │                                      │ │                                                                │      
        │                                      │ │                     authorization request                      │      
        │                                      │ │ ──────────────────────────────────────────────────────────────>│      
        │                                      │ │                                                                │      
        │                                      │ │                   AUTHORIZED | UNAUTHORIZED                    │      
        │                                      │ │ <─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ │      
        │                                      │ │                                                                │      
        │      200 OK | 401 UNAUTHORIZED       │ │                                                                │      
        │ <─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ │ │                                                                │      
     ┌──┴───┐                               ┌──└┬┘──┐                                                        ┌────┴─────┐
     │Device│                               │Webauth│                                                        │Webbrowser│
     └──────┘                               └───────┘                                                        └──────────┘
```

The authentication request is a simple HTTP POST request over a separate
back-channel. The server has different servers (ports) between the user API
and the back-channel. The HTTP request hangs until the user has responded, or
until a timeout occurs. An approved request is simply status code 200. Status
codes different from 200 is either timeouts, errors or access denied. The
endpoint uses ssl client certificate to mutually authenticate both server and
client host. The "CommonName" in the client certificate is used as "host id"
in webauth.

The authorization request is dispatced over an authenticated websocket to the
user.

### Build

The server is written in Python and deployed using a Docker container. A
few steps is needed to build and get the service ready, see below:

* Build the container with: `docker build --tag webauth-server:latest .`
* Create the container according to below. This command doesn't start the
  container since some configuration is needed first.
  ```bash
  docker create \
      -it \
      --name=webauth-server \
      --volume=webauth-server:/mnt/webauth \
      --publish 0.0.0.0:8099:8099 \
      --publish 0.0.0.0:8443:8443 \
      webauth-server:latest
  ```

### Configure identity provider(s)

The first thing needed is to configure an external identity provider
supporting OpenID Connect. Google and Keycloak is currently supported in
webauth. You need `client_id`, `client_secret` and `well_known` discovery
address, see section `openid_provider` in configuration file.

#### Keycloak

Keycloak documentation is scattered and a difficult to navigat through. Below 
summarizes the steps you need to perform for hosting your own identity provider
with keycloak:

* Create a new "realm".
* Create a new "Client", which is a "service" endpoint used to handle OpenID 
  authentications in webauth.
* On your newly created "Client":
  - Configure a "valid redirect URI" and "Base URL".
  - Under tab "Settings" you find the "Client ID" which is "client_id"
    in `config.yaml`.
  - Under tab "Credentials" you find the "Secret" which is "client_secret"
    in `config.yaml`. 

See more @ <https://www.keycloak.org/documentation.html>.

#### Google

See more @ <https://developers.google.com/identity/protocols/OpenIDConnect>.

### Configure webauth server

The configuration parameters in `webserver`: 

* `external_url` needs to be accordingly. 
* `cookie_secret` is used when signing cookies and shall be a random value.
  You can generate a random value using python with
  `import uuid; print(uuid.uuid4().hex)`.

#### SSL certificates

SSl-certificates needs to be created which is out of scope of this instruction.
See more @ <https://github.com/1nfiniteloop/easy-ca> which is another project
for easily managing ssl-certificates. After the certificate is generated copy
them into the persistent docker volume with: 
`docker cp *.pem webauth-server:/mnt/webauth/certs`.

#### Configure initial users

You need at least to configure an initial administrator user, see `bootstrap`
in `config.yaml`. You can also create other objects since the administration
API isn't available in the frontend-mockup. 

Copy the configuration file into persistent docker volume with:
`docker cp config/config.yaml webauth-server:/mnt/webauth/config`.

### Run

Start the container with : `docker start --attach webauth-server`. On first
start you will see a registration link where you can register and associate
an identity for the user(s).

If you need to alter the configuration or reset the database storage, you
can reach the docker persistent volume with another container with:
`docker run --rm -it -v  webauth-server:/mnt alpine:3.10`.

### API

#### Frontend

The frontend is available @ "https://${HOSTNAME}:8443/". You can login, logout
and authorize requests.

#### Authorization endpoint

This endpoint is dependent on client certificates and runs on port `8099`. It's
important to configure the certificates since the host identity is taken from
the client certifate's "Common Name". A host and unix-account must exist in the
webauth server. Unix account authorization requests can be tested with curl:

```
curl \
    --include \
    --request POST \
    --data "unix_account_id=1000&service=login" \
    --cacert certs/ca-chain.cert.pem \
    --cert certs/client.cert.pem \
    --key certs/client.key.pem \
    https://${HOSTNAME}:8099/api/unix_account/authorize
```

#### Administration

Webauth has HTTP REST API's for managing:

* User accounts
* Unix accounts
* Hosts

The frontend has currently not this API implemented, but example `curl` can be
used to reach the endpoints. Since you need to be authenticated as administrator
when using these endpoints the example configuration contains a user called
"curl-cli". You need to first fetch the session cookie using the registration
link for user `curl-cli`.
  
1. Get the registration link and use `curl` to bootstrap the user account
   and get the session cookie:
   ```
   curl \
       --include \
       --request GET \
       --location \
       --cookie \
       --cookie-jar ~/tmp/${HOSTNAME}.session \
       "http://${HOSTNAME}:8443/user_account/bootstrap/98973ce45cce4e86b29cf4ae78b6af8e?next=%2F"
   ```
2. Endpoints for HTTP GET:
   ```
   curl \
       --request GET \
       --silent \
       --show-error \
       --cookie ~/tmp/${HOSTNAME}.session \
       "http://${HOSTNAME}:8443/api/admin/{hosts,user_accounts,unix_accounts}"
   ```
