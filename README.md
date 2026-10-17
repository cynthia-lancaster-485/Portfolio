# Django Grading App

A course gradebook where students upload PDF assignments, teaching assistants grade them, and an instructor oversees everything. I built it in Python and Django over a semester in CS 3550 (Web Software Development I) at the University of Utah, deployed it to AWS, and later came back to fix bugs and add automated tests.

**Stack:** Python, Django 5, SQLite, Django templates, JavaScript (ES modules), jQuery, HTML, CSS
**Originally deployed on:** AWS EC2 (Ubuntu), NGINX reverse proxy, custom domain, HTTPS with Let's Encrypt

<!-- Add screenshots here, for example:
![Student gradebook with the what if calculator](docs/profile.png)
![TA grading page with validation errors](docs/grading.png)
-->

## What it does

**Three roles, three experiences**
- **Students** see every assignment, upload a PDF before the deadline, and track their grades with a live weighted final grade.
- **TAs** see only the submissions assigned to them and enter grades in a single form.
- **The instructor (admin)** sees every submission and overall grading progress.

**Highlights**
- **Fair TA assignment:** each new submission goes to the TA with the fewest submissions for that assignment, chosen in a single database query (`annotate` + `Count`).
- **Weighted grading:** graded work counts its percentage times its weight, missing work counts as zero, and ungraded or not yet due work is left out.
- **"What if" calculator:** students can type hypothetical scores for ungraded work and watch their final grade update as they type.
- **Accessible sortable tables:** click or press Enter on a column header to sort ascending, descending, then back to the original order. Headers expose `aria-sort` and `role="button"` for screen readers.
- **Asynchronous uploads:** submissions upload with AJAX, the form disables while uploading, and errors from the server appear inline.

## Security

Security rules live in one place, the `Submission` model, so every view enforces them the same way.

- `change_grade()` only lets the assigned TA (or the admin) change a grade, even if someone crafts their own POST request.
- `view_submission()` only lets the author, the assigned TA, or the admin download a file. Everyone else gets a 403.
- Uploads must be PDFs: the file name must end in `.pdf` **and** the file must start with the `%PDF-` signature. The size limit (64 MiB) is checked before the file is read. Files are checked again when they are downloaded, and served as attachments with an explicit `Content-Type`.
- Every page requires login. After logging in, the `next` redirect is only followed if it points back to this site, which prevents open redirects.
- Grade input is validated on the server (numbers only, within the assignment's point range, real submission IDs for this assignment). Valid grades are saved and invalid ones are reported next to the right row.
- CSRF protection on every form, including the AJAX upload.
- Secrets and deployment settings come from environment variables, not the code.

## Run it locally

You need Python 3.11 or newer.

```bash
git clone https://github.com/cynthia-lancaster-485/django-grading-app.git
cd django-grading-app
python3 -m venv .venv
source .venv/bin/activate        # on Windows: .venv\Scripts\activate
pip install -r requirements.txt

python3 manage.py migrate
python3 makedata.py              # loads sample users, assignments, and submissions
python3 manage.py runserver
```

Open http://localhost:8000 and log in with any sample account. Each password is the same as the username.

| Role | Username |
| --- | --- |
| Instructor (admin) | `pavpan` |
| TAs | `g`, `h` |
| Students | `a`, `b`, `c`, `d` |

## Tests

```bash
python3 manage.py test grades
```

21 tests cover login and redirects, upload validation, file permissions, TA assignment, grade validation (including crafted requests), and the weighted grade calculation. They run automatically on every push with GitHub Actions.

## Deployment

For the course I deployed the app to an Ubuntu EC2 instance on AWS:

- Elastic IP and a custom domain with DNS A records
- NGINX as a reverse proxy to Django, also serving static files directly
- HTTPS certificates from Let's Encrypt through Certbot
- Production settings with `DEBUG` off and restricted allowed hosts

For a longer lived deployment I would run Django under an application server such as Gunicorn, managed by systemd, instead of Django's development server.

Settings read from the environment:

| Variable | Purpose | Default |
| --- | --- | --- |
| `DJANGO_SECRET_KEY` | Secret key | development only value |
| `DJANGO_DEBUG` | `true` or `false` | `true` |
| `DJANGO_ALLOWED_HOSTS` | Comma separated host names | `localhost,127.0.0.1` |
| `DJANGO_CSRF_TRUSTED_ORIGINS` | Comma separated origins, for example `https://example.com` | none |

## Project structure

```
cs3550/          Django project settings and URL routes
grades/
  models.py      Assignment and Submission models, plus the security rules
  views.py       Pages, form handling, validation, grade math
  templates/     Django templates (shared header include)
  tests.py       Automated tests
static/
  main.js        Sorting, async upload, and the what if calculator
  main.css       Styles
makedata.py      Sample data
```

## Changes since the course

The first commit is the code as I submitted it in Fall 2024. When I revisited it I found and fixed several bugs, which you can see in the commit history:

- Saving grades crashed because a helper function had a view decorator on it.
- New uploads crashed because of an incorrect filter in the TA assignment query.
- Failed upload checks showed an error but still saved the file.
- The admin was locked out of the grading page.
- Percentages used an assignment's weight instead of its points.
- Several JavaScript fixes: an undefined CSRF token, restoring the original sort order, and the what if calculator replacing table cells instead of their contents.

I also added the automated tests and CI, moved secrets into environment variables, and replaced the class's git submodule for jQuery with a vendored copy (jQuery 4.0.0, MIT license, in `static/vendor/`).

## What I learned

- **Security is mostly about where you put the rules.** Keeping permission checks in model methods meant the same rule protected the page, the form, and the file download.
- **Never trust the browser.** Every limit in the HTML (input ranges, accepted file types) is repeated on the server, because anyone can edit a form or send their own request.
- **Tests change how you see your own code.** Writing tests for this project is what surfaced bugs that the class autograder never checked.
