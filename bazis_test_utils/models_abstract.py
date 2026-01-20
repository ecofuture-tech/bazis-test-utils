# Copyright 2026 EcoFuture Technology Services LLC and contributors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from django.db import models
from django.utils.translation import gettext_lazy as _


class ChildEntityBase(models.Model):
    child_name = models.CharField(max_length=255)
    child_description = models.TextField(blank=True, null=True)
    child_is_active = models.BooleanField(default=True)
    child_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    child_dt_approved = models.DateTimeField(blank=True, null=True)

    class Meta:
        abstract = True
        verbose_name = _('Child entity')
        verbose_name_plural = _('Child entities')

    def __str__(self):
        return self.child_name


class DependentEntityBase(models.Model):
    dependent_name = models.CharField(max_length=255)
    dependent_description = models.TextField(blank=True, null=True)
    dependent_is_active = models.BooleanField(default=True)
    dependent_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    dependent_dt_approved = models.DateTimeField(blank=True, null=True)

    class Meta:
        abstract = True
        verbose_name = _('Dependent entity')
        verbose_name_plural = _('Dependent entities')

    def __str__(self):
        return self.dependent_name


class ExtendedEntityBase(models.Model):
    extended_name = models.CharField(max_length=255)
    extended_description = models.TextField(blank=True, null=True)
    extended_is_active = models.BooleanField(default=True)
    extended_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    extended_dt_approved = models.DateTimeField(blank=True, null=True)

    class Meta:
        abstract = True
        verbose_name = _('Extended entity')
        verbose_name_plural = _('Extended entities')

    def __str__(self):
        return self.extended_name


class ParentEntityBase(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    dt_approved = models.DateTimeField(blank=True, null=True)

    class Meta:
        abstract = True
        verbose_name = _('Parent entity')
        verbose_name_plural = _('Parent entities')

    def __str__(self):
        return self.name
