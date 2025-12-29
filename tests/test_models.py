# Copyright 2016, 2023 John J. Rofrano. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Test cases for Product Model

Test cases can be run with:
    nosetests
    coverage report -m

While debugging just these tests it's convenient to use this:
    nosetests --stop tests/test_models.py:TestProductModel

"""
import os
import logging
import unittest
from decimal import Decimal
from service.models import Product, Category, db
from service import app
from tests.factories import ProductFactory

DATABASE_URI = os.getenv(
    "DATABASE_URI", "postgresql://postgres:postgres@localhost:5432/postgres"
)


######################################################################
#  P R O D U C T   M O D E L   T E S T   C A S E S
######################################################################
# pylint: disable=too-many-public-methods
class TestProductModel(unittest.TestCase):
    """Test Cases for Product Model"""

    @classmethod
    def setUpClass(cls):
        """This runs once before the entire test suite"""
        app.config["TESTING"] = True
        app.config["DEBUG"] = False
        app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URI
        app.logger.setLevel(logging.CRITICAL)
        Product.init_db(app)

    @classmethod
    def tearDownClass(cls):
        """This runs once after the entire test suite"""
        db.session.close()

    def setUp(self):
        """This runs before each test"""
        db.session.query(Product).delete()  # clean up the last tests
        db.session.commit()

    def tearDown(self):
        """This runs after each test"""
        db.session.remove()

    ######################################################################
    #  T E S T   C A S E S
    ######################################################################

    def test_create_a_product(self):
        """It should Create a product and assert that it exists"""
        product = Product(name="Fedora", description="A red hat", price=12.50, available=True, category=Category.CLOTHS)
        self.assertEqual(str(product), "<Product Fedora id=[None]>")
        self.assertTrue(product is not None)
        self.assertEqual(product.id, None)
        self.assertEqual(product.name, "Fedora")
        self.assertEqual(product.description, "A red hat")
        self.assertEqual(product.available, True)
        self.assertEqual(product.price, 12.50)
        self.assertEqual(product.category, Category.CLOTHS)

    def test_add_a_product(self):
        """It should Create a product and add it to the database"""
        products = Product.all()
        self.assertEqual(products, [])
        product = ProductFactory()
        product.id = None
        product.create()
        # Assert that it was assigned an id and shows up in the database
        self.assertIsNotNone(product.id)
        products = Product.all()
        self.assertEqual(len(products), 1)
        # Check that it matches the original product
        new_product = products[0]
        self.assertEqual(new_product.name, product.name)
        self.assertEqual(new_product.description, product.description)
        self.assertEqual(Decimal(new_product.price), product.price)
        self.assertEqual(new_product.available, product.available)
        self.assertEqual(new_product.category, product.category)

    #
    # ADD YOUR TEST CASES HERE
    #

    def test_read_a_product(self):
        """It should Read a product from the database"""

        # Create product
        product = ProductFactory()
        product.id = None
        product.create()
        print(f"\n------1(1)--------{product}\n")
        app.logger.info(f"Product: {product}")

        self.assertIsNotNone(product.id)
        fetched_product = Product.find(product.id)

        # check pointer
        product.name = "xxx"
        product.update()
        print(f"\n------1(2)--------{product}, {fetched_product}\n")

        # check read == created
        self.assertEqual(fetched_product, product)

    def test_update_a_product(self):
        """It should Update a product from the database"""

        # create a product
        product = ProductFactory()
        print(f"\n-------2(1)-------{product}, {product.description}\n")
        app.logger.info(f"Product: {product}")

        product.id = None
        product.create()
        print(f"\n-------2(2)-------{product}, {product.description}\n")
        app.logger.info(f"Product: {product}")

        self.assertIsNotNone(product.id)
        original_id = product.id

        # update product description
        product.description = "xxx"
        product.update()
        print(f"\n-------2(3)-------{product}, {product.description}\n")
        self.assertEqual(product.id, original_id)
        self.assertEqual(product.description, "xxx")

        # ensures only one product in db and is THE product with same ID but new description
        all_products = Product.all()
        self.assertEqual(len(all_products), 1)
        self.assertEqual(all_products[0].id, original_id)
        self.assertEqual(all_products[0].description, "xxx")

    def test_delete_a_product(self):
        """It should Delete a product from the database"""

        # create a product
        product = ProductFactory()
        product.id = None
        product.create()
        print(f"\n-------3(1)-------{product}, {product.description}\n")
        app.logger.info(f"Product: {product}")

        # ensures only one product in db
        all_products = Product.all()
        self.assertEqual(len(all_products), 1)

        # remove the product from db
        product.delete()

        # assert successful product deletion
        all_products = Product.all()
        self.assertEqual(len(all_products), 0)

    def test_list_all_products(self):
        """It should List all products in DB"""

        all_products = Product.all()
        self.assertEqual(len(all_products), 0)

        for _ in range(5):
            product = ProductFactory()
            product.create()

        all_products = Product.all()
        self.assertEqual(len(all_products), 5)

    def find_a_product_by_name(self):
        """It should return products from DB with the given name"""

        product_list = ProductFactory.create_batch(5)
        for product in product_list:
            product.create()

        self.assertEqual(len(product_list), 5)

        first_name = product_list[0].name
        first_name_count = len([i for i in product_list if i.name == first_name])

        found_products = Product.find_by_name(first_name)
        self.assertEqual(found_products.count(), first_name_count)

        for each in found_products:
            self.assertEqual(each.name, first_name)

    def test_find_a_product_by_availability(self):
        """It should return products from DB with the given availability"""

        product_list = ProductFactory.create_batch(10)
        for each in product_list:
            each.create()

        availability = product_list[0].available
        availability_count = len([i for i in product_list if i.available == availability])

        found_products = Product.find_by_availability(availability)
        self.assertEqual(found_products.count(), availability_count)
        for each in found_products:
            self.assertEqual(each.available, availability)

    def test_find_a_product_by_category(self):
        """It should return all products from DB with the given category"""
        product_list = ProductFactory.create_batch(10)
        for each in product_list:
            each.create()

        category = product_list[0].category
        category_count = len([i for i in product_list if i.category == category])

        found_products = Product.find_by_category(category)
        self.assertEqual(found_products.count(), category_count)
        for each in found_products:
            self.assertEqual(each.category, category)
