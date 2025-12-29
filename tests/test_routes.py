######################################################################
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
######################################################################
"""
Product API Service Test Suite

Test cases can be run with the following:
  nosetests -v --with-spec --spec-color
  coverage report -m
  codecov --token=$CODECOV_TOKEN

  While debugging just these tests it's convenient to use this:
    nosetests --stop tests/test_service.py:TestProductService
"""
import os
import logging
from decimal import Decimal
from unittest import TestCase
from urllib.parse import quote_plus

from service import app
from service.common import status
from service.models import db, init_db, Product
from tests.factories import ProductFactory

# Disable all but critical errors during normal test run
# uncomment for debugging failing tests
# logging.disable(logging.CRITICAL)

# DATABASE_URI = os.getenv('DATABASE_URI', 'sqlite:///../db/test.db')
DATABASE_URI = os.getenv(
    "DATABASE_URI", "postgresql://postgres:postgres@localhost:5432/postgres"
)
BASE_URL = "/products"


######################################################################
#  T E S T   C A S E S
######################################################################
# pylint: disable=too-many-public-methods
class TestProductRoutes(TestCase):
    """Product Service tests"""

    @classmethod
    def setUpClass(cls):
        """Run once before all tests"""
        app.config["TESTING"] = True
        app.config["DEBUG"] = False
        # Set up the test database
        app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URI
        app.logger.setLevel(logging.CRITICAL)
        init_db(app)

    @classmethod
    def tearDownClass(cls):
        """Run once after all tests"""
        db.session.close()

    def setUp(self):
        """Runs before each test"""
        self.client = app.test_client()
        db.session.query(Product).delete()  # clean up the last tests
        db.session.commit()

    def tearDown(self):
        db.session.remove()

    ############################################################
    # Utility function to bulk create products
    ############################################################
    def _create_products(self, count: int = 1) -> list:
        """Factory method to create products in bulk"""
        products = []
        for _ in range(count):
            test_product = ProductFactory()
            response = self.client.post(BASE_URL, json=test_product.serialize())
            self.assertEqual(
                response.status_code, status.HTTP_201_CREATED, "Could not create test product"
            )
            new_product = response.get_json()
            test_product.id = new_product["id"]
            products.append(test_product)
        return products

    ############################################################
    #  T E S T   C A S E S
    ############################################################
    def test_index(self):
        """It should return the index page"""
        response = self.client.get("/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn(b"Product Catalog Administration", response.data)

    def test_health(self):
        """It should be healthy"""
        response = self.client.get("/health")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.get_json()
        self.assertEqual(data['message'], 'OK')

    # ----------------------------------------------------------
    # TEST CREATE
    # ----------------------------------------------------------
    def test_create_product(self):
        """It should Create a new Product"""
        test_product = ProductFactory()
        logging.debug("Test Product: %s", test_product.serialize())
        response = self.client.post(BASE_URL, json=test_product.serialize())
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Make sure location header is set
        location = response.headers.get("Location", None)
        self.assertIsNotNone(location)

        # Check the data is correct
        new_product = response.get_json()
        self.assertEqual(new_product["name"], test_product.name)
        self.assertEqual(new_product["description"], test_product.description)
        self.assertEqual(Decimal(new_product["price"]), test_product.price)
        self.assertEqual(new_product["available"], test_product.available)
        self.assertEqual(new_product["category"], test_product.category.name)

        #
        # Uncomment this code once READ is implemented
        #

        # Check that the location header was correct
        response = self.client.get(location)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        new_product = response.get_json()
        self.assertEqual(new_product["name"], test_product.name)
        self.assertEqual(new_product["description"], test_product.description)
        self.assertEqual(Decimal(new_product["price"]), test_product.price)
        self.assertEqual(new_product["available"], test_product.available)
        self.assertEqual(new_product["category"], test_product.category.name)

    def test_create_product_with_no_name(self):
        """It should not Create a Product without a name"""
        product = self._create_products()[0]
        new_product = product.serialize()
        del new_product["name"]
        logging.debug("Product no name: %s", new_product)
        response = self.client.post(BASE_URL, json=new_product)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_product_no_content_type(self):
        """It should not Create a Product with no Content-Type"""
        response = self.client.post(BASE_URL, data="bad data")
        self.assertEqual(response.status_code, status.HTTP_415_UNSUPPORTED_MEDIA_TYPE)

    def test_create_product_wrong_content_type(self):
        """It should not Create a Product with wrong Content-Type"""
        response = self.client.post(BASE_URL, data={}, content_type="plain/text")
        self.assertEqual(response.status_code, status.HTTP_415_UNSUPPORTED_MEDIA_TYPE)

    #
    # ADD YOUR TEST CASES HERE
    #

    def test_get_product(self):
        """It should return a Product from DB given its ID"""

        # make test product, add to db
        test_product = self._create_products(1)[0]

        # get the test product from db by id
        response = self.client.get(f"{BASE_URL}/{test_product.id}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response_data = response.get_json()
        # make sure it's one product (a dict, not a list of dicts):
        self.assertIsInstance(response_data, dict)
        self.assertNotIsInstance(response_data, list)

        self.assertEqual(response_data, test_product.serialize())

    def test_update_a_product(self):
        """It should update an existing Product in DB with the given data"""

        # create a product
        test_product = ProductFactory()
        test_product_data = test_product.serialize()
        post_response = self.client.post(BASE_URL, json=test_product_data)
        self.assertEqual(post_response.status_code, status.HTTP_201_CREATED)

        # update the product with the real id
        new_product_data = post_response.get_json()
        actual_id = new_product_data["id"]
        new_product_data["name"] = "xxx"
        new_product_data["description"] = "unknown"
        new_product_data["price"] = "9999999"

        put_response = self.client.put(f"{BASE_URL}/{new_product_data['id']}", json=new_product_data)

        # check it's the same product but with the changes made successfully
        self.assertEqual(put_response.status_code, status.HTTP_200_OK)
        updated_product_data = put_response.get_json()

        self.assertEqual(updated_product_data["id"], actual_id)
        self.assertEqual(updated_product_data["name"], "xxx")
        self.assertEqual(updated_product_data["description"], "unknown")
        self.assertEqual(updated_product_data["price"], "9999999")

        self.assertEqual(updated_product_data, new_product_data)
        self.assertNotEqual(updated_product_data, test_product_data)

    def test_delete_a_product(self):
        """It should delete products in DB given their ids"""

        # add 5 new products to DB, get initial DB product count
        product_list = self._create_products(5)
        initial_product_count = self.get_product_count()

        # delete one product from DB, check for successful deletion and None response data
        test_product = product_list[0]
        test_id = test_product.id
        delete_response = self.client.delete(f"{BASE_URL}/{test_id}")
        self.assertEqual(delete_response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(len(delete_response.data), 0)

        # try to retrieve the deleted product
        get_response = self.client.get(f"{BASE_URL}/{test_id}")
        self.assertEqual(get_response.status_code, status.HTTP_404_NOT_FOUND)

        # check post-deletion product count in DB
        self.assertEqual(self.get_product_count(), initial_product_count - 1)

    def test_list_all_products(self):
        """It should return all products in DB"""

        product_list = self._create_products(5)
        get_response = self.client.get(BASE_URL)
        self.assertEqual(get_response.status_code, status.HTTP_200_OK)
        response_data = get_response.get_json()
        self.assertEqual(len(response_data), len(product_list))

    def test_list_by_name(self):
        """It should return all products in DB with the given name"""

        product_list = self._create_products(5)
        test_product = product_list[0]
        test_name = test_product.name
        test_name_count = len([i for i in product_list if i.name == test_name])

        get_response = self.client.get(BASE_URL, query_string=f"name={quote_plus(test_name)}")
        self.assertEqual(get_response.status_code, status.HTTP_200_OK)

        response_data = get_response.get_json()
        self.assertEqual(len(response_data), test_name_count)

        for each_product in response_data:
            self.assertEqual(each_product["name"], test_name)

    def test_list_by_category(self):
        """It should return all products in DB with the given category"""

        product_list = self._create_products(10)
        test_category = product_list[0].category

        found_list = [i for i in product_list if i.category == test_category]
        found_count = len(found_list)
        app.logger.info(f"{found_count} products found in category {test_category}")

        get_response = self.client.get(BASE_URL, query_string=f"category={test_category.name}")
        self.assertEqual(get_response.status_code, status.HTTP_200_OK)
        response_data = get_response.get_json()
        self.assertEqual(len(response_data), found_count)

        for each_product in response_data:
            self.assertEqual(each_product["category"], test_category.name)

    def test_list_by_availability(self):
        """It should return all products in DB with the given availability"""

        product_list = self._create_products(10)
        available_products = [i for i in product_list if i.available is True]
        available_count = len(available_products)
        app.logger.info(f"{available_count} products available in DB: {available_products}")

        get_response = self.client.get(BASE_URL, query_string="available=true")
        self.assertEqual(get_response.status_code, status.HTTP_200_OK)
        response_data = get_response.get_json()
        self.assertEqual(len(response_data), available_count)

        for each_product in response_data:
            self.assertEqual(each_product["available"], True)

    ######################################################################
    # Utility functions
    ######################################################################

    def get_product_count(self):
        """save the current number of products"""
        response = self.client.get(BASE_URL)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.get_json()
        # logging.debug("data = %s", data)
        return len(data)
