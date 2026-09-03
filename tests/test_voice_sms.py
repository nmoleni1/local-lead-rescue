import unittest
import json
import io
import os
import sys

# Ensure project root is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from api.index import handle_api_request, app

class TestVoiceSMS(unittest.TestCase):
    def test_voice_inbound(self):
        status, res = handle_api_request("POST", "/api/voice/inbound", "{}")
        self.assertEqual(status, 200)
        self.assertEqual(res.get("response_type"), "twiml")
        self.assertIn("<Gather", res.get("twiml", ""))

    def test_voice_gather_emergency(self):
        payload = json.dumps({
            "SpeechResult": "My basement is flooding with a water leak emergency at 3500 S",
            "From": "+18015551234",
            "CallSid": "CA12345"
        })
        status, res = handle_api_request("POST", "/api/voice/gather", payload)
        self.assertEqual(status, 200)
        self.assertEqual(res.get("response_type"), "twiml")
        self.assertIn("emergency", res.get("twiml", "").lower())

    def test_sms_inbound(self):
        payload = json.dumps({
            "From": "+18015559876",
            "To": "+18015550000",
            "Body": "My AC is blowing warm air, need someone out tomorrow"
        })
        status, res = handle_api_request("POST", "/api/sms/inbound", payload)
        self.assertEqual(status, 200)
        self.assertTrue(res.get("success"))

    def test_wsgi_twiml_content_type(self):
        environ = {
            'PATH_INFO': '/api/voice/inbound',
            'REQUEST_METHOD': 'POST',
            'CONTENT_LENGTH': 2,
            'CONTENT_TYPE': 'application/json',
            'wsgi.input': io.BytesIO(b'{}')
        }
        headers_captured = []
        def start_response(status, headers):
            headers_captured.extend(headers)

        body = app(environ, start_response)
        content_type = next((v for k, v in headers_captured if k == 'Content-Type'), '')
        self.assertIn('text/xml', content_type)
        self.assertIn(b'<Response>', body[0])

if __name__ == '__main__':
    unittest.main()
