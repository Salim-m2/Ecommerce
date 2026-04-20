# apps/authentication/tests.py

from datetime import datetime
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from apps.users.documents import User


class AuthAPITestCase(TestCase):
    """
    Integration tests for all authentication endpoints.
    Tests happy paths + key failure cases.
    """

    def setUp(self):
        """
        Runs before every test.
        Creates a fresh API client and cleans up any
        test users left over from previous runs.
        """
        self.client = APIClient()
        self.base_url = '/api/v1/auth'

        # Clean up test users before each test
        User.objects(email='testuser@example.com').delete()
        User.objects(email='existing@example.com').delete()

        # Create a pre-existing user for login tests
        existing = User(
            email      = 'existing@example.com',
            first_name = 'Existing',
            last_name  = 'User',
        )
        existing.set_password('testpass123')
        existing.save()

    def tearDown(self):
        """Runs after every test — clean up test data."""
        User.objects(email='testuser@example.com').delete()
        User.objects(email='existing@example.com').delete()

    # ─────────────────────────────────────────
    # REGISTER TESTS
    # ─────────────────────────────────────────
    def test_register_success(self):
        """Valid registration should return 201 with user data."""
        response = self.client.post(
            f'{self.base_url}/register/',
            {
                'first_name':       'Test',
                'last_name':        'User',
                'email':            'testuser@example.com',
                'password':         'securepass123',
                'confirm_password': 'securepass123',
            },
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('user', response.data)
        self.assertEqual(response.data['user']['email'], 'testuser@example.com')
        self.assertEqual(response.data['user']['role'], 'customer')
        # Password must never be returned
        self.assertNotIn('password', response.data['user'])
        self.assertNotIn('password_hash', response.data['user'])

    def test_register_duplicate_email(self):
        """Registering with an existing email should return 400."""
        response = self.client.post(
            f'{self.base_url}/register/',
            {
                'first_name':       'Another',
                'last_name':        'User',
                'email':            'existing@example.com',
                'password':         'securepass123',
                'confirm_password': 'securepass123',
            },
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('email', response.data)

    def test_register_password_mismatch(self):
        """Mismatched passwords should return 400."""
        response = self.client.post(
            f'{self.base_url}/register/',
            {
                'first_name':       'Test',
                'last_name':        'User',
                'email':            'testuser@example.com',
                'password':         'securepass123',
                'confirm_password': 'wrongpass123',
            },
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_register_short_password(self):
        """Password under 8 characters should return 400."""
        response = self.client.post(
            f'{self.base_url}/register/',
            {
                'first_name':       'Test',
                'last_name':        'User',
                'email':            'testuser@example.com',
                'password':         'short',
                'confirm_password': 'short',
            },
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    # ─────────────────────────────────────────
    # LOGIN TESTS
    # ─────────────────────────────────────────
    def test_login_success(self):
        """Valid credentials should return 200 and set cookies."""
        response = self.client.post(
            f'{self.base_url}/login/',
            {
                'email':    'existing@example.com',
                'password': 'testpass123',
            },
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('user', response.data)
        self.assertEqual(response.data['user']['email'], 'existing@example.com')

        # Verify JWT cookies are set
        self.assertIn('access_token', response.cookies)
        self.assertIn('refresh_token', response.cookies)

        # Verify cookies are httpOnly
        self.assertTrue(response.cookies['access_token']['httponly'])
        self.assertTrue(response.cookies['refresh_token']['httponly'])

    def test_login_wrong_password(self):
        """Wrong password should return 401."""
        response = self.client.post(
            f'{self.base_url}/login/',
            {
                'email':    'existing@example.com',
                'password': 'wrongpassword',
            },
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn('error', response.data)

    def test_login_nonexistent_email(self):
        """Login with unregistered email should return 401."""
        response = self.client.post(
            f'{self.base_url}/login/',
            {
                'email':    'nobody@example.com',
                'password': 'somepassword',
            },
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    # ─────────────────────────────────────────
    # LOGOUT TESTS
    # ─────────────────────────────────────────
    def test_logout_clears_cookies(self):
        """Logout should clear both JWT cookies."""
        # First login to get cookies
        login_response = self.client.post(
            f'{self.base_url}/login/',
            {'email': 'existing@example.com', 'password': 'testpass123'},
            format='json'
        )
        self.assertEqual(login_response.status_code, status.HTTP_200_OK)

        # Now logout
        logout_response = self.client.post(f'{self.base_url}/logout/')
        self.assertEqual(logout_response.status_code, status.HTTP_200_OK)

        # Cookies should be cleared (max-age=0 or empty value)
        if 'access_token' in logout_response.cookies:
            cookie = logout_response.cookies['access_token']
            self.assertTrue(
                cookie.value == '' or cookie['max-age'] == 0,
                'access_token cookie should be cleared on logout'
            )

    def test_logout_requires_authentication(self):
        """Logout without cookies should return 401."""
        response = self.client.post(f'{self.base_url}/logout/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    # ─────────────────────────────────────────
    # TOKEN REFRESH TESTS
    # ─────────────────────────────────────────
    def test_token_refresh_success(self):
        """After login, token refresh should return 200 and new access cookie."""
        # Login first
        self.client.post(
            f'{self.base_url}/login/',
            {'email': 'existing@example.com', 'password': 'testpass123'},
            format='json'
        )

        # Refresh
        response = self.client.post(f'{self.base_url}/token/refresh/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access_token', response.cookies)

    def test_token_refresh_no_cookie(self):
        """Token refresh without a refresh cookie should return 401."""
        response = self.client.post(f'{self.base_url}/token/refresh/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    # ─────────────────────────────────────────
    # ME ENDPOINT TESTS
    # ─────────────────────────────────────────
    def test_me_endpoint_authenticated(self):
        """Authenticated user should get their data from /me/."""
        # Login first
        self.client.post(
            f'{self.base_url}/login/',
            {'email': 'existing@example.com', 'password': 'testpass123'},
            format='json'
        )

        # Call /me/
        response = self.client.get(f'{self.base_url}/me/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['email'], 'existing@example.com')
        self.assertIn('id', response.data)
        self.assertNotIn('password_hash', response.data)

    def test_me_endpoint_unauthenticated(self):
        """Unauthenticated request to /me/ should return 401."""
        response = self.client.get(f'{self.base_url}/me/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    # ─────────────────────────────────────────
    # PASSWORD RESET TESTS
    # ─────────────────────────────────────────
    def test_password_reset_request(self):
        """Password reset request should always return 200."""
        # Real email
        response = self.client.post(
            f'{self.base_url}/password/reset/',
            {'email': 'existing@example.com'},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Fake email — same response to prevent enumeration
        response2 = self.client.post(
            f'{self.base_url}/password/reset/',
            {'email': 'nobody@example.com'},
            format='json'
        )
        self.assertEqual(response2.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, response2.data)

    def test_password_reset_confirm_invalid_token(self):
        """Invalid reset token should return 400."""
        response = self.client.post(
            f'{self.base_url}/password/reset/confirm/',
            {
                'token':        'invalidtoken123',
                'new_password': 'newpassword123',
            },
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)