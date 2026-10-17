import datetime
import shutil
import tempfile

from django.contrib.auth.models import Group, User
from django.core.files.base import ContentFile
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.utils import timezone

from .models import Assignment, Submission
from .views import pick_grader

TEMP_MEDIA = tempfile.mkdtemp()
PDF_BYTES = b"%PDF-1.4 test document"


@override_settings(MEDIA_ROOT=TEMP_MEDIA)
class GradesTestCase(TestCase):
    """Shared setup: one admin, two TAs, two students, a past and a future assignment."""

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA, ignore_errors=True)

    def setUp(self):
        tas = Group.objects.create(name="Teaching Assistants")
        students = Group.objects.create(name="Students")

        self.admin = User.objects.create_superuser("admin", "admin@example.com", "pw")
        self.ta1 = User.objects.create_user("ta1", password="pw", first_name="Garry", last_name="Grader")
        self.ta2 = User.objects.create_user("ta2", password="pw", first_name="Helen", last_name="Helper")
        tas.user_set.add(self.ta1, self.ta2)
        self.alice = User.objects.create_user("alice", password="pw", first_name="Alice", last_name="A")
        self.bob = User.objects.create_user("bob", password="pw", first_name="Bob", last_name="B")
        students.user_set.add(self.alice, self.bob)

        now = timezone.now()
        self.past = Assignment.objects.create(
            title="HW1", description="<p>Done</p>", deadline=now - datetime.timedelta(days=1), weight=100, points=50
        )
        self.future = Assignment.objects.create(
            title="HW2", description="<p>Soon</p>", deadline=now + datetime.timedelta(days=7), weight=50, points=10
        )

    def make_submission(self, assignment, author, grader, score=None, content=PDF_BYTES, name="work.pdf"):
        submission = Submission(assignment=assignment, author=author, grader=grader, score=score)
        submission.file.save(name, ContentFile(content), save=True)
        return submission

    def login(self, user):
        self.client.force_login(user)


class AuthenticationTests(GradesTestCase):
    def test_pages_require_login(self):
        response = self.client.get("/")
        self.assertRedirects(response, "/profile/login/?next=/", fetch_redirect_response=False)

    def test_login_redirects_to_next(self):
        response = self.client.post("/profile/login/", {"username": "alice", "password": "pw", "next": "/profile/"})
        self.assertRedirects(response, "/profile/", fetch_redirect_response=False)

    def test_login_blocks_open_redirect(self):
        response = self.client.post("/profile/login/", {"username": "alice", "password": "pw", "next": "https://evil.example"})
        self.assertRedirects(response, "/", fetch_redirect_response=False)

    def test_bad_password_shows_error(self):
        response = self.client.post("/profile/login/", {"username": "alice", "password": "wrong"})
        self.assertContains(response, "Username and password do not match")


class UploadTests(GradesTestCase):
    def upload(self, name, content, assignment=None):
        assignment = assignment or self.future
        return self.client.post(f"/{assignment.id}/", {"submission_file": SimpleUploadedFile(name, content)})

    def test_valid_pdf_is_saved_and_assigned_a_ta(self):
        self.login(self.alice)
        response = self.upload("hw.pdf", PDF_BYTES)
        self.assertEqual(response.status_code, 302)
        submission = Submission.objects.get(assignment=self.future, author=self.alice)
        self.assertIn(submission.grader, [self.ta1, self.ta2])

    def test_non_pdf_is_rejected(self):
        self.login(self.alice)
        response = self.upload("notes.txt", b"hello")
        self.assertContains(response, "File must be a PDF", status_code=400)
        self.assertFalse(Submission.objects.exists())

    def test_renamed_file_is_rejected(self):
        self.login(self.alice)
        response = self.upload("fake.pdf", b"not really a pdf")
        self.assertEqual(response.status_code, 400)
        self.assertFalse(Submission.objects.exists())

    def test_upload_after_deadline_is_rejected(self):
        self.login(self.alice)
        response = self.upload("hw.pdf", PDF_BYTES, assignment=self.past)
        self.assertEqual(response.status_code, 400)
        self.assertFalse(Submission.objects.exists())

    def test_resubmitting_keeps_the_same_ta(self):
        self.make_submission(self.future, self.alice, self.ta2)
        self.login(self.alice)
        self.upload("hw-v2.pdf", PDF_BYTES)
        self.assertEqual(Submission.objects.get(author=self.alice).grader, self.ta2)

    def test_pick_grader_balances_work(self):
        self.make_submission(self.future, self.bob, self.ta1)
        self.assertEqual(pick_grader(self.future), self.ta2)


class FileAccessTests(GradesTestCase):
    def setUp(self):
        super().setUp()
        self.submission = self.make_submission(self.past, self.alice, self.ta1)
        self.url = self.submission.file.url

    def test_author_assigned_ta_and_admin_can_view(self):
        for user in (self.alice, self.ta1, self.admin):
            self.login(user)
            response = self.client.get(self.url)
            self.assertEqual(response.status_code, 200, user.username)
            self.assertEqual(response["Content-Type"], "application/pdf")
            self.assertIn("attachment", response["Content-Disposition"])

    def test_other_users_cannot_view(self):
        for user in (self.bob, self.ta2):
            self.login(user)
            self.assertEqual(self.client.get(self.url).status_code, 403, user.username)


class GradingTests(GradesTestCase):
    def setUp(self):
        super().setUp()
        self.alice_sub = self.make_submission(self.past, self.alice, self.ta1)
        self.bob_sub = self.make_submission(self.past, self.bob, self.ta2, name="bob.pdf")
        self.url = f"/{self.past.id}/submissions"

    def test_students_cannot_open_grading_page(self):
        self.login(self.alice)
        self.assertEqual(self.client.get(self.url).status_code, 403)

    def test_ta_only_sees_assigned_submissions(self):
        self.login(self.ta1)
        response = self.client.get(self.url)
        self.assertContains(response, "Alice A")
        self.assertNotContains(response, "Bob B")

    def test_admin_sees_all_submissions(self):
        self.login(self.admin)
        response = self.client.get(self.url)
        self.assertContains(response, "Alice A")
        self.assertContains(response, "Bob B")

    def test_valid_grade_is_saved(self):
        self.login(self.ta1)
        response = self.client.post(self.url, {f"grade-{self.alice_sub.id}": "42.5"})
        self.assertEqual(response.status_code, 302)
        self.alice_sub.refresh_from_db()
        self.assertEqual(self.alice_sub.score, 42.5)

    def test_invalid_grades_are_rejected_but_valid_ones_saved(self):
        self.make_submission(self.past, self.bob, self.ta1, name="bob2.pdf")
        extra = Submission.objects.filter(grader=self.ta1).exclude(id=self.alice_sub.id).get()
        self.login(self.ta1)
        response = self.client.post(self.url, {
            f"grade-{self.alice_sub.id}": "hello",
            f"grade-{extra.id}": "10",
            "grade-99999": "5",
        })
        self.assertContains(response, "Grade needs to be a number")
        self.assertContains(response, "There is no submission with ID 99999")
        self.alice_sub.refresh_from_db()
        extra.refresh_from_db()
        self.assertIsNone(self.alice_sub.score)
        self.assertEqual(extra.score, 10)

    def test_out_of_range_grade_is_rejected(self):
        self.login(self.ta1)
        response = self.client.post(self.url, {f"grade-{self.alice_sub.id}": "500"})
        self.assertContains(response, "Grade must be between 0 and 50")
        self.assertContains(response, 'value="500"')
        self.alice_sub.refresh_from_db()
        self.assertIsNone(self.alice_sub.score)

    def test_ta_cannot_grade_unassigned_submission_with_crafted_post(self):
        self.login(self.ta1)
        response = self.client.post(self.url, {f"grade-{self.bob_sub.id}": "50"})
        self.assertContains(response, "You are not assigned to grade this submission")
        self.bob_sub.refresh_from_db()
        self.assertIsNone(self.bob_sub.score)


class GradeCalculationTests(GradesTestCase):
    def test_final_grade_uses_weighted_percentages(self):
        # HW1: 40/50 = 80% at weight 100.  A missing assignment counts as 0 at weight 50.
        self.make_submission(self.past, self.alice, self.ta1, score=40)
        Assignment.objects.create(
            title="HW0", description="", deadline=timezone.now() - datetime.timedelta(days=2), weight=50, points=20
        )
        self.login(self.alice)
        response = self.client.get("/profile/")
        self.assertContains(response, "80.0%")
        self.assertContains(response, "Missing")
        self.assertContains(response, "Not Due")
        # (80 + 0) earned out of (100 + 50) available = 53.33%
        self.assertContains(response, "53.33%")

    def test_no_graded_work_means_100_percent(self):
        self.login(self.bob)
        self.past.deadline = timezone.now() + datetime.timedelta(days=1)
        self.past.save()
        response = self.client.get("/profile/")
        self.assertContains(response, "100.00%")
