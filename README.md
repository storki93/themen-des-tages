# Themen des Tages podcast RSS

An independent RSS generator for NDR Info's **Themen des Tages** on ARD Sounds. Audio stays on ARD servers. This deliberately does not use podcast2986.xml, which currently serves the different show **Das Thema**.

## Publish on GitHub

1. Create a public repository named `themen-des-tages` with default branch `main` and upload the contents of this folder, including `.github/workflows/refresh.yml`.
2. In **Settings → Pages → Build and deployment → Source**, choose **GitHub Actions**.
3. In **Actions → Refresh podcast RSS**, run the workflow. If the initial push ran before Pages was configured, rerun it.
4. The workflow's deployment URL is the homepage. Append `feed.xml` to that URL and paste it into your podcast app.

Typical URL: `https://YOUR-USERNAME.github.io/themen-des-tages/feed.xml` (an example, not a deployed feed).

The workflow checks hourly at minute 17, and can also be run manually. GitHub may delay scheduled runs; podcast apps poll on their own schedule. For public repositories GitHub disables scheduled workflows after 60 days without repository activity. New episode commits normally keep this repository active; if publication pauses, check and re-enable the workflow.

## Behavior

- Reads embedded ARD episode metadata from the exact requested show.
- Links direct MP3 audio enclosures, with titles, descriptions, dates, stable IDs, and durations.
- Persists all encountered episodes in `episodes.json`; ARD's initial page provides the latest 12, not the entire historical catalog.
- Retains older entries even when they leave ARD's first page. Availability of old audio remains controlled by ARD.
- Fails without overwriting the feed if the page metadata disappears or the show changes. Review failed Actions runs if ARD changes its website.
- Uses only Python's standard library: `python generate_feed.py`.

A local `docs/feed.xml` is a snapshot. Automatic refresh starts only after publishing and enabling the GitHub workflow.
