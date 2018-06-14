
# Standard
from typing import Optional
import logging

# Third-party
from django.db import models
from django.conf import settings
from django.contrib.auth.models import User
import paho.mqtt.client as mqtt

# Local


MQTT_SERVER = settings.BZWOPS_SODA_CONFIG.get('MQTT_SERVER', None)
MQTT_PORT = settings.BZWOPS_SODA_CONFIG.get('MQTT_PORT', None)
MQTT_USER = settings.BZWOPS_SODA_CONFIG.get('MQTT_USER', None)
MQTT_PW = settings.BZWOPS_SODA_CONFIG.get('MQTT_PW', None)
MQTT_TOPIC = settings.BZWOPS_SODA_CONFIG.get('MQTT_TOPIC', None)


_logger = logging.getLogger("soda")


class Product(models.Model):

    name = models.CharField(max_length=40, unique=True,
        help_text="The name of the product, for example 'Diet Coke'")

    def vend(self):
        bin = VendingMachineBin.for_product(self)
        if bin is not None:
            if settings.ISDEVHOST:
                _logger.info("Would have vended from bin {}.".format(bin))
            else:
                bin.vend()
        else:
            _logger.warning("No bin specified for {}.".format(self.name))

    def __str__(self):
        return self.name


class SkuToProductMapping(models.Model):

    sku_or_desc = models.CharField(max_length=40, unique=True,
        help_text="The SKU (or description) the payment processor will report.")

    product = models.ForeignKey(Product,
        on_delete=models.CASCADE,
        help_text="The product that the SKU (or description) identifies.")

    @classmethod
    def mapSkuToProduct(cls, sku: str):
        pass


class VendingMachineBin(models.Model):

    number = models.IntegerField(unique=True,
        help_text="The bin number, 1 or greater.")

    contents = models.ForeignKey(Product, null=True,
        on_delete=models.SET_NULL,
        help_text="The product currently stocked in this bin.")

    @classmethod
    def for_sku(cls, sku: str) -> Optional['VendingMachineBin']:
        raise NotImplementedError

    @classmethod
    def for_product(cls, product: Product) -> Optional['VendingMachineBin']:
        try:
            return VendingMachineBin.objects.get(contents=product)
        except VendingMachineBin.DoesNotExist:
            return None

    def vend(self):
        client = mqtt.Client()
        client.username_pw_set(MQTT_USER, MQTT_PW)
        client.connect(MQTT_SERVER, int(MQTT_PORT))
        client.publish(MQTT_TOPIC, self.number)

    def __str__(self):
        return "Bin #{} ({})".format(self.number, self.contents.name)

    class Meta:
        ordering = ['number']


class VendLog(models.Model):

    when = models.DateTimeField(auto_now_add=True,
        help_text="Date and time that the product was vended.")

    who_for = models.ForeignKey(User, null=False,
        on_delete=models.PROTECT,
        help_text="Who was this product vended for?")

    product = models.ForeignKey(Product, null=False,
        on_delete=models.PROTECT,
        help_text="The product that was vended.")
