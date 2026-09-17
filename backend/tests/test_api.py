import unittest
from fastapi.testclient import TestClient

class PortalTests(unittest.TestCase):
    def setUp(self):
        from app.main import app
        self.client = TestClient(app)

    def test_health(self):
        self.assertEqual(self.client.get('/health').json(), {'status': 'ok'})

    def test_search_normalized(self):
        for query in ['CAMINHAO', 'caminhão', '12345', 'REF-12345', '7890000012345']:
            with self.subTest(query=query):
                response = self.client.get('/api/search', params={'q':query})
                self.assertEqual(response.status_code, 200)
                self.assertIn('12345', [p['code'] for p in response.json()['results']])

    def test_missing_product(self):
        self.assertEqual(self.client.get('/api/products/invalid').status_code, 404)

    def test_catalog(self):
        self.assertGreater(len(self.client.get('/api/latest').json()), 0)
        self.assertIn('Veículos', self.client.get('/api/categories').json())
        self.assertEqual(self.client.get('/api/products/12345').json()['code'], '12345')
        self.assertIn('images', self.client.get('/api/products/12345/media').json())

    def test_no_results(self):
        self.assertEqual(self.client.get('/api/search?q=inexistentezzzz').json()['results'], [])

if __name__ == '__main__':
    unittest.main()
