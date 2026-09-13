from django.test import TestCase


class PwaEndpointTests(TestCase):
    def test_manifest_is_served_as_json(self):
        response = self.client.get("/manifest.webmanifest")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/manifest+json")
        self.assertContains(response, '"short_name": "KTM LPG"')

    def test_service_worker_is_root_scoped_javascript(self):
        response = self.client.get("/service-worker.js")

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response["Content-Type"].startswith("application/javascript"))
        self.assertContains(response, 'const CACHE_NAME = "kathmandu-lpg-shell-v6"')
        self.assertContains(response, 'const OFFLINE_URL = "/offline/"')

    def test_offline_fallback_is_public(self):
        response = self.client.get("/offline/")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "You’re offline for now.")
