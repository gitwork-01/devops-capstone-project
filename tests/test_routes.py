"""
Account API Service Test Suite

Test cases can be run with the following:
  nosetests -v --with-spec --spec-color
  coverage report -m
"""
import os
import logging
from unittest import TestCase
from tests.factories import AccountFactory
from service.common import status  # HTTP Status Codes
from service.models import db, Account, init_db
from service.routes import app
from service import talisman

DATABASE_URI = os.getenv(
    "DATABASE_URI", "postgresql://postgres:postgres@localhost:5432/postgres"
)

BASE_URL = "/accounts"
HTTPS_ENVIRON = {'wsgi.url_scheme': 'https'}


######################################################################
#  T E S T   C A S E S
######################################################################
class TestAccountService(TestCase):
    """Account Service Tests"""

    @classmethod
    def setUpClass(cls):
        """Run once before all tests"""
        app.config["TESTING"] = True
        app.config["DEBUG"] = False
        app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URI
        app.logger.setLevel(logging.CRITICAL)
        init_db(app)
        talisman.force_https = False

    @classmethod
    def tearDownClass(cls):
        """Runs once before test suite"""

    def setUp(self):
        """Runs before each test"""
        db.session.query(Account).delete()  # clean up the last tests
        db.session.commit()

        self.client = app.test_client()

    def tearDown(self):
        """Runs once after each test case"""
        db.session.remove()

    ######################################################################
    #  H E L P E R   M E T H O D S
    ######################################################################

    def _create_accounts(self, count):
        """Factory method to create accounts in bulk"""
        accounts = []
        for _ in range(count):
            account = AccountFactory()
            response = self.client.post(BASE_URL, json=account.serialize())
            self.assertEqual(
                response.status_code,
                status.HTTP_201_CREATED,
                "Could not create test Account",
            )
            new_account = response.get_json()
            account.id = new_account["id"]
            accounts.append(account)
        return accounts

    ######################################################################
    #  A C C O U N T   T E S T   C A S E S
    ######################################################################

    def test_index(self):
        """It should get 200_OK from the Home Page"""
        response = self.client.get("/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_health(self):
        """It should be healthy"""
        resp = self.client.get("/health")
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertEqual(data["status"], "OK")

    def test_create_account(self):
        """It should Create a new Account"""
        account = AccountFactory()
        response = self.client.post(
            BASE_URL,
            json=account.serialize(),
            content_type="application/json"
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Make sure location header is set
        location = response.headers.get("Location", None)
        self.assertIsNotNone(location)

        # Check the data is correct
        new_account = response.get_json()
        self.assertEqual(new_account["name"], account.name)
        self.assertEqual(new_account["email"], account.email)
        self.assertEqual(new_account["address"], account.address)
        self.assertEqual(new_account["phone_number"], account.phone_number)
        self.assertEqual(new_account["date_joined"], str(account.date_joined))

    def test_bad_request(self):
        """It should not Create an Account when sending the wrong data"""
        response = self.client.post(BASE_URL, json={"name": "not enough data"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_unsupported_media_type(self):
        """It should not Create an Account when sending the wrong media type"""
        account = AccountFactory()
        response = self.client.post(
            BASE_URL,
            json=account.serialize(),
            content_type="test/html"
        )
        self.assertEqual(response.status_code, status.HTTP_415_UNSUPPORTED_MEDIA_TYPE)

    # ADD YOUR TEST CASES HERE ...
    def test_read_an_account(self):
        # make a POST call to accounts to create a new acount, passing in some data
        account = self._create_accounts(1)[0]

        # make a GET call to the the endpoint, passing in the id
        response = self.client.get(f"{BASE_URL}/{account.id}", content_type="application/json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        new_account = response.get_json()

        # assert that json returned is the same as the data sent
        self.assertEqual(new_account["name"], account.name)
        self.assertEqual(new_account["email"], account.email)
        self.assertEqual(new_account["address"], account.address)
        self.assertEqual(new_account["phone_number"], account.phone_number)
        self.assertEqual(new_account["date_joined"], str(account.date_joined))

    def test_account_not_found(self):
        """It should return 404 Error given an invalid id"""
        response = self.client.get(f"{BASE_URL}/0", content_type="application/json")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_get_accounts_list(self):
        """It shoudl return list of accounts"""
        # call _createAccounts to create list of accounts
        accounts = self._create_accounts(10)

        # make a GET request to /accounts
        resp = self.client.get(f"{BASE_URL}", content_type="application/json")
        data = resp.get_json()

        # assert status code 200 OK and that length of list is same as length of accounts
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(len(data), len(accounts), "Server did not return all accounts")

        # iterate through each account returned and verify that all of the data matches
        for (i, this_account) in enumerate(data):
            self.assertEqual(this_account["name"], accounts[i].name)
            self.assertEqual(this_account["email"], accounts[i].email)
            self.assertEqual(this_account["address"], accounts[i].address)
            self.assertEqual(this_account["phone_number"], accounts[i].phone_number)
            self.assertEqual(this_account["date_joined"], str(accounts[i].date_joined))

    def test_update_user_account(self):
        """It should update an account"""
        # Add a new account to the database
        account = self._create_accounts(1)[0]

        # retrieve that account from API and assert that it is the same as the new account
        resp = self.client.get(f"{BASE_URL}/{account.id}", content_type='application/json')
        retrieved_account = resp.get_json()
        self.assertEqual(retrieved_account["id"], account.id)
        self.assertEqual(retrieved_account["name"], account.name)
        self.assertEqual(retrieved_account["email"], account.email)
        self.assertEqual(retrieved_account["address"], account.address)
        self.assertEqual(retrieved_account["phone_number"], account.phone_number)
        self.assertEqual(retrieved_account["date_joined"], str(account.date_joined))

        # modify data of initial account and serialize it, then PUT call to API with JSON payload
        temp_id = account.id
        account = AccountFactory()
        account.id = temp_id
        payload = account.serialize()
        resp = self.client.put(f"{BASE_URL}/{account.id}", json=payload)

        # assert status 200 OK and body contains updated account
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        updated_account = resp.get_json()
        for key in updated_account.keys():
            self.assertEqual(updated_account[key], payload[key])

    def test_invalid_account_not_updated(self):
        """Should not update invalid account data"""
        # create a new account using _create
        account = self._create_accounts(1)[0]

        # change all of the account values except id
        temp_id = account.id
        account = AccountFactory()
        account.id = temp_id

        # PUT request to API using 0 as id and assert 404
        resp = self.client.put(f"{BASE_URL}/0", json=account.serialize())
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

        # pass None in request body for PUT and assert 400
        resp = self.client.put(f"{BASE_URL}/{account.id}", json=None)
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_delete_an_account(self):
        """Should delete an existing account"""
        # create an account
        account = self._create_accounts(1)[0]

        # delete that account
        resp = self.client.delete(f"{BASE_URL}/{account.id}")

        # assert that item not found and HTTP 204 deleted
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(self.client.get(f"{BASE_URL}/{account.id}").status_code, status.HTTP_404_NOT_FOUND)

    def test_invalid_http_method_rejected(self):
        """Should not allow HTTP request methods that aren't permitted"""
        # make a POST request to /
        resp = self.client.post("/")
        self.assertEqual(resp.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_security_headers(self):
        """API should add security and CORS policy headers"""
        resp = self.client.get("/", environ_overrides=HTTPS_ENVIRON)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        headers = {
            'X-Frame-Options': 'SAMEORIGIN',
            'X-Content-Type-Options': 'nosniff',
            'Content-Security-Policy': 'default-src \'self\'; object-src \'none\'',
            'Referrer-Policy': 'strict-origin-when-cross-origin'
        }
        for key, value in headers.items():
            self.assertEqual(resp.headers.get(key), value)

    def test_cors_header(self):
        """API should return CORS policy in header"""
        resp = self.client.get("/", environ_overrides=HTTPS_ENVIRON)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.headers.get('Access-Control-Allow-Origin'), '*')