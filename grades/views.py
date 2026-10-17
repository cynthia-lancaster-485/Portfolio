from . import models
from django.shortcuts import render, get_object_or_404, redirect
from django.http import Http404, HttpResponseBadRequest, HttpResponseRedirect, HttpResponse
from django.contrib.auth import authenticate, login, logout
from django.utils import timezone
from django.db.models import Count, Q
from django.contrib.auth.decorators import login_required
from django.utils.http import url_has_allowed_host_and_scheme
from django.core.exceptions import PermissionDenied

MAX_UPLOAD_SIZE = 64 * 1024 * 1024  # 64 MiB


@login_required
def index(request):

    assignments = models.Assignment.objects.all()

    return render(request, "index.html", {"assignments": assignments})


@login_required
def assignment(request, assignment_id):

    assignment = get_object_or_404(models.Assignment, id=assignment_id)
    user_type = get_user_type(request.user)

    #lets get the submissions
    if user_type == "admin":
        total_submissions = assignment.submission_set.count()
        subs_grader = None
    elif user_type == "ta":
        total_submissions = assignment.submission_set.count()
        subs_grader = assignment.submission_set.filter(grader=request.user).count()
    else:
        total_submissions = None
        subs_grader = None

    total_students = models.Group.objects.get(name="Students").user_set.count()
    user_submission = models.Submission.objects.filter(assignment=assignment, author=request.user).first()

    overdue = assignment.deadline < timezone.now()
    error = ""

    if request.method == "POST":
        # Only students can submit, and only before the deadline
        if user_type != "student":
            raise PermissionDenied
        if overdue:
            return HttpResponseBadRequest("This assignment is past due")

        submission_file = request.FILES.get("submission_file")

        # Validate the upload. Size is checked first so we never read a huge file.
        if not submission_file:
            error = "Please choose a file to upload"
        elif submission_file.size > MAX_UPLOAD_SIZE:
            error = "File is too large. It needs to be 64 MiB or smaller"
        elif not is_pdf(submission_file):
            error = "File must be a PDF"

        if not error:
            if user_submission:
                # Replacing a file keeps the TA who was already assigned
                user_submission.file = submission_file
                user_submission.score = None
            # Else create a new submission and assign the TA with the fewest submissions
            else:
                user_submission = models.Submission(assignment=assignment, author=request.user, file=submission_file, score=None, grader=pick_grader(assignment))

            user_submission.save()

            return redirect(f'/{ assignment_id }/')

    status = get_submission_status(assignment, user_submission, overdue)

    context = {'assignment': assignment, 'total_submissions': total_submissions, 'subs_grader': subs_grader, 'total_students': total_students, 'user': request.user, 'user_submission': user_submission, 'user_type': user_type, 'status': status, 'overdue': overdue, 'error': error}

    # A failed upload re-renders the page with the error and a 400 status,
    # which also lets the AJAX upload know that it failed
    return render(request, "assignment.html", context, status=400 if error else 200)


def get_submission_status(assignment, user_submission, overdue):
    if user_submission:
        if user_submission.score is not None:
            # Get grade percentage and status message
            percent = (user_submission.score / assignment.points) * 100
            return f"Your submission, {user_submission.file.name}, received {user_submission.score:g}/{assignment.points} points ({percent:.1f}%)"
        elif overdue:
            return f"Your submission, {user_submission.file.name}, is being graded"
        else:
            return f"Your current submission is {user_submission.file.name}"
    else:
        if overdue:
            return "You did not submit this assignment and received 0 points"
        else:
            return "No current submission"


def process_grades(data, assignment, user):
    """Validate submitted grades. Saves the valid ones and returns any errors.

    Returns (errors, general_errors): errors maps a submission id to a list of
    messages, and general_errors holds messages for ids that are not real
    submissions to this assignment.
    """
    new_submissions = []
    errors = {}
    general_errors = []
    assignment_points = assignment.points

    for key in data:
        if not (key.startswith('grade-') and len(key) > len('grade-')):
            continue

        try:
            submission_id = int(key.removeprefix('grade-'))
            submission = models.Submission.objects.get(id=submission_id, assignment=assignment)
        except (ValueError, models.Submission.DoesNotExist):
            general_errors.append(f"There is no submission with ID {key.removeprefix('grade-')} for this assignment")
            continue

        score = data[key].strip()

        #If its empty set to None
        if score == '':
            score = None
        #Convert it to a float and check the range
        else:
            try:
                score = float(score)
            except ValueError:
                errors.setdefault(submission_id, []).append("Grade needs to be a number")
                continue

            if score < 0 or score > assignment_points:
                errors.setdefault(submission_id, []).append(f"Grade must be between 0 and {assignment_points}")
                continue

        # change_grade enforces who is allowed to grade this submission
        try:
            submission.change_grade(user, score)
        except PermissionDenied:
            errors.setdefault(submission_id, []).append("You are not assigned to grade this submission")
            continue

        new_submissions.append(submission)

    #Use bulk update to save every valid grade in one query
    if new_submissions:
        models.Submission.objects.bulk_update(new_submissions, ['score'])

    return errors, general_errors


@login_required
def submissions(request, assignment_id):

    assignment = get_object_or_404(models.Assignment, id=assignment_id)
    user_type = get_user_type(request.user)

    # Only TAs and the admin can see the grading page
    if user_type not in ("ta", "admin"):
        raise PermissionDenied

    submissions = models.Submission.objects.filter(assignment=assignment).select_related("author").order_by("author__username")
    if user_type == "ta":
        submissions = submissions.filter(grader=request.user)

    errors = {}
    general_errors = []

    if request.method == "POST":
        errors, general_errors = process_grades(request.POST, assignment, request.user)

        if not errors and not general_errors:
            return redirect(f"/{assignment_id}/submissions")

    # Pair each submission with its errors so the template can show them on the right row
    rows = [{'submission': submission, 'errors': errors.get(submission.id, [])} for submission in submissions]

    # Errors for submissions not shown on this page (e.g. a crafted POST) go at the top
    shown_ids = {row['submission'].id for row in rows}
    for submission_id, messages in errors.items():
        if submission_id not in shown_ids:
            general_errors.extend(f"Submission {submission_id}: {message}" for message in messages)

    return render(request, "submissions.html", {'rows': rows, 'assignment': assignment, 'general_errors': general_errors})


@login_required
def profile(request):

    user = request.user
    user_type = get_user_type(user)

    assignments = models.Assignment.objects.all()
    assignment_data = []
    earned_points = 0
    available_points = 0
    now = timezone.now()

    for assignment in assignments:
        if user_type == "admin":
            submissions = models.Submission.objects.filter(assignment=assignment)
        elif user_type == "ta":
            submissions = models.Submission.objects.filter(assignment=assignment, grader=user)

        if user_type in ("admin", "ta"):
            assignment_data.append({
                'assignment': assignment,
                'submissions_assigned': submissions.count(),
                'graded_submissions': submissions.filter(score__isnull=False).count(),
            })
            continue

        submission = models.Submission.objects.filter(assignment=assignment, author=user).first()
        sort_value = ""

        if submission and submission.score is not None:
            # Graded: counts toward both available and earned points
            percent = (submission.score / assignment.points) * 100
            show_score = f"{percent:.1f}%"
            sort_value = percent
            earned_points += (percent / 100) * assignment.weight
            available_points += assignment.weight
        elif submission:
            show_score = "Ungraded"
        elif assignment.deadline < now:
            # Missing: counts as a zero
            show_score = "Missing"
            sort_value = 0
            available_points += assignment.weight
        else:
            show_score = "Not Due"

        assignment_data.append({
            'assignment': assignment,
            'score': show_score,
            'sort_value': sort_value,
        })

    # With nothing graded or missing yet, a student's grade is 100%
    if available_points > 0:
        final_grade = (earned_points / available_points) * 100
    else:
        final_grade = 100

    return render(request, "profile.html", {'assignment_data': assignment_data, 'user': user, 'user_type': user_type, 'final_grade': final_grade})


def login_form(request):
    # I added post here so that when it redirects to the page it still can save the next variable
    next_url = request.GET.get('next') or request.POST.get('next') or '/profile/'

    if request.method == 'POST':
        username = request.POST.get("username", "")
        password = request.POST.get("password", "")

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)

            # Only follow "next" if it points back to this site (prevents open redirects)
            if url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}, require_https=request.is_secure()):
                return HttpResponseRedirect(next_url)
            else:
                return redirect("/")
        else:
            return render(request, "login.html", {'error': "Username and password do not match", 'next': next_url})

    return render(request, "login.html", {'next': next_url})


@login_required
def show_upload(request, filename):
    try:
        submission = models.Submission.objects.get(file=filename)
    except models.Submission.DoesNotExist:
        raise Http404("File doesnt exist")

    # view_submission raises PermissionDenied (403) for anyone who shouldn't see it
    file = submission.view_submission(request.user)

    # Check again on the way out, so new checks also apply to older uploads
    file.open("rb")
    try:
        if not is_pdf(file):
            raise Http404("File is not a valid PDF")
        file.seek(0)
        response = HttpResponse(file.read(), content_type="application/pdf")
    finally:
        file.close()

    response['Content-Disposition'] = f'attachment; filename="{submission.file.name}"'
    return response


def logout_form(request):
    logout(request)

    return redirect("/profile/login/")


def is_pdf(file):
    """A file counts as a PDF if its name ends in .pdf and it starts with %PDF-."""
    if not file.name.lower().endswith('.pdf'):
        return False
    file.seek(0)
    first_bytes = file.read(5)
    file.seek(0)
    return first_bytes.startswith(b'%PDF-')


def is_ta(user):
    return user.groups.filter(name="Teaching Assistants").exists()


def is_student(user):
    return user.groups.filter(name="Students").exists()


def get_user_type(user):
    if user.is_superuser:
        return "admin"
    elif is_ta(user):
        return "ta"
    else:
        return "student"


def pick_grader(assignment):
    """Return the TA with the fewest submissions to grade for this assignment, in one query."""
    tas = models.Group.objects.get(name="Teaching Assistants")

    fewest_submissions = tas.user_set.annotate(
        total_assigned=Count('graded_set', filter=Q(graded_set__assignment=assignment))
    ).order_by('total_assigned', 'id').first()

    return fewest_submissions
