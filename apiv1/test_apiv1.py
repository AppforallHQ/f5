from mock import patch
import httpretty

from django.contrib.auth.models import User
from django.test import TestCase
from django.test.client import RequestFactory

from plans.models import Subscription, Invoice
from plans.forms import PlanForm

import re
import json

from plans.tests import a_valid_plan

class SimpleTest(TestCase):

    def setUp(self):
        self.credentials = {"username": 'joe@rubako.us', "password": "top_secret"}
        self.user = User.objects.create_user(**self.credentials)

        self.client.login(**self.credentials)

        form_data = a_valid_plan

        form = PlanForm(data=form_data)
        self.plan = form.save()

        self.uuid = "SOME_UUID"
        self.interaction_endpoint_url = form_data["interaction_endpoint_url"]

        httpretty.enable()
        httpretty.register_uri(
            httpretty.POST,
            re.compile("example.com"),
            status=200,
        )

        # Fetch email body from external endpoint
        self.email_contents = {
            "body": "Dear user, pay the invoice from here: %(url)s",
            "subject": "pay the invoice, man",
            "sender": "foo@example.com",
        }

        httpretty.register_uri(
            httpretty.POST,
            re.compile("example.com/mail_endpoint"),
            status=200,
            body=json.dumps(self.email_contents)
        )


    def tearDown(self):
        httpretty.disable()

    def mock_http_response_for_url_interaction(self, pass_or_fail):
        httpretty.HTTPretty.reset()

        if pass_or_fail == "pass":
            body = "passed"
            status = 200
        else:
            body = "failed :("
            status = 404

        interaction_url = self.interaction_endpoint_url
        httpretty.register_uri(
            httpretty.PUT,
            re.compile("example.com"),
            responses=[httpretty.Response(body=body, status=status)],
        )

    def test_plan_list(self):
        response = self.client.get('/api/v1/plans/')

        self.assertEqual(response.status_code, 200)

        res = json.loads(response.content)
        self.assertEqual(res["count"], 1)
        self.assertIn({"id": 1}, res["results"])

    def test_new_subscription(self):
        subscription = {"uuid": self.uuid,
                        "plan": self.plan.pk,
                        "email": "joe@rubako.us"}

        response = self.client.post('/api/v1/subscriptions/', subscription)
        self.assertEqual(response.status_code, 201)

        the_response = json.loads(response.content)
        self.assertIn("uuid", the_response)
        self.assertIn("plan", the_response)
        self.assertIn("email", the_response)
        self.assertIn("active_invoice_payment_url", the_response)

        # for those other tests
        self.subscription = Subscription.objects.get(**subscription)

    def test_generate_new_invoice_when_api_is_called(self):
        self.test_new_subscription()
        active_invoice = self.subscription.active_invoice
        active_invoice.mark_as_invalid()

        self.assertEqual(None, self.subscription.active_invoice)

        response = self.client.get('/api/v1/subscriptions/%d/' % self.subscription.pk)

        self.assertNotEqual(None, self.subscription.active_invoice)

    def test_call_interaction_endpoint_url_for_activation(self):
        self.test_new_subscription()

        self.mock_http_response_for_url_interaction("fail")

        response = self.subscription.call_endpoint_url_for_activation()
        assert not response.successful()

        last_request = httpretty.last_request()
        post_data = json.loads(last_request.body)

        assert post_data["uuid"] == self.uuid
        assert post_data["plan"] == self.subscription.plan.pk
        assert post_data["activate"] == True
        self.assertEqual("PUT", last_request.method)

        self.mock_http_response_for_url_interaction("pass")
        response = self.subscription.call_endpoint_url_for_activation()
        assert response.successful()

    def test_call_interaction_endpoint_url_for_deactivation(self):
        self.test_new_subscription()

        self.mock_http_response_for_url_interaction("fail")

        response = self.subscription.call_endpoint_url_for_deactivation()
        assert not response.successful()

        last_request = httpretty.last_request()
        post_data = json.loads(last_request.body)

        assert post_data["uuid"] == self.uuid
        assert post_data["plan"] == self.subscription.plan.pk
        assert post_data["activate"] == False
        self.assertEqual("PUT", last_request.method)

        self.mock_http_response_for_url_interaction("pass")

        response = self.subscription.call_endpoint_url_for_deactivation()
        assert response.successful()

    @patch.object(Subscription, 'call_endpoint_url_for_activation')
    def test_is_external_endpoint_called_when_paid(self, mocked_method):
        list_of_return_values= [False, True]
        def side_effect():
            return list_of_return_values.pop()
        mocked_method.side_effect = side_effect

        self.test_new_subscription()

        self.subscription.active_invoice.mark_as_paid()

        mocked_method.assert_called_with()

    @patch.object(Subscription, 'call_endpoint_url_for_deactivation')
    def test_is_external_endpoint_called_when_grace_time_ends(self, mocked_method):
        list_of_return_values= [False, True]
        def side_effect():
            return list_of_return_values.pop()
        mocked_method.side_effect = side_effect

        self.test_new_subscription()

        self.subscription.mark_as_overdue()
        self.subscription.end_grace_time()

        mocked_method.assert_called_with()

    def test_invalid_subscription_data(self):
        # lets not provide email for example
        subscription = {"uuid": self.uuid,
                        "plan": self.plan.pk}

        response = self.client.post('/api/v1/subscriptions/', subscription)

        self.assertEqual(response.status_code, 400)
