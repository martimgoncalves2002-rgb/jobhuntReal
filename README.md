# JobHunt on GitHub — beginner setup guide

You'll end up with a free robot that, every morning on its own:
1. checks London finance jobs (Adzuna + company career pages),
2. emails you only the **new** ones, and
3. updates a webpage you can bookmark.

No coding and nothing installed on your laptop. Follow the parts in order.
Each "→" is a click. Takes about 20 minutes the first time.

---

## Part A — Make an account and a repository

1. Go to **github.com** → **Sign up** (free). Verify your email.
2. Top-right **+** → **New repository**.
3. Repository name: `jobhunt` (anything is fine).
4. Choose **Public** (free unlimited automation; no secrets live in the files).
5. Leave everything else default → **Create repository**.

You now have an empty repo page open. Keep it open.

---

## Part B — Add the files

You're uploading the files I gave you, plus creating one file by hand.

### B1. Upload the main files
1. On the repo page → **Add file** → **Upload files**.
2. Drag in these files from the `jobhunt-gh` folder:
   `jobhunt.py`, `sources.py`, `filters.py`, `notify.py`,
   `config.yaml`, `requirements.txt`, `README.md`
3. Scroll down → green **Commit changes**.

### B2. Create the schedule file by hand
The robot's instructions live in a special folder. Easiest to type the path:
1. **Add file** → **Create new file**.
2. In the name box type exactly:
   `.github/workflows/jobhunt.yml`
   (the slashes auto-create the folders)
3. Open the `jobhunt.yml` I gave you, copy ALL of it, paste it in the box.
4. **Commit changes**.

---

## Part C — Add your secrets (keys & password)

These are stored encrypted and never appear in your files.

First, get the two things you need:
- **Adzuna keys** — register free at https://developer.adzuna.com/ , copy your
  `app_id` and `app_key`.
- **Gmail App Password** — turn on 2-Step Verification on your Google account,
  then go to https://myaccount.google.com/apppasswords , create one, copy the
  16-character code (this is NOT your normal Gmail password).

Now add them:
1. Repo → **Settings** (top tab) → left menu **Secrets and variables** → **Actions**.
2. **New repository secret**, add each of these (Name must match exactly):

   | Name | Value |
   |------|-------|
   | `ADZUNA_APP_ID` | your Adzuna app id |
   | `ADZUNA_APP_KEY` | your Adzuna app key |
   | `EMAIL_USERNAME` | your full Gmail address |
   | `EMAIL_PASSWORD` | the 16-char app password |
   | `EMAIL_TO` | where to send the digest (your email) |

---

## Part D — Test it now

1. Repo → **Actions** tab. If it asks to enable workflows, click to enable.
2. Click **JobHunt daily** in the left list → **Run workflow** → **Run workflow**.
3. Wait ~1 minute, refresh. A green check = success. Click the run to see logs
   (you'll see how many jobs it found). Check your email for the digest.

If something's red, open the run, click the failed step to read the error.
Most first-time errors are a mistyped secret name or a missing config value.

---

## Part E — Turn on the webpage (optional but nice)

1. Repo → **Settings** → left menu **Pages**.
2. Under **Source** choose **Deploy from a branch**.
3. Branch: **main**, folder: **/ (root)** → **Save**.
4. Wait a minute or two. Your dashboard appears at:
   `https://YOUR-USERNAME.github.io/jobhunt/`
   Bookmark it. It refreshes itself after each daily run.

---

## Part F — Make it yours

Open `config.yaml` in the repo and click the **pencil** to edit in the browser:
- Add the companies you're targeting under `greenhouse / lever / ashby`
  (find the slug in their careers URL — see the comments in the file).
- Adjust the Adzuna `queries` and the `filter` keywords.
- Raise `min_score` if you get too much; lower it if you get too little.
- **Commit changes** to save. The next run uses your edits.

It now runs every morning at ~8am Lisbon time automatically. To change the
time, edit the `cron` line in `.github/workflows/jobhunt.yml` (it's in UTC).

---

## Good to know
- **Cost:** free. Public repos get unlimited Actions minutes.
- **Inactivity:** GitHub pauses schedules after ~60 days of no repo activity —
  but this robot commits its results daily, which counts as activity, so it
  keeps itself alive.
- **Don't get spammed twice:** the `seen.json` file remembers what you've been
  shown. Delete it in the repo to reset and treat everything as new again.
- **Pair it with free alerts:** also set a saved LinkedIn job alert and an
  eFinancialCareers alert. The big banks use Workday (no public feed), so those
  alerts cover what the robot can't reach.
