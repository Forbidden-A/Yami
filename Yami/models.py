from tortoise import fields
from tortoise.models import Model


class StarredMessage(Model):
    id = fields.BigIntField(unique=True, pk=True)
    star_id = fields.BigIntField(unique=True)
    stars = fields.IntField()


class Guild(Model):
    id = fields.BigIntField(unique=True, pk=True)
    prefix = fields.TextField(default="y.")
    starboard = fields.BigIntField(null=True, default=None)
    stars = fields.IntField(default=3)
