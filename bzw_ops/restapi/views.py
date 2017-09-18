
# Standard
from datetime import datetime

# Third Party
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticatedOrReadOnly

# Local
import bzw_ops.models as models
import bzw_ops.restapi.serializers as serializers


# ---------------------------------------------------------------------------
# TIME BLOCKS
# ---------------------------------------------------------------------------

class TimeBlockViewSet(viewsets.ModelViewSet):
    queryset = models.TimeBlock.objects.all()
    serializer_class = serializers.TimeBlockSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]


class TimeBlockTypeViewSet(viewsets.ModelViewSet):
    queryset = models.TimeBlockType.objects.all()
    serializer_class = serializers.TimeBlockTypeSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
