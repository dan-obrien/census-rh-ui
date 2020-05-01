import json

from unittest import mock
from urllib.parse import urlsplit, parse_qs

from aiohttp.client_exceptions import ClientConnectionError
from aiohttp.test_utils import unittest_run_loop
from aioresponses import aioresponses

from app.exceptions import InactiveCaseError, InvalidEqPayLoad

from . import RHTestCase, build_eq_raises, skip_encrypt


# noinspection PyTypeChecker
class TestStartHandlersUnlinked(RHTestCase):
    @skip_encrypt
    @unittest_run_loop
    async def test_unlinked_uac_happy_path_en(self):
        with self.assertLogs('respondent-home', 'INFO') as cm, mock.patch(
                'app.utils.AddressIndex.get_ai_postcode') as mocked_get_ai_postcode, mock.patch(
                'app.utils.AddressIndex.get_ai_uprn') as mocked_get_ai_uprn, mock.patch(
            'app.utils.RHService.post_unlinked_uac') as mocked_post_unlinked_uac, aioresponses(
            passthrough=[str(self.server._root)]) \
                as mocked:

            mocked.get(self.rhsvc_url, payload=self.unlinked_uac_json_en)
            mocked_get_ai_postcode.return_value = self.ai_postcode_results
            mocked_get_ai_uprn.return_value = self.ai_uprn_result
            mocked_post_unlinked_uac.return_value = self.rhsvc_post_linked_uac_en

            mocked.post(self.rhsvc_url_surveylaunched)
            eq_payload = self.eq_payload.copy()
            eq_payload['region_code'] = 'GB-ENG'
            eq_payload['language_code'] = 'en'
            account_service_url = self.app['ACCOUNT_SERVICE_URL']
            url_path_prefix = self.app['URL_PATH_PREFIX']
            url_display_region = '/en'
            eq_payload[
                'account_service_url'] = \
                f'{account_service_url}{url_path_prefix}{url_display_region}{self.account_service_url}'
            eq_payload[
                'account_service_log_out_url'] = \
                f'{account_service_url}{url_path_prefix}{url_display_region}{self.account_service_log_out_url}'
            eq_payload['ru_ref'] = '10023122451'
            eq_payload['display_address'] = '1 Gate Reach, Exeter'

            response = await self.client.request('GET', self.get_start_en)
            self.assertEqual(200, response.status)
            self.assertLogEvent(cm, "received GET on endpoint 'en/start'")

            response = await self.client.request('POST',
                                                 self.post_start_en,
                                                 allow_redirects=True,
                                                 data=self.start_data_valid)

            self.assertLogEvent(cm, "received POST on endpoint 'en/start'")
            self.assertLogEvent(cm, "unlinked case")

            self.assertEqual(200, response.status)
            contents = str(await response.content.read())
            self.assertLogEvent(cm, "received GET on endpoint 'en/start/unlinked/enter-address'")
            self.assertIn(self.ons_logo_en, contents)
            self.assertIn(self.content_start_unlinked_enter_address_title_en, contents)
            self.assertIn(self.content_start_unlinked_enter_address_secondary_en, contents)
            self.assertIn(self.content_start_unlinked_enter_address_question_title_en, contents)

            response = await self.client.request(
                    'POST',
                    self.post_start_unlinked_enter_address_en,
                    data=self.common_postcode_input_valid)
            self.assertLogEvent(cm, 'valid postcode')

            self.assertLogEvent(cm, "received POST on endpoint 'en/start/unlinked/enter-address'")
            self.assertLogEvent(cm, "received GET on endpoint 'en/start/unlinked/select-address'")

            self.assertEqual(200, response.status)
            resp_content = await response.content.read()
            self.assertIn(self.ons_logo_en, str(resp_content))
            self.assertIn(self.content_common_select_address_title_en, str(resp_content))
            self.assertIn(self.content_common_select_address_value_en, str(resp_content))

            response = await self.client.request(
                    'POST',
                    self.post_start_unlinked_select_address_en,
                    data=self.common_select_address_input_valid)
            self.assertLogEvent(cm, "received POST on endpoint 'en/start/unlinked/select-address'")
            self.assertLogEvent(cm, "received GET on endpoint 'en/start/unlinked/confirm-address'")

            self.assertEqual(200, response.status)
            resp_content = await response.content.read()
            self.assertIn(self.ons_logo_en, str(resp_content))
            self.assertIn(self.content_common_confirm_address_title_en, str(resp_content))
            self.assertIn(self.content_common_confirm_address_value_en, str(resp_content))

            response = await self.client.request(
                    'POST',
                    self.post_start_unlinked_confirm_address_en,
                    data=self.common_confirm_address_input_yes)
            self.assertLogEvent(cm, "received POST on endpoint 'en/start/unlinked/confirm-address'")
            self.assertLogEvent(cm, "received GET on endpoint 'en/start/unlinked/address-has-been-linked'")

            self.assertEqual(response.status, 200)
            resp_content = await response.content.read()
            self.assertIn(self.ons_logo_en, str(resp_content))
            self.assertIn(self.content_start_unlinked_address_has_been_linked_title_en, str(resp_content))
            self.assertIn(self.content_start_unlinked_address_has_been_linked_secondary_en, str(resp_content))

            response = await self.client.request(
                'POST',
                self.post_start_unlinked_address_is_linked_en,
                allow_redirects=False,
                data=self.start_address_linked)

            self.assertLogEvent(cm, 'redirecting to eq')

        self.assertEqual(response.status, 302)
        redirected_url = response.headers['location']
        # outputs url on fail
        self.assertTrue(redirected_url.startswith(self.app['EQ_URL']),
                        redirected_url)
        # we only care about the query string
        _, _, _, query, *_ = urlsplit(redirected_url)
        # convert token to dict
        token = json.loads(parse_qs(query)['token'][0])
        # fail early if payload keys differ
        self.assertEqual(eq_payload.keys(), token.keys())
        for key in eq_payload.keys():
            # skip uuid / time generated values
            if key in ['jti', 'tx_id', 'iat', 'exp']:
                continue
            # outputs failed key as msg
            self.assertEqual(eq_payload[key], token[key], key)

    @skip_encrypt
    @unittest_run_loop
    async def test_unlinked_uac_happy_path_cy(self):
        with self.assertLogs('respondent-home', 'INFO') as cm, mock.patch(
                'app.utils.AddressIndex.get_ai_postcode') as mocked_get_ai_postcode, mock.patch(
                'app.utils.AddressIndex.get_ai_uprn') as mocked_get_ai_uprn, mock.patch(
            'app.utils.RHService.post_unlinked_uac') as mocked_post_unlinked_uac, aioresponses(
            passthrough=[str(self.server._root)]) \
                as mocked:

            mocked.get(self.rhsvc_url, payload=self.unlinked_uac_json_cy)
            mocked_get_ai_postcode.return_value = self.ai_postcode_results
            mocked_get_ai_uprn.return_value = self.ai_uprn_result
            mocked_post_unlinked_uac.return_value = self.rhsvc_post_linked_uac_cy

            mocked.post(self.rhsvc_url_surveylaunched)
            eq_payload = self.eq_payload.copy()
            eq_payload['region_code'] = 'GB-WLS'
            eq_payload['language_code'] = 'cy'
            account_service_url = self.app['ACCOUNT_SERVICE_URL']
            url_path_prefix = self.app['URL_PATH_PREFIX']
            url_display_region = '/cy'
            eq_payload[
                'account_service_url'] = \
                f'{account_service_url}{url_path_prefix}{url_display_region}{self.account_service_url}'
            eq_payload[
                'account_service_log_out_url'] = \
                f'{account_service_url}{url_path_prefix}{url_display_region}{self.account_service_log_out_url}'
            eq_payload['ru_ref'] = '10023122451'
            eq_payload['display_address'] = '1 Gate Reach, Exeter'

            response = await self.client.request('GET', self.get_start_cy)
            self.assertEqual(200, response.status)
            self.assertLogEvent(cm, "received GET on endpoint 'cy/start'")

            response = await self.client.request('POST',
                                                 self.post_start_cy,
                                                 allow_redirects=True,
                                                 data=self.start_data_valid)

            self.assertLogEvent(cm, "received POST on endpoint 'cy/start'")
            self.assertLogEvent(cm, "unlinked case")

            self.assertEqual(200, response.status)
            contents = str(await response.content.read())
            self.assertLogEvent(cm, "received GET on endpoint 'cy/start/unlinked/enter-address'")
            self.assertIn(self.ons_logo_cy, contents)
            self.assertIn(self.content_start_unlinked_enter_address_title_cy, contents)
            self.assertIn(self.content_start_unlinked_enter_address_secondary_cy, contents)
            self.assertIn(self.content_start_unlinked_enter_address_question_title_cy, contents)

            response = await self.client.request(
                    'POST',
                    self.post_start_unlinked_enter_address_cy,
                    data=self.common_postcode_input_valid)
            self.assertLogEvent(cm, 'valid postcode')

            self.assertLogEvent(cm, "received POST on endpoint 'cy/start/unlinked/enter-address'")
            self.assertLogEvent(cm, "received GET on endpoint 'cy/start/unlinked/select-address'")

            self.assertEqual(200, response.status)
            resp_content = await response.content.read()
            self.assertIn(self.ons_logo_cy, str(resp_content))
            self.assertIn(self.content_common_select_address_title_cy, str(resp_content))
            self.assertIn(self.content_common_select_address_value_cy, str(resp_content))

            response = await self.client.request(
                    'POST',
                    self.post_start_unlinked_select_address_cy,
                    data=self.common_select_address_input_valid)
            self.assertLogEvent(cm, "received POST on endpoint 'cy/start/unlinked/select-address'")
            self.assertLogEvent(cm, "received GET on endpoint 'cy/start/unlinked/confirm-address'")

            self.assertEqual(200, response.status)
            resp_content = await response.content.read()
            self.assertIn(self.ons_logo_cy, str(resp_content))
            self.assertIn(self.content_common_confirm_address_title_cy, str(resp_content))
            self.assertIn(self.content_common_confirm_address_value_cy, str(resp_content))

            response = await self.client.request(
                    'POST',
                    self.post_start_unlinked_confirm_address_cy,
                    data=self.common_confirm_address_input_yes)
            self.assertLogEvent(cm, "received POST on endpoint 'cy/start/unlinked/confirm-address'")
            self.assertLogEvent(cm, "received GET on endpoint 'cy/start/unlinked/address-has-been-linked'")

            self.assertEqual(response.status, 200)
            resp_content = await response.content.read()
            self.assertIn(self.ons_logo_cy, str(resp_content))
            self.assertIn(self.content_start_unlinked_address_has_been_linked_title_cy, str(resp_content))
            self.assertIn(self.content_start_unlinked_address_has_been_linked_secondary_cy, str(resp_content))

            response = await self.client.request(
                'POST',
                self.post_start_unlinked_address_is_linked_cy,
                allow_redirects=False,
                data=self.start_address_linked)

            self.assertLogEvent(cm, 'redirecting to eq')

        self.assertEqual(response.status, 302)
        redirected_url = response.headers['location']
        # outputs url on fail
        self.assertTrue(redirected_url.startswith(self.app['EQ_URL']),
                        redirected_url)
        # we only care about the query string
        _, _, _, query, *_ = urlsplit(redirected_url)
        # convert token to dict
        token = json.loads(parse_qs(query)['token'][0])
        # fail early if payload keys differ
        self.assertEqual(eq_payload.keys(), token.keys())
        for key in eq_payload.keys():
            # skip uuid / time generated values
            if key in ['jti', 'tx_id', 'iat', 'exp']:
                continue
            # outputs failed key as msg
            self.assertEqual(eq_payload[key], token[key], key)

    @skip_encrypt
    @unittest_run_loop
    async def test_unlinked_uac_happy_path_ni(self):
        with self.assertLogs('respondent-home', 'INFO') as cm, mock.patch(
                'app.utils.AddressIndex.get_ai_postcode') as mocked_get_ai_postcode, mock.patch(
                'app.utils.AddressIndex.get_ai_uprn') as mocked_get_ai_uprn, mock.patch(
            'app.utils.RHService.post_unlinked_uac') as mocked_post_unlinked_uac, aioresponses(
            passthrough=[str(self.server._root)]) \
                as mocked:

            mocked.get(self.rhsvc_url, payload=self.unlinked_uac_json_ni)
            mocked_get_ai_postcode.return_value = self.ai_postcode_results
            mocked_get_ai_uprn.return_value = self.ai_uprn_result
            mocked_post_unlinked_uac.return_value = self.rhsvc_post_linked_uac_ni

            mocked.post(self.rhsvc_url_surveylaunched)
            eq_payload = self.eq_payload.copy()
            eq_payload['region_code'] = 'GB-NIR'
            eq_payload['language_code'] = 'en'
            account_service_url = self.app['ACCOUNT_SERVICE_URL']
            url_path_prefix = self.app['URL_PATH_PREFIX']
            url_display_region = '/ni'
            eq_payload[
                'account_service_url'] = \
                f'{account_service_url}{url_path_prefix}{url_display_region}{self.account_service_url}'
            eq_payload[
                'account_service_log_out_url'] = \
                f'{account_service_url}{url_path_prefix}{url_display_region}{self.account_service_log_out_url}'
            eq_payload['ru_ref'] = '10023122451'
            eq_payload['display_address'] = '1 Gate Reach, Exeter'

            response = await self.client.request('GET', self.get_start_ni)
            self.assertEqual(200, response.status)
            self.assertLogEvent(cm, "received GET on endpoint 'ni/start'")

            response = await self.client.request('POST',
                                                 self.post_start_ni,
                                                 allow_redirects=True,
                                                 data=self.start_data_valid)

            self.assertLogEvent(cm, "received POST on endpoint 'ni/start'")
            self.assertLogEvent(cm, "unlinked case")

            self.assertEqual(200, response.status)
            contents = str(await response.content.read())
            self.assertLogEvent(cm, "received GET on endpoint 'ni/start/unlinked/enter-address'")
            self.assertIn(self.nisra_logo, contents)
            self.assertIn(self.content_start_unlinked_enter_address_title_en, contents)
            self.assertIn(self.content_start_unlinked_enter_address_secondary_en, contents)
            self.assertIn(self.content_start_unlinked_enter_address_question_title_en, contents)

            response = await self.client.request(
                    'POST',
                    self.post_start_unlinked_enter_address_ni,
                    data=self.common_postcode_input_valid)
            self.assertLogEvent(cm, 'valid postcode')

            self.assertLogEvent(cm, "received POST on endpoint 'ni/start/unlinked/enter-address'")
            self.assertLogEvent(cm, "received GET on endpoint 'ni/start/unlinked/select-address'")

            self.assertEqual(200, response.status)
            resp_content = await response.content.read()
            self.assertIn(self.nisra_logo, str(resp_content))
            self.assertIn(self.content_common_select_address_title_en, str(resp_content))
            self.assertIn(self.content_common_select_address_value_en, str(resp_content))

            response = await self.client.request(
                    'POST',
                    self.post_start_unlinked_select_address_ni,
                    data=self.common_select_address_input_valid)
            self.assertLogEvent(cm, "received POST on endpoint 'ni/start/unlinked/select-address'")
            self.assertLogEvent(cm, "received GET on endpoint 'ni/start/unlinked/confirm-address'")

            self.assertEqual(200, response.status)
            resp_content = await response.content.read()
            self.assertIn(self.nisra_logo, str(resp_content))
            self.assertIn(self.content_common_confirm_address_title_en, str(resp_content))
            self.assertIn(self.content_common_confirm_address_value_en, str(resp_content))

            response = await self.client.request(
                    'POST',
                    self.post_start_unlinked_confirm_address_ni,
                    data=self.common_confirm_address_input_yes)
            self.assertLogEvent(cm, "received POST on endpoint 'ni/start/unlinked/confirm-address'")
            self.assertLogEvent(cm, "received GET on endpoint 'ni/start/unlinked/address-has-been-linked'")

            self.assertEqual(response.status, 200)
            resp_content = await response.content.read()
            self.assertIn(self.nisra_logo, str(resp_content))
            self.assertIn(self.content_start_unlinked_address_has_been_linked_title_en, str(resp_content))
            self.assertIn(self.content_start_unlinked_address_has_been_linked_secondary_en, str(resp_content))

            response = await self.client.request(
                'POST',
                self.post_start_unlinked_address_is_linked_ni,
                data=self.start_address_linked)
            self.assertLogEvent(cm, "received POST on endpoint 'ni/start/unlinked/address-has-been-linked'")
            self.assertLogEvent(cm, "received GET on endpoint 'ni/start/language-options'")

            self.assertEqual(response.status, 200)
            resp_content = await response.content.read()
            self.assertIn(self.nisra_logo, str(resp_content))
            self.assertIn(self.content_start_ni_language_options_title, str(resp_content))
            self.assertIn(self.content_start_ni_language_options_option_yes, str(resp_content))

            response = await self.client.request(
                'POST',
                self.post_start_language_options_ni,
                allow_redirects=False,
                data=self.start_ni_language_option_data_yes)

            self.assertLogEvent(cm, "received POST on endpoint 'ni/start/language-options'")
            self.assertLogEvent(cm, 'redirecting to eq')

        self.assertEqual(response.status, 302)
        redirected_url = response.headers['location']
        # outputs url on fail
        self.assertTrue(redirected_url.startswith(self.app['EQ_URL']),
                        redirected_url)
        # we only care about the query string
        _, _, _, query, *_ = urlsplit(redirected_url)
        # convert token to dict
        token = json.loads(parse_qs(query)['token'][0])
        # fail early if payload keys differ
        self.assertEqual(eq_payload.keys(), token.keys())
        for key in eq_payload.keys():
            # skip uuid / time generated values
            if key in ['jti', 'tx_id', 'iat', 'exp']:
                continue
            # outputs failed key as msg
            self.assertEqual(eq_payload[key], token[key], key)

    @unittest_run_loop
    async def test_unlinked_address_in_scotland_en(self):
        with self.assertLogs('respondent-home', 'INFO') as cm, mock.patch(
                'app.utils.AddressIndex.get_ai_postcode') as mocked_get_ai_postcode, mock.patch(
                'app.utils.AddressIndex.get_ai_uprn') as mocked_get_ai_uprn, aioresponses(
            passthrough=[str(self.server._root)]) \
                as mocked:

            mocked.get(self.rhsvc_url, payload=self.unlinked_uac_json_en)
            mocked_get_ai_postcode.return_value = self.ai_postcode_results
            mocked_get_ai_uprn.return_value = self.ai_uprn_result_scotland

            await self.client.request('GET', self.get_start_en)
            self.assertLogEvent(cm, "received GET on endpoint 'en/start'")

            await self.client.request('POST',
                                      self.post_start_en,
                                      allow_redirects=True,
                                      data=self.start_data_valid)

            self.assertLogEvent(cm, "received POST on endpoint 'en/start'")
            self.assertLogEvent(cm, "received GET on endpoint 'en/start/unlinked/enter-address'")

            await self.client.request(
                    'POST',
                    self.post_start_unlinked_enter_address_en,
                    data=self.common_postcode_input_valid)

            self.assertLogEvent(cm, "received POST on endpoint 'en/start/unlinked/enter-address'")
            self.assertLogEvent(cm, "received GET on endpoint 'en/start/unlinked/select-address'")

            await self.client.request(
                    'POST',
                    self.post_start_unlinked_select_address_en,
                    data=self.common_select_address_input_valid)
            self.assertLogEvent(cm, "received POST on endpoint 'en/start/unlinked/select-address'")
            self.assertLogEvent(cm, "received GET on endpoint 'en/start/unlinked/confirm-address'")

            response = await self.client.request(
                    'POST',
                    self.post_start_unlinked_confirm_address_en,
                    data=self.common_confirm_address_input_yes)
            self.assertLogEvent(cm, "received POST on endpoint 'en/start/unlinked/confirm-address'")
            self.assertLogEvent(cm, "received GET on endpoint 'en/start/address-in-scotland'")

            self.assertEqual(response.status, 200)
            resp_content = await response.content.read()
            self.assertIn(self.ons_logo_en, str(resp_content))
            self.assertIn(self.content_common_address_in_scotland_en, str(resp_content))

    @unittest_run_loop
    async def test_unlinked_address_in_scotland_cy(self):
        with self.assertLogs('respondent-home', 'INFO') as cm, mock.patch(
                'app.utils.AddressIndex.get_ai_postcode') as mocked_get_ai_postcode, mock.patch(
                'app.utils.AddressIndex.get_ai_uprn') as mocked_get_ai_uprn, aioresponses(
            passthrough=[str(self.server._root)]) \
                as mocked:

            mocked.get(self.rhsvc_url, payload=self.unlinked_uac_json_cy)
            mocked_get_ai_postcode.return_value = self.ai_postcode_results
            mocked_get_ai_uprn.return_value = self.ai_uprn_result_scotland

            await self.client.request('GET', self.get_start_cy)
            self.assertLogEvent(cm, "received GET on endpoint 'cy/start'")

            await self.client.request('POST',
                                      self.post_start_cy,
                                      allow_redirects=True,
                                      data=self.start_data_valid)

            self.assertLogEvent(cm, "received POST on endpoint 'cy/start'")
            self.assertLogEvent(cm, "received GET on endpoint 'cy/start/unlinked/enter-address'")

            await self.client.request(
                    'POST',
                    self.post_start_unlinked_enter_address_cy,
                    data=self.common_postcode_input_valid)

            self.assertLogEvent(cm, "received POST on endpoint 'cy/start/unlinked/enter-address'")
            self.assertLogEvent(cm, "received GET on endpoint 'cy/start/unlinked/select-address'")

            await self.client.request(
                    'POST',
                    self.post_start_unlinked_select_address_cy,
                    data=self.common_select_address_input_valid)
            self.assertLogEvent(cm, "received POST on endpoint 'cy/start/unlinked/select-address'")
            self.assertLogEvent(cm, "received GET on endpoint 'cy/start/unlinked/confirm-address'")

            response = await self.client.request(
                    'POST',
                    self.post_start_unlinked_confirm_address_cy,
                    data=self.common_confirm_address_input_yes)
            self.assertLogEvent(cm, "received POST on endpoint 'cy/start/unlinked/confirm-address'")
            self.assertLogEvent(cm, "received GET on endpoint 'cy/start/address-in-scotland'")

            self.assertEqual(response.status, 200)
            resp_content = await response.content.read()
            self.assertIn(self.ons_logo_cy, str(resp_content))
            self.assertIn(self.content_common_address_in_scotland_cy, str(resp_content))

    @unittest_run_loop
    async def test_unlinked_address_in_scotland_ni(self):
        with self.assertLogs('respondent-home', 'INFO') as cm, mock.patch(
                'app.utils.AddressIndex.get_ai_postcode') as mocked_get_ai_postcode, mock.patch(
                'app.utils.AddressIndex.get_ai_uprn') as mocked_get_ai_uprn, aioresponses(
            passthrough=[str(self.server._root)]) \
                as mocked:

            mocked.get(self.rhsvc_url, payload=self.unlinked_uac_json_ni)
            mocked_get_ai_postcode.return_value = self.ai_postcode_results
            mocked_get_ai_uprn.return_value = self.ai_uprn_result_scotland

            await self.client.request('GET', self.get_start_ni)
            self.assertLogEvent(cm, "received GET on endpoint 'ni/start'")

            await self.client.request('POST',
                                      self.post_start_ni,
                                      allow_redirects=True,
                                      data=self.start_data_valid)

            self.assertLogEvent(cm, "received POST on endpoint 'ni/start'")
            self.assertLogEvent(cm, "received GET on endpoint 'ni/start/unlinked/enter-address'")

            await self.client.request(
                    'POST',
                    self.post_start_unlinked_enter_address_ni,
                    data=self.common_postcode_input_valid)

            self.assertLogEvent(cm, "received POST on endpoint 'ni/start/unlinked/enter-address'")
            self.assertLogEvent(cm, "received GET on endpoint 'ni/start/unlinked/select-address'")

            await self.client.request(
                    'POST',
                    self.post_start_unlinked_select_address_ni,
                    data=self.common_select_address_input_valid)
            self.assertLogEvent(cm, "received POST on endpoint 'ni/start/unlinked/select-address'")
            self.assertLogEvent(cm, "received GET on endpoint 'ni/start/unlinked/confirm-address'")

            response = await self.client.request(
                    'POST',
                    self.post_start_unlinked_confirm_address_ni,
                    data=self.common_confirm_address_input_yes)
            self.assertLogEvent(cm, "received POST on endpoint 'ni/start/unlinked/confirm-address'")
            self.assertLogEvent(cm, "received GET on endpoint 'ni/start/address-in-scotland'")

            self.assertEqual(response.status, 200)
            resp_content = await response.content.read()
            self.assertIn(self.nisra_logo, str(resp_content))
            self.assertIn(self.content_common_address_in_scotland_en, str(resp_content))

    @unittest_run_loop
    async def test_unlinked_address_not_listed_en(self):
        with self.assertLogs('respondent-home', 'INFO') as cm, mock.patch(
                'app.utils.AddressIndex.get_ai_postcode') as mocked_get_ai_postcode, aioresponses(
            passthrough=[str(self.server._root)]) \
                as mocked:

            mocked.get(self.rhsvc_url, payload=self.unlinked_uac_json_en)
            mocked_get_ai_postcode.return_value = self.ai_postcode_results

            await self.client.request('GET', self.get_start_en)
            self.assertLogEvent(cm, "received GET on endpoint 'en/start'")

            await self.client.request('POST',
                                      self.post_start_en,
                                      allow_redirects=True,
                                      data=self.start_data_valid)

            self.assertLogEvent(cm, "received POST on endpoint 'en/start'")
            self.assertLogEvent(cm, "received GET on endpoint 'en/start/unlinked/enter-address'")

            await self.client.request(
                    'POST',
                    self.post_start_unlinked_enter_address_en,
                    data=self.common_postcode_input_valid)

            self.assertLogEvent(cm, "received POST on endpoint 'en/start/unlinked/enter-address'")
            self.assertLogEvent(cm, "received GET on endpoint 'en/start/unlinked/select-address'")

            response = await self.client.request(
                    'POST',
                    self.post_start_unlinked_select_address_en,
                    data=self.common_select_address_input_not_listed_en)
            self.assertLogEvent(cm, "received POST on endpoint 'en/start/unlinked/select-address'")
            self.assertLogEvent(cm, "received GET on endpoint 'en/start/call-contact-centre/address-not-found'")

            self.assertEqual(200, response.status)
            resp_content = await response.content.read()
            self.assertIn(self.ons_logo_en, str(resp_content))
            self.assertIn(self.content_common_call_contact_centre_title_en, str(resp_content))
            self.assertIn(self.content_common_call_contact_centre_address_not_found_en, str(resp_content))

    @unittest_run_loop
    async def test_unlinked_address_not_listed_cy(self):
        with self.assertLogs('respondent-home', 'INFO') as cm, mock.patch(
                'app.utils.AddressIndex.get_ai_postcode') as mocked_get_ai_postcode, aioresponses(
            passthrough=[str(self.server._root)]) \
                as mocked:

            mocked.get(self.rhsvc_url, payload=self.unlinked_uac_json_cy)
            mocked_get_ai_postcode.return_value = self.ai_postcode_results

            await self.client.request('GET', self.get_start_cy)
            self.assertLogEvent(cm, "received GET on endpoint 'cy/start'")

            await self.client.request('POST',
                                      self.post_start_cy,
                                      allow_redirects=True,
                                      data=self.start_data_valid)

            self.assertLogEvent(cm, "received POST on endpoint 'cy/start'")
            self.assertLogEvent(cm, "received GET on endpoint 'cy/start/unlinked/enter-address'")

            await self.client.request(
                    'POST',
                    self.post_start_unlinked_enter_address_cy,
                    data=self.common_postcode_input_valid)

            self.assertLogEvent(cm, "received POST on endpoint 'cy/start/unlinked/enter-address'")
            self.assertLogEvent(cm, "received GET on endpoint 'cy/start/unlinked/select-address'")

            response = await self.client.request(
                    'POST',
                    self.post_start_unlinked_select_address_cy,
                    data=self.common_select_address_input_not_listed_cy)
            self.assertLogEvent(cm, "received POST on endpoint 'cy/start/unlinked/select-address'")
            self.assertLogEvent(cm, "received GET on endpoint 'cy/start/call-contact-centre/address-not-found'")

            self.assertEqual(200, response.status)
            resp_content = await response.content.read()
            self.assertIn(self.ons_logo_cy, str(resp_content))
            self.assertIn(self.content_common_call_contact_centre_title_cy, str(resp_content))
            self.assertIn(self.content_common_call_contact_centre_address_not_found_cy, str(resp_content))

    @unittest_run_loop
    async def test_unlinked_address_not_listed_ni(self):
        with self.assertLogs('respondent-home', 'INFO') as cm, mock.patch(
                'app.utils.AddressIndex.get_ai_postcode') as mocked_get_ai_postcode, aioresponses(
            passthrough=[str(self.server._root)]) \
                as mocked:

            mocked.get(self.rhsvc_url, payload=self.unlinked_uac_json_ni)
            mocked_get_ai_postcode.return_value = self.ai_postcode_results

            await self.client.request('GET', self.get_start_ni)
            self.assertLogEvent(cm, "received GET on endpoint 'ni/start'")

            await self.client.request('POST',
                                      self.post_start_ni,
                                      allow_redirects=True,
                                      data=self.start_data_valid)

            self.assertLogEvent(cm, "received POST on endpoint 'ni/start'")
            self.assertLogEvent(cm, "received GET on endpoint 'ni/start/unlinked/enter-address'")

            await self.client.request(
                    'POST',
                    self.post_start_unlinked_enter_address_ni,
                    data=self.common_postcode_input_valid)
            self.assertLogEvent(cm, "received POST on endpoint 'ni/start/unlinked/enter-address'")
            self.assertLogEvent(cm, "received GET on endpoint 'ni/start/unlinked/select-address'")

            response = await self.client.request(
                    'POST',
                    self.post_start_unlinked_select_address_ni,
                    data=self.common_select_address_input_not_listed_en)
            self.assertLogEvent(cm, "received POST on endpoint 'ni/start/unlinked/select-address'")
            self.assertLogEvent(cm, "received GET on endpoint 'ni/start/call-contact-centre/address-not-found'")

            self.assertEqual(200, response.status)
            resp_content = await response.content.read()
            self.assertIn(self.nisra_logo, str(resp_content))
            self.assertIn(self.content_common_call_contact_centre_title_en, str(resp_content))
            self.assertIn(self.content_common_call_contact_centre_address_not_found_en, str(resp_content))

    @unittest_run_loop
    async def test_post_start_unlinked_enter_address_bad_postcode_en(
            self):

        with self.assertLogs('respondent-home', 'INFO') as cm, aioresponses(
            passthrough=[str(self.server._root)]
        ) as mocked:

            mocked.get(self.rhsvc_url, payload=self.unlinked_uac_json_en)

            await self.client.request('GET', self.get_start_en)

            await self.client.request('POST',
                                      self.post_start_en,
                                      allow_redirects=True,
                                      data=self.start_data_valid)

            self.assertLogEvent(cm, "received POST on endpoint 'en/start'")
            self.assertLogEvent(cm, "unlinked case")

            response = await self.client.request(
                'POST',
                self.post_start_unlinked_enter_address_en,
                data=self.common_postcode_input_invalid)
        self.assertLogEvent(cm, 'invalid postcode')
        self.assertLogEvent(cm, "received POST on endpoint 'en/start/unlinked/enter-address'")

        self.assertEqual(response.status, 200)
        contents = str(await response.content.read())
        self.assertIn(self.ons_logo_en, contents)
        self.assertIn(self.content_start_unlinked_enter_address_title_en, contents)
        self.assertIn(self.content_start_unlinked_enter_address_secondary_en, contents)
        self.assertIn(self.content_start_unlinked_enter_address_question_title_en, contents)
        self.assertIn(self.content_common_enter_address_error_en, contents)

    @unittest_run_loop
    async def test_post_start_unlinked_enter_address_bad_postcode_cy(
            self):

        with self.assertLogs('respondent-home', 'INFO') as cm, aioresponses(
            passthrough=[str(self.server._root)]
        ) as mocked:

            mocked.get(self.rhsvc_url, payload=self.unlinked_uac_json_cy)

            await self.client.request('GET', self.get_start_cy)

            await self.client.request('POST',
                                      self.post_start_cy,
                                      allow_redirects=True,
                                      data=self.start_data_valid)

            self.assertLogEvent(cm, "received POST on endpoint 'cy/start'")
            self.assertLogEvent(cm, "unlinked case")

            response = await self.client.request(
                'POST',
                self.post_start_unlinked_enter_address_cy,
                data=self.common_postcode_input_invalid)
        self.assertLogEvent(cm, 'invalid postcode')
        self.assertLogEvent(cm, "received POST on endpoint 'cy/start/unlinked/enter-address'")

        self.assertEqual(response.status, 200)
        contents = str(await response.content.read())
        self.assertIn(self.ons_logo_cy, contents)
        self.assertIn(self.content_start_unlinked_enter_address_title_cy, contents)
        self.assertIn(self.content_start_unlinked_enter_address_secondary_cy, contents)
        self.assertIn(self.content_start_unlinked_enter_address_question_title_cy, contents)
        self.assertIn(self.content_common_enter_address_error_cy, contents)

    @unittest_run_loop
    async def test_post_start_unlinked_enter_address_bad_postcode_ni(
            self):

        with self.assertLogs('respondent-home', 'INFO') as cm, aioresponses(
            passthrough=[str(self.server._root)]
        ) as mocked:

            mocked.get(self.rhsvc_url, payload=self.unlinked_uac_json_ni)

            await self.client.request('GET', self.get_start_ni)

            await self.client.request('POST',
                                      self.post_start_ni,
                                      allow_redirects=True,
                                      data=self.start_data_valid)

            self.assertLogEvent(cm, "received POST on endpoint 'ni/start'")
            self.assertLogEvent(cm, "unlinked case")

            response = await self.client.request(
                'POST',
                self.post_start_unlinked_enter_address_ni,
                data=self.common_postcode_input_invalid)
        self.assertLogEvent(cm, 'invalid postcode')
        self.assertLogEvent(cm, "received POST on endpoint 'ni/start/unlinked/enter-address'")

        self.assertEqual(response.status, 200)
        contents = str(await response.content.read())
        self.assertIn(self.nisra_logo, contents)
        self.assertIn(self.content_start_unlinked_enter_address_title_en, contents)
        self.assertIn(self.content_start_unlinked_enter_address_secondary_en, contents)
        self.assertIn(self.content_start_unlinked_enter_address_question_title_en, contents)
        self.assertIn(self.content_common_enter_address_error_en, contents)

    @unittest_run_loop
    async def test_unlinked_no_address_selected_en(self):
        with self.assertLogs('respondent-home', 'INFO') as cm, mock.patch(
                'app.utils.AddressIndex.get_ai_postcode') as mocked_get_ai_postcode, aioresponses(
            passthrough=[str(self.server._root)]) \
                as mocked:

            mocked.get(self.rhsvc_url, payload=self.unlinked_uac_json_en)
            mocked_get_ai_postcode.return_value = self.ai_postcode_results

            await self.client.request('GET', self.get_start_en)
            self.assertLogEvent(cm, "received GET on endpoint 'en/start'")

            await self.client.request('POST',
                                      self.post_start_en,
                                      allow_redirects=True,
                                      data=self.start_data_valid)

            self.assertLogEvent(cm, "received POST on endpoint 'en/start'")
            self.assertLogEvent(cm, "received GET on endpoint 'en/start/unlinked/enter-address'")

            await self.client.request(
                    'POST',
                    self.post_start_unlinked_enter_address_en,
                    data=self.common_postcode_input_valid)

            self.assertLogEvent(cm, "received POST on endpoint 'en/start/unlinked/enter-address'")
            self.assertLogEvent(cm, "received GET on endpoint 'en/start/unlinked/select-address'")

            response = await self.client.request(
                    'POST',
                    self.post_start_unlinked_select_address_en,
                    data=self.common_form_data_empty)
            self.assertLogEvent(cm, "received POST on endpoint 'en/start/unlinked/select-address'")

            self.assertEqual(200, response.status)
            resp_content = await response.content.read()
            self.assertIn(self.ons_logo_en, str(resp_content))
            self.assertIn(self.content_common_select_address_title_en, str(resp_content))
            self.assertIn(self.content_common_select_address_error_en, str(resp_content))
            self.assertIn(self.content_common_select_address_value_en, str(resp_content))

    @unittest_run_loop
    async def test_unlinked_no_address_selected_cy(self):
        with self.assertLogs('respondent-home', 'INFO') as cm, mock.patch(
                'app.utils.AddressIndex.get_ai_postcode') as mocked_get_ai_postcode, aioresponses(
            passthrough=[str(self.server._root)]) \
                as mocked:

            mocked.get(self.rhsvc_url, payload=self.unlinked_uac_json_cy)
            mocked_get_ai_postcode.return_value = self.ai_postcode_results

            await self.client.request('GET', self.get_start_cy)
            self.assertLogEvent(cm, "received GET on endpoint 'cy/start'")

            await self.client.request('POST',
                                      self.post_start_cy,
                                      allow_redirects=True,
                                      data=self.start_data_valid)

            self.assertLogEvent(cm, "received POST on endpoint 'cy/start'")
            self.assertLogEvent(cm, "received GET on endpoint 'cy/start/unlinked/enter-address'")

            await self.client.request(
                    'POST',
                    self.post_start_unlinked_enter_address_cy,
                    data=self.common_postcode_input_valid)

            self.assertLogEvent(cm, "received POST on endpoint 'cy/start/unlinked/enter-address'")
            self.assertLogEvent(cm, "received GET on endpoint 'cy/start/unlinked/select-address'")

            response = await self.client.request(
                    'POST',
                    self.post_start_unlinked_select_address_cy,
                    data=self.common_form_data_empty)
            self.assertLogEvent(cm, "received POST on endpoint 'cy/start/unlinked/select-address'")

            self.assertEqual(200, response.status)
            resp_content = await response.content.read()
            self.assertIn(self.ons_logo_cy, str(resp_content))
            self.assertIn(self.content_common_select_address_title_cy, str(resp_content))
            self.assertIn(self.content_common_select_address_error_cy, str(resp_content))
            self.assertIn(self.content_common_select_address_value_cy, str(resp_content))

    @unittest_run_loop
    async def test_unlinked_no_address_selected_ni(self):
        with self.assertLogs('respondent-home', 'INFO') as cm, mock.patch(
                'app.utils.AddressIndex.get_ai_postcode') as mocked_get_ai_postcode, aioresponses(
            passthrough=[str(self.server._root)]) \
                as mocked:

            mocked.get(self.rhsvc_url, payload=self.unlinked_uac_json_ni)
            mocked_get_ai_postcode.return_value = self.ai_postcode_results

            await self.client.request('GET', self.get_start_ni)
            self.assertLogEvent(cm, "received GET on endpoint 'ni/start'")

            await self.client.request('POST',
                                      self.post_start_ni,
                                      allow_redirects=True,
                                      data=self.start_data_valid)

            self.assertLogEvent(cm, "received POST on endpoint 'ni/start'")
            self.assertLogEvent(cm, "received GET on endpoint 'ni/start/unlinked/enter-address'")

            await self.client.request(
                    'POST',
                    self.post_start_unlinked_enter_address_ni,
                    data=self.common_postcode_input_valid)
            self.assertLogEvent(cm, "received POST on endpoint 'ni/start/unlinked/enter-address'")
            self.assertLogEvent(cm, "received GET on endpoint 'ni/start/unlinked/select-address'")

            response = await self.client.request(
                    'POST',
                    self.post_start_unlinked_select_address_ni,
                    data=self.common_form_data_empty)
            self.assertLogEvent(cm, "received POST on endpoint 'ni/start/unlinked/select-address'")

            self.assertEqual(200, response.status)
            resp_content = await response.content.read()
            self.assertIn(self.nisra_logo, str(resp_content))
            self.assertIn(self.content_common_select_address_title_en, str(resp_content))
            self.assertIn(self.content_common_select_address_error_en, str(resp_content))
            self.assertIn(self.content_common_select_address_value_en, str(resp_content))

    @unittest_run_loop
    async def test_unlinked_confirm_address_no_en(self):
        with self.assertLogs('respondent-home', 'INFO') as cm, mock.patch(
                'app.utils.AddressIndex.get_ai_postcode') as mocked_get_ai_postcode, aioresponses(
            passthrough=[str(self.server._root)]) \
                as mocked:

            mocked.get(self.rhsvc_url, payload=self.unlinked_uac_json_en)
            mocked_get_ai_postcode.return_value = self.ai_postcode_results

            await self.client.request('GET', self.get_start_en)
            self.assertLogEvent(cm, "received GET on endpoint 'en/start'")

            await self.client.request('POST',
                                      self.post_start_en,
                                      allow_redirects=True,
                                      data=self.start_data_valid)

            self.assertLogEvent(cm, "received POST on endpoint 'en/start'")
            self.assertLogEvent(cm, "received GET on endpoint 'en/start/unlinked/enter-address'")

            await self.client.request(
                    'POST',
                    self.post_start_unlinked_enter_address_en,
                    data=self.common_postcode_input_valid)

            self.assertLogEvent(cm, "received POST on endpoint 'en/start/unlinked/enter-address'")
            self.assertLogEvent(cm, "received GET on endpoint 'en/start/unlinked/select-address'")

            await self.client.request(
                    'POST',
                    self.post_start_unlinked_select_address_en,
                    data=self.common_select_address_input_valid)
            self.assertLogEvent(cm, "received POST on endpoint 'en/start/unlinked/select-address'")
            self.assertLogEvent(cm, "received GET on endpoint 'en/start/unlinked/confirm-address'")

            response = await self.client.request(
                    'POST',
                    self.post_start_unlinked_confirm_address_en,
                    data=self.common_confirm_address_input_no)
            self.assertLogEvent(cm, "received POST on endpoint 'en/start/unlinked/confirm-address'")
            self.assertLogEvent(cm, "received GET on endpoint 'en/start/unlinked/enter-address'")

            self.assertEqual(200, response.status)
            resp_content = await response.content.read()
            self.assertIn(self.ons_logo_en, str(resp_content))
            self.assertIn(self.content_start_unlinked_enter_address_title_en, str(resp_content))
            self.assertIn(self.content_start_unlinked_enter_address_secondary_en, str(resp_content))
            self.assertIn(self.content_start_unlinked_enter_address_question_title_en, str(resp_content))

    @unittest_run_loop
    async def test_unlinked_confirm_address_no_cy(self):
        with self.assertLogs('respondent-home', 'INFO') as cm, mock.patch(
                'app.utils.AddressIndex.get_ai_postcode') as mocked_get_ai_postcode, aioresponses(
            passthrough=[str(self.server._root)]) \
                as mocked:

            mocked.get(self.rhsvc_url, payload=self.unlinked_uac_json_cy)
            mocked_get_ai_postcode.return_value = self.ai_postcode_results

            await self.client.request('GET', self.get_start_cy)
            self.assertLogEvent(cm, "received GET on endpoint 'cy/start'")

            await self.client.request('POST',
                                      self.post_start_cy,
                                      allow_redirects=True,
                                      data=self.start_data_valid)

            self.assertLogEvent(cm, "received POST on endpoint 'cy/start'")
            self.assertLogEvent(cm, "received GET on endpoint 'cy/start/unlinked/enter-address'")

            await self.client.request(
                    'POST',
                    self.post_start_unlinked_enter_address_cy,
                    data=self.common_postcode_input_valid)

            self.assertLogEvent(cm, "received POST on endpoint 'cy/start/unlinked/enter-address'")
            self.assertLogEvent(cm, "received GET on endpoint 'cy/start/unlinked/select-address'")

            await self.client.request(
                    'POST',
                    self.post_start_unlinked_select_address_cy,
                    data=self.common_select_address_input_valid)
            self.assertLogEvent(cm, "received POST on endpoint 'cy/start/unlinked/select-address'")
            self.assertLogEvent(cm, "received GET on endpoint 'cy/start/unlinked/confirm-address'")

            response = await self.client.request(
                    'POST',
                    self.post_start_unlinked_confirm_address_cy,
                    data=self.common_confirm_address_input_no)
            self.assertLogEvent(cm, "received POST on endpoint 'cy/start/unlinked/confirm-address'")
            self.assertLogEvent(cm, "received GET on endpoint 'cy/start/unlinked/enter-address'")

            self.assertEqual(200, response.status)
            resp_content = await response.content.read()
            self.assertIn(self.ons_logo_cy, str(resp_content))
            self.assertIn(self.content_start_unlinked_enter_address_title_cy, str(resp_content))
            self.assertIn(self.content_start_unlinked_enter_address_secondary_cy, str(resp_content))
            self.assertIn(self.content_start_unlinked_enter_address_question_title_cy, str(resp_content))

    @unittest_run_loop
    async def test_unlinked_confirm_address_no_ni(self):
        with self.assertLogs('respondent-home', 'INFO') as cm, mock.patch(
                'app.utils.AddressIndex.get_ai_postcode') as mocked_get_ai_postcode, aioresponses(
            passthrough=[str(self.server._root)]) \
                as mocked:

            mocked.get(self.rhsvc_url, payload=self.unlinked_uac_json_ni)
            mocked_get_ai_postcode.return_value = self.ai_postcode_results

            await self.client.request('GET', self.get_start_ni)
            self.assertLogEvent(cm, "received GET on endpoint 'ni/start'")

            await self.client.request('POST',
                                      self.post_start_ni,
                                      allow_redirects=True,
                                      data=self.start_data_valid)

            self.assertLogEvent(cm, "received POST on endpoint 'ni/start'")
            self.assertLogEvent(cm, "received GET on endpoint 'ni/start/unlinked/enter-address'")

            await self.client.request(
                    'POST',
                    self.post_start_unlinked_enter_address_ni,
                    data=self.common_postcode_input_valid)

            self.assertLogEvent(cm, "received POST on endpoint 'ni/start/unlinked/enter-address'")
            self.assertLogEvent(cm, "received GET on endpoint 'ni/start/unlinked/select-address'")

            await self.client.request(
                    'POST',
                    self.post_start_unlinked_select_address_ni,
                    data=self.common_select_address_input_valid)
            self.assertLogEvent(cm, "received POST on endpoint 'ni/start/unlinked/select-address'")
            self.assertLogEvent(cm, "received GET on endpoint 'ni/start/unlinked/confirm-address'")

            response = await self.client.request(
                    'POST',
                    self.post_start_unlinked_confirm_address_ni,
                    data=self.common_confirm_address_input_no)
            self.assertLogEvent(cm, "received POST on endpoint 'ni/start/unlinked/confirm-address'")
            self.assertLogEvent(cm, "received GET on endpoint 'ni/start/unlinked/enter-address'")

            self.assertEqual(200, response.status)
            resp_content = await response.content.read()
            self.assertIn(self.nisra_logo, str(resp_content))
            self.assertIn(self.content_start_unlinked_enter_address_title_en, str(resp_content))
            self.assertIn(self.content_start_unlinked_enter_address_secondary_en, str(resp_content))
            self.assertIn(self.content_start_unlinked_enter_address_question_title_en, str(resp_content))

    @unittest_run_loop
    async def test_unlinked_confirm_address_invalid_en(self):
        with self.assertLogs('respondent-home', 'INFO') as cm, mock.patch(
                'app.utils.AddressIndex.get_ai_postcode') as mocked_get_ai_postcode, aioresponses(
            passthrough=[str(self.server._root)]) \
                as mocked:

            mocked.get(self.rhsvc_url, payload=self.unlinked_uac_json_en)
            mocked_get_ai_postcode.return_value = self.ai_postcode_results

            await self.client.request('GET', self.get_start_en)
            self.assertLogEvent(cm, "received GET on endpoint 'en/start'")

            await self.client.request('POST',
                                      self.post_start_en,
                                      allow_redirects=True,
                                      data=self.start_data_valid)

            self.assertLogEvent(cm, "received POST on endpoint 'en/start'")
            self.assertLogEvent(cm, "received GET on endpoint 'en/start/unlinked/enter-address'")

            await self.client.request(
                    'POST',
                    self.post_start_unlinked_enter_address_en,
                    data=self.common_postcode_input_valid)

            self.assertLogEvent(cm, "received POST on endpoint 'en/start/unlinked/enter-address'")
            self.assertLogEvent(cm, "received GET on endpoint 'en/start/unlinked/select-address'")

            await self.client.request(
                    'POST',
                    self.post_start_unlinked_select_address_en,
                    data=self.common_select_address_input_valid)
            self.assertLogEvent(cm, "received POST on endpoint 'en/start/unlinked/select-address'")
            self.assertLogEvent(cm, "received GET on endpoint 'en/start/unlinked/confirm-address'")

            response = await self.client.request(
                    'POST',
                    self.post_start_unlinked_confirm_address_en,
                    data=self.common_confirm_address_input_invalid)
            self.assertLogEvent(cm, "received POST on endpoint 'en/start/unlinked/confirm-address'")

            self.assertEqual(200, response.status)
            resp_content = await response.content.read()
            self.assertIn(self.ons_logo_en, str(resp_content))
            self.assertIn(self.content_common_confirm_address_title_en, str(resp_content))
            self.assertIn(self.content_common_confirm_address_value_en, str(resp_content))

    @unittest_run_loop
    async def test_unlinked_confirm_address_invalid_cy(self):
        with self.assertLogs('respondent-home', 'INFO') as cm, mock.patch(
                'app.utils.AddressIndex.get_ai_postcode') as mocked_get_ai_postcode, aioresponses(
            passthrough=[str(self.server._root)]) \
                as mocked:

            mocked.get(self.rhsvc_url, payload=self.unlinked_uac_json_cy)
            mocked_get_ai_postcode.return_value = self.ai_postcode_results

            await self.client.request('GET', self.get_start_cy)
            self.assertLogEvent(cm, "received GET on endpoint 'cy/start'")

            await self.client.request('POST',
                                      self.post_start_cy,
                                      allow_redirects=True,
                                      data=self.start_data_valid)

            self.assertLogEvent(cm, "received POST on endpoint 'cy/start'")
            self.assertLogEvent(cm, "received GET on endpoint 'cy/start/unlinked/enter-address'")

            await self.client.request(
                    'POST',
                    self.post_start_unlinked_enter_address_cy,
                    data=self.common_postcode_input_valid)

            self.assertLogEvent(cm, "received POST on endpoint 'cy/start/unlinked/enter-address'")
            self.assertLogEvent(cm, "received GET on endpoint 'cy/start/unlinked/select-address'")

            await self.client.request(
                    'POST',
                    self.post_start_unlinked_select_address_cy,
                    data=self.common_select_address_input_valid)
            self.assertLogEvent(cm, "received POST on endpoint 'cy/start/unlinked/select-address'")
            self.assertLogEvent(cm, "received GET on endpoint 'cy/start/unlinked/confirm-address'")

            response = await self.client.request(
                    'POST',
                    self.post_start_unlinked_confirm_address_cy,
                    data=self.common_confirm_address_input_invalid)
            self.assertLogEvent(cm, "received POST on endpoint 'cy/start/unlinked/confirm-address'")

            self.assertEqual(200, response.status)
            resp_content = await response.content.read()
            self.assertIn(self.ons_logo_cy, str(resp_content))
            self.assertIn(self.content_common_confirm_address_title_cy, str(resp_content))
            self.assertIn(self.content_common_confirm_address_value_cy, str(resp_content))

    @unittest_run_loop
    async def test_unlinked_confirm_address_invalid_ni(self):
        with self.assertLogs('respondent-home', 'INFO') as cm, mock.patch(
                'app.utils.AddressIndex.get_ai_postcode') as mocked_get_ai_postcode, aioresponses(
            passthrough=[str(self.server._root)]) \
                as mocked:

            mocked.get(self.rhsvc_url, payload=self.unlinked_uac_json_ni)
            mocked_get_ai_postcode.return_value = self.ai_postcode_results

            await self.client.request('GET', self.get_start_ni)
            self.assertLogEvent(cm, "received GET on endpoint 'ni/start'")

            await self.client.request('POST',
                                      self.post_start_ni,
                                      allow_redirects=True,
                                      data=self.start_data_valid)

            self.assertLogEvent(cm, "received POST on endpoint 'ni/start'")
            self.assertLogEvent(cm, "received GET on endpoint 'ni/start/unlinked/enter-address'")

            await self.client.request(
                    'POST',
                    self.post_start_unlinked_enter_address_ni,
                    data=self.common_postcode_input_valid)

            self.assertLogEvent(cm, "received POST on endpoint 'ni/start/unlinked/enter-address'")
            self.assertLogEvent(cm, "received GET on endpoint 'ni/start/unlinked/select-address'")

            await self.client.request(
                    'POST',
                    self.post_start_unlinked_select_address_ni,
                    data=self.common_select_address_input_valid)
            self.assertLogEvent(cm, "received POST on endpoint 'ni/start/unlinked/select-address'")
            self.assertLogEvent(cm, "received GET on endpoint 'ni/start/unlinked/confirm-address'")

            response = await self.client.request(
                    'POST',
                    self.post_start_unlinked_confirm_address_ni,
                    data=self.common_confirm_address_input_invalid)
            self.assertLogEvent(cm, "received POST on endpoint 'ni/start/unlinked/confirm-address'")

            self.assertEqual(200, response.status)
            resp_content = await response.content.read()
            self.assertIn(self.nisra_logo, str(resp_content))
            self.assertIn(self.content_common_confirm_address_title_en, str(resp_content))
            self.assertIn(self.content_common_confirm_address_value_en, str(resp_content))
