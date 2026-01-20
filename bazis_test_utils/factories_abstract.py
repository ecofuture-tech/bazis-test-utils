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

import random

from django.utils import timezone

import factory

from .models_abstract import ChildEntityBase


class ChildEntityFactoryAbstract(factory.django.DjangoModelFactory):
    child_name = factory.Faker('name')
    child_description = factory.Faker('text')
    child_is_active = factory.Faker('pybool')
    child_price = factory.Faker(
        'pydecimal', left_digits=5, right_digits=2, min_value=10, max_value=1000, positive=True
    )
    child_dt_approved = factory.Faker(
        'date_time_this_year',
        tzinfo=timezone.get_current_timezone(),
        before_now=False,
        after_now=True,
    )


class DependentEntityFactoryAbstract(factory.django.DjangoModelFactory):
    dependent_name = factory.Faker('name')
    dependent_description = factory.Faker('text')
    dependent_is_active = factory.Faker('pybool')
    dependent_price = factory.Faker(
        'pydecimal',
        left_digits=5,
        right_digits=2,
        min_value=10,
        max_value=1000,
        positive=True,
    )
    dependent_dt_approved = factory.Faker(
        'date_time_this_year',
        tzinfo=timezone.get_current_timezone(),
        before_now=False,
        after_now=True,
    )


class ExtendedEntityFactoryAbstract(factory.django.DjangoModelFactory):
    extended_name = factory.Faker('name')
    extended_description = factory.Faker('text')
    extended_is_active = factory.Faker('pybool')
    extended_price = factory.Faker(
        'pydecimal',
        left_digits=5,
        right_digits=2,
        min_value=10,
        max_value=1000,
        positive=True,
    )
    extended_dt_approved = factory.Faker(
        'date_time_this_year',
        tzinfo=timezone.get_current_timezone(),
        before_now=False,
        after_now=True,
    )


class ParentEntityFactoryAbstract(factory.django.DjangoModelFactory):
    name = factory.Faker('name')
    description = factory.Faker('text')
    is_active = factory.Faker('pybool')
    price = factory.Faker(
        'pydecimal', left_digits=5, right_digits=2, min_value=10, max_value=1000, positive=True
    )
    dt_approved = factory.Faker(
        'date_time_this_year',
        tzinfo=timezone.get_current_timezone(),
        before_now=False,
        after_now=True,
    )
    dependent_entities = factory.RelatedFactory(
        'tests.factories.DependentEntityFactory',
        factory_related_name='parent_entity',
    )
    extended_entity = factory.RelatedFactory(
        'tests.factories.ExtendedEntityFactory',
        factory_related_name='parent_entity',
    )

    @factory.post_generation
    def child_entities(self, create, extracted, **kwargs):
        if not create or not extracted:
            return

        if isinstance(extracted, ChildEntityBase):
            self.child_entities.add(extracted)
        elif isinstance(extracted, list):
            self.child_entities.add(*extracted)
        else:
            child_entities_model = self.child_entities.model
            child_entity_subclasses = ChildEntityFactoryAbstract.__subclasses__()

            factories = [
                x
                for x in child_entity_subclasses
                if not x._meta.abstract and x._meta.model == child_entities_model
            ]

            if factories:
                self.child_entities.add(*factories[0].create_batch(random.randint(1, 10)))

    class Meta:
        skip_postgeneration_save = True
