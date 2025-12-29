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
from service.models import Product, Category, db, DataValidationError
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
        app.logger.info(f"Product: {product}")

        self.assertIsNotNone(product.id)
        fetched_product = Product.find(product.id)

        # check pointer
        product.name = "xxx"
        product.update()

        # check read == created
        self.assertEqual(fetched_product, product)

    def test_update_a_product(self):
        """It should Update a product from the database"""

        # create a product
        product = ProductFactory()
        app.logger.info(f"Product: {product}")

        product.id = None
        product.create()
        app.logger.info(f"Product: {product}")

        self.assertIsNotNone(product.id)
        original_id = product.id

        # update product description
        product.description = "xxx"
        product.update()
        self.assertEqual(product.id, original_id)
        self.assertEqual(product.description, "xxx")

        # ensures only one product in db and is THE product with same ID but new description
        all_products = Product.all()
        self.assertEqual(len(all_products), 1)
        self.assertEqual(all_products[0].id, original_id)
        self.assertEqual(all_products[0].description, "xxx")

    def test_update_product_with_no_id(self):
        """It should not Update a Product with no id"""
        product = ProductFactory()
        product.id = None  # No ID set
        self.assertRaises(DataValidationError, product.update)

    def test_delete_a_product(self):
        """It should Delete a product from the database"""

        # create a product
        product = ProductFactory()
        product.id = None
        product.create()
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

    def test_find_a_product_by_price(self):
        """It should return all products from DB with the given price"""

        product_list = ProductFactory.create_batch(10)
        for each in product_list:
            each.create()

        price = product_list[0].price
        price_count = len([i for i in product_list if i.price == price])

        price_versions = [Decimal(price), str(price)]

        for each_price in price_versions:
            found_products = Product.find_by_price(each_price)
            self.assertEqual(found_products.count(), price_count)
            for each in found_products:
                self.assertEqual(each.price, Decimal(price))

    def test_deserialize(self):
        """It should Deserialize a Product dict into a Product object"""

        product = ProductFactory()
        product_data = product.serialize()
        self.assertIsInstance(product_data, dict)

        # Create a new Product instance to deserialize into
        new_product = Product()
        new_product.deserialize(product_data)

        # check new product is of Product object type
        self.assertIsInstance(new_product, Product)

        # check deserialize assigned the correct data to the new product object
        self.assertEqual(new_product.name, product.name)
        self.assertEqual(new_product.description, product.description)
        self.assertEqual(new_product.price, product.price)
        self.assertEqual(new_product.available, product.available)
        self.assertEqual(new_product.category, product.category)

    def test_deserialize_with_non_bool_available_type(self):
        """It should not Deserialize and should raise DataValidationError when the 'available' value is not bool"""

        invalid_available_value = ["true", 1, 1.0]

        for invalid_value in invalid_available_value:

            product_data = ProductFactory().serialize()
            self.assertIsInstance(product_data, dict)

            # Create a new Product instance to deserialize into
            new_product = Product()

            # test 'available' attribute not being bool, expect DataValidationError
            product_data['available'] = invalid_value
            with self.assertRaises(DataValidationError) as context:
                new_product.deserialize(product_data)

            self.assertIn("Invalid type for boolean [available]: ", str(context.exception))

    def test_deserialize_with_invalid_category_attribute(self):
        """It should not Deserialize and should raise DataValidationError when the dict category is not a Category object"""

        invalid_categories = ['INVALID', 'ELECTRONICS', 'BOOKS', 'xxx', '']

        for category in invalid_categories:
            product_data = ProductFactory().serialize()
            self.assertIsInstance(product_data, dict)

            # Create a new Product instance to deserialize into
            new_product = Product()

            # test data dict with invalid Category value; expect DataValidationError
            product_data['category'] = category  # Triggers AttributeError which raises DataValidationError
            with self.assertRaises(DataValidationError) as context:
                new_product.deserialize(product_data)

                # Verify it mentions "Invalid attribute"
                self.assertIn("Invalid attribute", str(context.exception))

    def test_deserialize_with_null_data(self):
        """It should not Deserialize and should raise DataValidationError when 'price' is not decimal"""

        # Create a new Product instance to deserialize into
        new_product = Product()

        # test with None data; expect DataValidationError
        with self.assertRaises(DataValidationError) as context:
            new_product.deserialize(None)

        self.assertIn("Invalid product: body of request contained bad or no data ", str(context.exception))

    def test_deserialize_missing_dict_keys(self):
        """It should not Deserialize and should raise DataValidationError when any required dict key is missing"""

        required_fields = ['name', 'description', 'price', 'available', 'category']

        product_data = ProductFactory().serialize()

        for field in required_fields:
            test_data = product_data.copy()
            del test_data[field]

            product = Product()
            with self.assertRaises(DataValidationError) as context:
                product.deserialize(test_data)

            # Verify it mentions "missing"
            self.assertIn("Invalid product: missing ", str(context.exception))

