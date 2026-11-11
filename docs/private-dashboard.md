# Private dashboard online (Cloudflare Pages + Access)

Use this to see your **real** data from your phone. The site is static (Cloudflare Pages). A
**Cloudflare Access** policy sits in front of it, so only your email can open it, using a one-time code
sent to your inbox or a Google login. Everything here fits in Cloudflare's free plans.

> The bot never uploads private data until you set `LIFELOG_ACCESS_CONFIRMED=1`. Do that only
> after step 4.

## 1. Account and API token
1. Create a free Cloudflare account.
2. **Account ID:** Dashboard → *Workers & Pages* → copy *Account ID* (right column).
3. **API token:** *My Profile* → *API Tokens* → *Create Token* → *Custom token* →
   permission **Account · Cloudflare Pages · Edit** → *Create* → copy it.
4. In `.env`:
   ```
   CLOUDFLARE_ACCOUNT_ID=...
   CLOUDFLARE_API_TOKEN=...
   ```

## 2. Create the (empty) Pages project
```bash
uv run --env-file .env lifelog publish --create
```
This creates `lifelog-private` and then stops with "Refusing to upload private data". That's expected:
nothing is uploaded yet.

## 3. Protect it with Cloudflare Access
1. Dashboard → **Zero Trust**. Pick a team name and the **Free** plan (it may ask for a payment
   method even on the free plan).
2. *Access* → *Applications* → *Add an application* → **Self-hosted**:
   - Name: `Trilhos`
   - Public hostnames: **`lifelog-private.pages.dev`** and **`*.lifelog-private.pages.dev`**.
     Add both: the second covers preview URLs.
   - Session duration: 1 month (so your phone stays logged in).
3. Policy: **Allow** → Include → **Emails** → your email.
4. Login methods: **One-time PIN** works immediately (code sent to your email). To use
   "Sign in with Google", add Google under *Settings → Authentication → Login methods*
   (it needs an OAuth client from the Google Cloud console).

## 4. Check, then confirm
Open `https://lifelog-private.pages.dev` in a private window. You must see the **Cloudflare Access
login**, not the app. Then set in `.env`:
```
LIFELOG_ACCESS_CONFIRMED=1
```

## 5. Publish
```bash
make publish
```
Restart the bot (`make bot-voice`). From now on, every saved message rebuilds and re-uploads the
dashboard in the background, about 30 s later. The open page refreshes itself.

## Cost & teardown
Cloudflare Pages and Zero Trust (up to 50 users) are free. To remove everything:
```bash
cd web && npx wrangler pages project delete lifelog-private
```
Then delete the Access application in Zero Trust, revoke the API token, and remove the `CLOUDFLARE_*`
lines from `.env`.
