from smoketest import SmokeTest
from models import Stand


class DBConnectivity(SmokeTest):
    def test_retrieve(self):
        cnt = Stand.objects.all().count()
        self.assertTrue(cnt > 0)
