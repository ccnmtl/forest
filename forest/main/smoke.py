from django.conf import settings
from smoketest import SmokeTest
from models import Stand


class DBConnectivity(SmokeTest):
    def test_retrieve(self):
        cnt = Stand.objects.all().count()
        self.assertTrue(cnt > 0)


class SeedStandExists(SmokeTest):
    def test_seed_stand(self):
        cnt = Stand.objects.get(hostname=settings.SEED_STAND)
        self.assertTrue(cnt > 0)
