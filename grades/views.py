from . import models
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.models import User
from django.http import HttpRequest, Http404, HttpResponseBadRequest, HttpResponseRedirect, HttpResponse
from django.contrib.auth import authenticate, login, logout
from django.utils import timezone
from django.db.models import Count
from django.contrib.auth.decorators import login_required
from django.utils.http import url_has_allowed_host_and_scheme
from django.contrib.auth.decorators import user_passes_test
from django.core.exceptions import PermissionDenied

@login_required
def index(request):

    assignments = models.Assignment.objects.all()

    return render(request, "index.html", {"assignments": assignments})

@login_required
def assignment(request, assignment_id):

    assignment = get_object_or_404(models.Assignment, id=assignment_id)

    if not request.user.is_authenticated:
        user_type = "student"
    elif request.user.is_superuser:
        user_type = "admin"
    elif is_student(request.user):
        user_type = "student"
    elif is_ta(request.user):
        user_type = "ta"
    else:
        user_type = "unknown"

    #lets get the submissions
    if user_type == "admin":
        total_submissions = assignment.submission_set.count()
        subs_grader = None
    elif user_type == "ta":
        total_submissions = assignment.submission_set.count()
        subs_grader = assignment.submission_set.filter(grader=request.user).count()
    else :
        total_submissions = None
        subs_grader = None

    total_students = models.Group.objects.get(name="Students").user_set.count()
    user_submission = models.Submission.objects.filter(assignment=assignment, author=request.user).first()

    status = ""
    overdue = assignment.deadline < timezone.now()
    max_size = 64 * 1024 * 1024
    error = ""

    if user_submission:
        if user_submission.score is not None:
            # Get grade percentage and status message
            percent = (user_submission.score / assignment.weight) * 100
            status = f"Your submission, {user_submission.file.name}, received {user_submission}/{assignment.weight} points ({percent}%)"
       
        elif timezone.now() > assignment.deadline:
            status = f"Your submission, {user_submission.file.name}, is being graded"
        else:
            status = f"Your current submission is {user_submission.file.name}"
    else: 
        if assignment.deadline < timezone.now():
            status = "You did not submit this assignment and received 0 points"
        else: 
            status = "No current submission"

    if request.method == "POST":
        submission_file = request.FILES.get("submission_file")

        if timezone.now() > assignment.deadline:
            return HttpResponseBadRequest("This assignment is past due")

        # If there is a submission file create new submission
        if submission_file:
            #Check size 
            if submission_file.size > max_size:
                error = "File is too large. Needs to be less than 65MiB"
            #Check that it ends with pdf
            elif not submission_file.name.lower().endswith('pdf'):
                error = "File must be a PDF"
            #Check if it starts with %PDF
            elif not submission_file.read(5).startswith(b'%PDF-'):
                error = "File is not a valid PDF"
    
            if user_submission:
                user_submission.file = submission_file
                user_submission.grader = pick_grader(assignment)
                user_submission.score = None
            # Else create blank submission
            else:
                grader = pick_grader(assignment)
                user_submission = models.Submission(assignment=assignment, author=request.user, file=submission_file, score=None, grader=grader)

            user_submission.save()

            return redirect(f'/{ assignment_id }')
        

    return render(request, "assignment.html", {'assignment': assignment, 'total_submissions': total_submissions,  'subs_grader': subs_grader,  'total_students': total_students, 'user': request.user, 'user_submission': user_submission, 'user_type': user_type, 'status': status, 'overdue': overdue, 'error': error })


@login_required
def process_grades(data, assignment, request):
    new_submissions = []
    errors = {}
    assignment_points = assignment.points


    for key in data:
        if key.startswith('grade-') and len(key) > len('grade-'):
            submission_id = key.removeprefix('grade-')
            # grades[submission_id] = data[key]

            try:
                submission_id = int(submission_id)
                submission = models.Submission.objects.get(id=submission_id)
                score = data[key]
                
                #If its empty set to None
                if score == '':
                    submission.score = None
                    new_submissions.append(submission)
                #Convert it to a float and store
                else:
                    try:
                        score = float(score)

                    except ValueError:
                        errors.setdefault(submission_id, []).append("Grade needs to be a number")
                        continue

                if score < 0 or score > assignment_points:
                    errors.setdefault(submission_id, []).append(f"Grade must be above 0 but less than {assignment_points}")
                    continue

                submission.change_grade(request.user, score)
                # submission.save()
                new_submissions.append(submission)
            
            except(ValueError):
                errors.setdefault(submission_id, []).append(f"Invalid grade ID")
                continue
            except(models.Submission.DoesNotExist):
                errors.setdefault(submission_id, []).append(f"Submission doesnt exist")
                continue
            except(TypeError):
                errors.setdefault(submission_id, []).append(f"Enter a number")
                continue
        
        #Use bulk update to go faster
        if new_submissions:
            models.Submission.objects.bulk_update(new_submissions, ['score'])
            return errors


def is_ta(user):
    user_groups = user.groups.all()
    return user.groups.filter(name="Teaching Assistants").exists()

@user_passes_test(is_ta)
@login_required
def submissions(request, assignment_id):

    assignment = get_object_or_404(models.Assignment, id=assignment_id)

    if request.user.is_superuser:
        user_type = "admin"
    elif is_ta(request.user):
        user_type = "ta"
    else:
        user_type = "student"

    if user_type == "admin":
        submissions = models.Submission.objects.filter(assignment=assignment)
    else:
        submissions = models.Submission.objects.filter(assignment=assignment, grader=request.user)

    if request.method == "POST":
        errors = process_grades(request.POST, assignment, request.user)

        if errors:
            #re-render page
            return render(request, "submissions.html", {'submissions': submissions, 'assignment': assignment, 'errors': errors})
        
        return redirect(f"/{assignment_id}/submissions")

    return render(request, "submissions.html", {'submissions': submissions, 'assignment': assignment})

@login_required
def profile(request):

    user = request.user

    if request.user.is_superuser:
        user_type = "admin"
    elif is_ta(user):
        user_type = "ta"
    else:
        user_type = "student"
        student = user

    # if user_type == "student":
    #     

    if user_type == "ta":
        grader = request.user
    else:
        grader = None

    assignments = models.Assignment.objects.all()
    assignment_data = []
    total_points = 0
    total_weight = 0
    
    for assignment in assignments:
        if user_type == "admin":
            submissions_assigned = models.Submission.objects.filter(assignment=assignment).count()
            graded_submissions = models.Submission.objects.filter(assignment=assignment, score__isnull=False).count()

            assignment_data.append({
            'assignment': assignment,
            'submissions_assigned': submissions_assigned, 
            'graded_submissions': graded_submissions,
        })
        elif user_type == "ta":
            submissions_assigned = models.Submission.objects.filter(assignment=assignment, grader=grader).count()
            graded_submissions = models.Submission.objects.filter(assignment=assignment, grader=grader, score__isnull=False).count()

            assignment_data.append({
            'assignment': assignment,
            'submissions_assigned': submissions_assigned, 
            'graded_submissions': graded_submissions,
        })
        else:
            submission = models.Submission.objects.filter(assignment=assignment, author=student).first()

            if submission:
                if submission.score is not None:
                    # Get grade percentage
                    percent = (submission.score / assignment.weight) * 100
                    show_score = f"{percent}%"

                    #Add them for final grade
                    total_points += submission.score
                    total_weight += assignment.weight

                else:
                    show_score = "Ungraded"
            else: 
                if assignment.deadline < timezone.now():
                    show_score = "Missing"
                    total_weight += assignment.weight
                else: 
                    show_score = "Not Due"

            assignment_data.append({
            'assignment': assignment,
            'score': show_score,
            })

    if total_points > 0:
        final_grade = (total_points / total_weight) * 100
    else:
        final_grade = 0

    return render(request, "profile.html", {'assignment_data': assignment_data, 'grader': grader, 'user': request.user, 'user_type': user_type, 'final_grade': final_grade})

def login_form(request):
    # I added post here so that when it redirects to the page it still can save the next variable
    next_url = request.GET.get('next') or request.POST.get('next') or '/profile/'

    if request.method == 'POST':
        username = request.POST.get("username", "")
        password = request.POST.get("password", "")

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)

            if url_has_allowed_host_and_scheme(next_url, None):
                return HttpResponseRedirect(next_url)
            else:
                return redirect("/")
        else:
            return render(request, "login.html", {'error': "Username or password is incorrect", 'next': next_url})
        
    return render(request, "login.html", {'next': next_url})

@login_required
def show_upload(request, filename):
    try:
        submission = models.Submission.objects.get(file=filename)
        try:
            file = submission.view_submission(request.user)
        except PermissionDenied:
            return HttpResponse("You dont have permission to see this file ")
        file_name = submission.file.name.lower()

        #Check that it ends with pdf
        if not file_name.endswith('pdf'):
            raise Http404("File must be a PDF")
        #Check if it starts with %PDF
        submission.file.seek(0)
        if not submission.file.read(5).startswith(b'%PDF-'):
            raise Http404("File is not a valid PDF")
        
        file.open()
        response = HttpResponse(submission.file.read(), content_type="application/pdf")
        response['Content-Disposition'] = f'attachment; filename="{submission.file.name}"'
    
        return response
    
    except models.Submission.DoesNotExist:
        raise Http404("File doesnt exist")
    
def logout_form(request):
    next = request.GET.get('next', '/profile')
    logout(request)
    
    return redirect(next)

def is_student(user):
    user_groups = user.groups.all()
    return user.groups.filter(name="Students").exists()


def pick_grader(assignment):
    tas = models.Group.objects.get(name="Teaching Assistants")

    fewest_submissions = tas.user_set.annotate(
        total_assigned=Count(
            'graded_set', 
            filter=models.Submission.objects.filter(assignment=assignment, grader__isnull=False)
        )
    ).order_by('total_assigned').first()

    return fewest_submissions
