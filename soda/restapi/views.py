
# Standard

# Third Party
from rest_framework import viewsets

# Local
import soda.models as sm
import soda.restapi.serializers as ts
import soda.restapi.permissions as tp
from xis.utils import user_is_kiosk


# ---------------------------------------------------------------------------
# VEND LOGS
# ---------------------------------------------------------------------------

class VendLogViewSet(viewsets.ModelViewSet):
    queryset = sm.VendLog.objects.all().order_by('id')
    serializer_class = ts.VendLogSerializer
    permission_classes = [tp.VendLogPermission]

    def get_queryset(self):

        if user_is_kiosk(self.request):
            return sm.VendLog.objects.all().order_by('id')
        else:
            return sm.VendLog.objects.all().order_by('id')
