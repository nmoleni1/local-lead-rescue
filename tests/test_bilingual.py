import unittest
import json
import os
import sys

# Ensure project root is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from api.index import detect_language, generate_ai_sms_draft, handle_api_request

class TestBilingualEngine(unittest.TestCase):
    def test_detect_language(self):
        self.assertEqual(detect_language("Hola necesito un plomero urgente para una fuga"), "es")
        self.assertEqual(detect_language("Buenos dias, cuanto cuesta reparar un calentador?"), "es")
        self.assertEqual(detect_language("Tengo una emergencia en mi bano"), "es")
        self.assertEqual(detect_language("Emergency water leak in basement"), "en")
        self.assertEqual(detect_language("Can you give me a free estimate for AC repair?"), "en")

    def test_spanish_sms_generation(self):
        spanish_draft = generate_ai_sms_draft("Carlos Garcia", "Plomería", "Tengo una fuga de agua en el baño")
        self.assertIn("Carlos", spanish_draft)
        self.assertIn("comunicarse", spanish_draft)
        self.assertIn("licenciados", spanish_draft)

        english_draft = generate_ai_sms_draft("John Doe", "Plumbing", "Water leak in basement")
        self.assertIn("Hi John!", english_draft)
        self.assertIn("licensed technicians", english_draft)

    def test_bilingual_voice_gather_spanish(self):
        payload = json.dumps({
            "From": "+18015554321",
            "To": "+18015550100",
            "SpeechResult": "Hola buenas tardes, tengo una emergencia con una fuga de agua en West Valley",
            "CallSid": "SIM_ES_001"
        })
        status, res = handle_api_request("POST", "/api/voice/gather", payload)
        self.assertEqual(status, 200)
        self.assertEqual(res.get("response_type"), "twiml")
        self.assertEqual(res.get("language"), "es")
        self.assertIn("Polly.Lupe", res.get("twiml"))
        self.assertIn('language="es-US"', res.get("twiml"))

    def test_bilingual_sms_inbound_spanish(self):
        payload = json.dumps({
            "From": "+18015557788",
            "To": "+18015550100",
            "Body": "Hola, necesito ayuda urgente con el aire acondicionado no enfria"
        })
        status, res = handle_api_request("POST", "/api/sms/inbound", payload)
        self.assertEqual(status, 200)
        self.assertTrue(res.get("success"))
        self.assertEqual(res.get("language"), "es")

if __name__ == "__main__":
    unittest.main()
