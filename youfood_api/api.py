import psycopg2
from psycopg2 import IntegrityError, ProgrammingError
from flask import Flask, jsonify, request, Response
from flask.views import MethodView
from psycopg2._psycopg import DataError
from datetime import datetime

app = Flask(__name__)

conn = psycopg2.connect(dbname="youfood", user="youfood", password="wizard11", host="localhost")

def home():
    return "<h1 style='color:blue'>Hello There!</h1>"

def flatten(iterable):
    it = iter(iterable)
    for e in it:
        if isinstance(e, (list, tuple)):
            for f in flatten(e):
                yield f
        else:
            yield e

def verify_login():
    """
    POST: /verify_login
    Request Body:
    {
        is_owner: <true/false>,
        email: <email>,
        password: <password
    }

    Returns 400 if a request param was missing, 401 if the login was invalid, or 204 if it was valid
    """
    json_data = request.get_json()
    is_owner = json_data.get("is_owner")
    email = json_data.get("email")
    password = json_data.get("password")

    if is_owner == None or email == None or password == None:
        return "Missing necessary parameter in request body", 400

    if is_owner == True:
        with conn as c:
            with c.cursor() as cur:
                cur.execute("""
                    SELECT * 
                    FROM "Owner" 
                    WHERE email = %s AND hashedpass = %s""", (email, password))

                row = cur.fetchone()
                if row == None:
                    return "Invalid Login", 401
                else:
                    return Response(status=204)
    else:
        with conn as c:
            with c.cursor() as cur:
                cur.execute("""
                    SELECT * 
                    FROM "User" 
                    WHERE email = %s AND hashedpass = %s""", (email, password))

                row = cur.fetchone()
                if row == None:
                    return "Invalid Login", 401
                else:
                    return Response(status=204)



class UserAPI(MethodView):

    def get(self):
        """
        GET: /users?email=<emali>
        Gets user info for a given specified email address that is a URL query parameter
        """
        
        email = request.args.get("email")
        if email == None:
            return jsonify({'error': 'No email address specified'}), 400

        cur = conn.cursor()
        with conn as c:
            with c.cursor() as cur:
                cur.execute("SELECT * FROM \"User\" WHERE email=%s;", (email,))
                row = cur.fetchone()
                # Executes if no user with that email address was found
                if row == None:
                    return jsonify({'error': 'No user with that email exists'}), 400

                data = {
                    'email' : row[0],
                    'name' : row[1]
                }

                return jsonify(data), 200

    def post(self):
        """
        POST: /users

        JSON request payload:
        {
            "email" : <email>
            "name" : <name>
            "password" : <password>
        }
        """
        json_data = request.get_json()
        email = json_data.get("email")
        name = json_data.get("name")
        password = json_data.get("password")
        
        if email == None or name == None or password == None:
            return Response(status=400)

        with conn as c:
            with c.cursor() as cur:
                cur.execute("INSERT INTO \"User\" (email, name, hashedpass) VALUES (%s, %s, %s);", (email, name, password))
                return Response(status=201)

    def put(self):
        """
        PUT: /users

        JSON request payload (email is required, at least 1 of name or password is also required)
        {
            "email" : <email>
            "name" : <name>
            "password" : <password>
        }
        """
        json_data = request.get_json()
        email = json_data.get("email")
        name = json_data.get("name")
        password = json_data.get("password")
        
        if email == None or (name == None and password == None):
            return jsonify({'error': 'Missing email or both name and password'}), 400

        with conn as c:
            with c.cursor() as cur:
                if(name != None):
                    cur.execute("UPDATE \"User\" SET name = %s WHERE email = %s;", (name, email))
                    if cur.rowcount == 0:
                        return jsonify({'error': 'No user with that email exists'}), 400

                if(password != None):
                    cur.execute("UPDATE \"User\" SET hashedpass = %s WHERE email = %s;", (password, email))
                    if cur.rowcount == 0:
                        return jsonify({'error': 'No user with that email exists'}), 400

                return Response(status=204)

    def delete(self):
        """
        DELETE: /users?email=<email>
        Deletes a user with a given email address. It is only 1 user because email is a primary key, so the email
        entered can correspond to at most 1 user
        """
        
        email = request.args.get("email")
        if email == None:
            return jsonify({'error': 'No email address specified'}), 400

        with conn as c:
            with c.cursor() as cur:
                cur.execute("DELETE FROM \"User\" WHERE email=%s;", (email,))
                if cur.rowcount == 0:
                    return jsonify({'error': 'No user with that email exists'}), 400

                return Response(status=204)


def format_restaurants(restaurant_tuples):
    json_objects = []
    i = 0
    while i < len(restaurant_tuples):
        rest_tuple = restaurant_tuples[i]
        address, name, pricerange, phone, image_url, category = rest_tuple
        json_obj = {
            "address": address,
            "name": name,
            "pricerange": pricerange,
            "phone": phone,
            "image_url": image_url,
            "categories": [category]
        }

        while (i+1) < len(restaurant_tuples) and address == restaurant_tuples[i+1][0] and name == restaurant_tuples[i+1][1]:
            json_obj["categories"].append(restaurant_tuples[i+1][5])
            i = i + 1

        json_objects.append(json_obj)
        i = i + 1

    return json_objects


class RestaurantAPI(MethodView):

    def get(self):
        """
        Respond to API call /restaurants?params with a list of all restaurants, encoded as JSON.
        Accepts params as GET arguments, which are documented in build_where.
        :return: JSON response, formatted by format_restaurant.
        """

        def build_where(query_params):
            subqueries = {
                "name": "name = %s",
                "address": "address = %s",
                "pricelt": "pricerange < %s",
                "priceeq": "pricerange = %s",
            }
            selections = []
            params = []
            for k, v in query_params.items():
                if k in subqueries:
                    selections += [subqueries[k]]
                    params += [str(v)]
            if selections:
                where_clause = "WHERE " + " AND ".join(selections)
                return where_clause, params
            return "", ""

        where_clause, where_params = build_where(request.args)
        with conn as c:
            with c.cursor() as cur:
                cur.execute("""SELECT "Restaurant".address, "Restaurant".name, "Restaurant".pricerange, 
                    "Restaurant".phone, "Restaurant".image_url, "RestaurantCategories".category
                    FROM "Restaurant", "RestaurantCategories"
                    {where_clause} AND "Restaurant".name = "RestaurantCategories".restaurant_name 
                    AND "Restaurant".address = "RestaurantCategories".restaurant_address 
                    ORDER BY "Restaurant".name ASC, "Restaurant".address ASC""".format(where_clause=where_clause), where_params)
                rv = cur.fetchall()
                jsonobjects = format_restaurants(rv)
                return jsonify(jsonobjects), 200


class RestaurantCategoriesAPI(MethodView):
    def get(self):
        """
        Respond to API call /restaurant_categories?category=<category>
        :return: JSON response, formatted by format_restaurant.
        """
        category = request.args.get("category")
        if category == None:
            return jsonify({'error': 'No category specified'}), 400

        with conn as c:
            with c.cursor() as cur:
                cur.execute("""SELECT "Restaurant".address, "Restaurant".name, "Restaurant".pricerange, 
                    "Restaurant".phone, "Restaurant".image_url, "SpecificRestaurants".category
                    FROM "Restaurant",
                        (
                            (SELECT * FROM "RestaurantCategories")
                            EXCEPT
                            (SELECT * 
                             FROM "RestaurantCategories" AS "OuterTable"
                             WHERE NOT EXISTS
                                (
                                SELECT * FROM "RestaurantCategories"
                                WHERE "RestaurantCategories".category = %s AND 
                                "RestaurantCategories".restaurant_name = "OuterTable".restaurant_name AND 
                                "RestaurantCategories".restaurant_address = "OuterTable".restaurant_address
                                )
                            ) 
                        ) AS "SpecificRestaurants"
                    WHERE "Restaurant".name = "SpecificRestaurants".restaurant_name 
                    AND "Restaurant".address = "SpecificRestaurants".restaurant_address 
                    ORDER BY "Restaurant".name ASC, "Restaurant".address ASC;""", (category,))
                rv = cur.fetchall()
                jsonobjects = format_restaurants(rv)
                return jsonify(jsonobjects), 200


class RecommendationAPI(MethodView):
    def convert_to_json(self, rows):
        json_objects = []
        for row in rows:
            date, useremail, restaurant_name, restaurant_address = row
            json_obj = {
                'date': date.strftime("%d-%m-%Y %H:%M:%S"), 
                'useremail': useremail,
                'restaurant_name': restaurant_name,
                'restaurant_address': restaurant_address
            }
            json_objects.append(json_obj)

        return json_objects

    def get(self):
        """
        GET /recommendations?useremail=<useremail>
        Response: JSON array of all recommendations for that user
        """
        useremail = request.args.get("useremail")
        if useremail == None:
            return "Missing request arg", 400

        with conn as c:
            with c.cursor() as cur:
                cur.execute("""
                    SELECT date, useremail, restaurant_name, restaurant_address
                    FROM "Recommendation"
                    WHERE useremail = %s
                    """, (useremail,))
                rv = cur.fetchall()
                json_objects = self.convert_to_json(rv)
                return jsonify(json_objects), 200

    def post(self):
        """
        POST /recommendations
        Request:
        {
            "date": <"%d-%m-%Y %H:%M:%S">
            "useremail": <useremail>,
            "restaurant_name": <name>,
            "restaurant_address": <addres>
        }
        """
        json_data = request.get_json()
        date = json_data.get("date")
        useremail = json_data.get("useremail")
        restaurant_name = json_data.get("restaurant_name")
        restaurant_address = json_data.get("restaurant_address")

        if date == None or useremail == None or restaurant_name == None or restaurant_address == None:
            return "Missing request arg", 400

        with conn as c:
            with c.cursor() as cur:
                formatted_date_obj = datetime.strptime(date, "%d-%m-%Y %H:%M:%S")
                cur.execute("""
                    INSERT INTO
                    "Recommendation" (date, useremail, restaurant_name, restaurant_address)
                    VALUES (%s, %s, %s, %s);""", (formatted_date_obj, useremail, restaurant_name, restaurant_address))
                return Response(status=201)


    def delete(self):
        """
        DELETE /recommendations?usermail=<usermail>&restaurant_name=<name>&restaurant_address=Maddress>&date=<date>
        Response is 400 if missing arg, 500 if error, 204 NO CONTENT
        """
        date = request.args.get("date")
        useremail = request.args.get("useremail")
        restaurant_name = request.args.get("restaurant_name")
        restaurant_address = request.args.get("restaurant_address")

        if useremail == None or restaurant_name == None or restaurant_address == None or date == None:
            return "Missing request arg", 400

        with conn as c:
            with c.cursor() as cur:
                formatted_date_obj = datetime.strptime(date, "%d-%m-%Y %H:%M:%S")
                cur.execute("""
                    DELETE FROM "Recommendation"
                    WHERE date = %s
                    AND useremail=%s
                    AND restaurant_name=%s
                    AND restaurant_address=%s
                    """, (formatted_date_obj, useremail, restaurant_name, restaurant_address))
                if cur.rowcount == 0:
                    return jsonify({'error': 'No record to delete'}), 400
                return Response(status=204)


class ReviewAPI(MethodView):
    def convert_to_json(self, rows):
        json_objects = []
        for row in rows:
            useremail, restaurant_name, restaurant_address, description, rating, date = row
            json_obj = {
                'useremail': useremail,
                'restaurant_name': restaurant_name,
                'restaurant_address': restaurant_address,
                'description': description,
                'rating': int(rating),
                'date': date.strftime("%d-%m-%Y %H:%M:%S")
            }
            json_objects.append(json_obj)

        return json_objects

    def get(self):
        """
        GET /reviews?search_user=<bool>...
        if search_user='True': &useremail=<email>
        if search_user='False': &restaurant_name=<name> &restaurant_address=<address>
        """
        search_user = request.args.get("search_user")
        if search_user == None:
            return "Missing Request Arg", 400

        if search_user == 'True':
            useremail = request.args.get("useremail")
            if useremail == None:
                return "Missing Request Arg", 400

            with conn as c:
                with c.cursor() as cur:
                    cur.execute("""
                        SELECT useremail, restaurant_name, restaurant_address, description, rating, date
                        FROM "Review"
                        WHERE useremail=%s;""", (useremail,))
                    rows = cur.fetchall()
                    json_objects = self.convert_to_json(rows)
                    return jsonify(json_objects), 200
        else:
            restaurant_name = request.args.get("restaurant_name")
            restaurant_address = request.args.get("restaurant_address")
            if restaurant_name == None or restaurant_address == None:
                return "Missing Request Arg", 400

            with conn as c:
                with c.cursor() as cur:
                    cur.execute("""
                        SELECT useremail, restaurant_name, restaurant_address, description, rating, date
                        FROM "Review"
                        WHERE restaurant_name=%s
                        AND restaurant_address=%s;""", (restaurant_name, restaurant_address))
                    rows = cur.fetchall()
                    json_objects = self.convert_to_json(rows)
                    return jsonify(json_objects), 200

    def post(self):
        """
        POST /recommendations
        Request:
        {
            "date": <"%d-%m-%Y %H:%M:%S">
            "useremail": <useremail>,
            "restaurant_name": <name>,
            "restaurant_address": <address>,
            "description": <description>,
            "rating": <rating>
        }
        """
        json_data = request.get_json()
        date = json_data.get("date")
        useremail = json_data.get("useremail")
        restaurant_name = json_data.get("restaurant_name")
        restaurant_address = json_data.get("restaurant_address")
        description = json_data.get("description")
        rating = json_data.get("rating")

        if date == None or useremail == None or restaurant_name == None or restaurant_address == None or description == None or rating == None:
            return "Missing request arg", 400

        with conn as c:
            with c.cursor() as cur:
                formatted_date_obj = datetime.strptime(date, "%d-%m-%Y %H:%M:%S")
                cur.execute("""
                    INSERT INTO
                    "Review" (date, useremail, restaurant_name, restaurant_address, description, rating)
                    VALUES (%s, %s, %s, %s, %s, %s);""", (formatted_date_obj, useremail, restaurant_name, restaurant_address, description, rating))
                return Response(status=201)

    def put(self):
        """
        PUT /recommendations
        Request (first 4 params used to identify what to update, last 2 are attributes that can be updated)
        {
            "date": <"%d-%m-%Y %H:%M:%S">
            "useremail": <useremail>,
            "restaurant_name": <name>,
            "restaurant_address": <address>,
            "description": <description>,
            "rating": <rating>
        }
        """
        json_data = request.get_json()
        date = json_data.get("date")
        useremail = json_data.get("useremail")
        restaurant_name = json_data.get("restaurant_name")
        restaurant_address = json_data.get("restaurant_address")
        description = json_data.get("description")
        rating = json_data.get("rating")

        if date == None or useremail == None or restaurant_name == None or restaurant_address == None or (description == None and rating == None):
            return "Missing request arg", 400

        with conn as c:
            with c.cursor() as cur:
                formatted_date_obj = datetime.strptime(date, "%d-%m-%Y %H:%M:%S")
                
                if description != None:
                    cur.execute("""
                        UPDATE "Review"
                        SET description = %s
                        WHERE date = %s AND useremail = %s AND restaurant_name = %s
                        AND restaurant_address = %s;""", (description, formatted_date_obj, useremail, restaurant_name, restaurant_address))
                    if cur.rowcount == 0:
                        return "Record Not Found", 400

                if rating != None:
                    cur.execute("""
                        UPDATE "Review"
                        SET rating = %s
                        WHERE date = %s AND useremail = %s AND restaurant_name = %s
                        AND restaurant_address = %s;""", (rating, formatted_date_obj, useremail, restaurant_name, restaurant_address))
                    if cur.rowcount == 0:
                        return "Record Not Found", 400

                return Response(status=204)

    def delete(self):
        """
        DELETE /recommendations?usermail=<usermail>&restaurant_name=<name>&restaurant_address=Maddress>&date=<date>
        Response is 400 if missing arg, 500 if error, 204 NO CONTENT
        """
        date = request.args.get("date")
        useremail = request.args.get("useremail")
        restaurant_name = request.args.get("restaurant_name")
        restaurant_address = request.args.get("restaurant_address")

        if useremail == None or restaurant_name == None or restaurant_address == None or date == None:
            return "Missing request arg", 400

        with conn as c:
            with c.cursor() as cur:
                formatted_date_obj = datetime.strptime(date, "%d-%m-%Y %H:%M:%S")
                cur.execute("""
                    DELETE FROM "Review"
                    WHERE date = %s
                    AND useremail=%s
                    AND restaurant_name=%s
                    AND restaurant_address=%s
                    """, (formatted_date_obj, useremail, restaurant_name, restaurant_address))
                if cur.rowcount == 0:
                    return jsonify({'error': 'No record to delete'}), 400
                return Response(status=204)



app.add_url_rule('/', 'home', home, methods=['GET'])
app.add_url_rule('/verify_login', 'verify_login', verify_login, methods=['POST'])

user_view = UserAPI.as_view('user_api')
app.add_url_rule('/users', view_func=user_view, methods=['GET', 'POST', 'PUT', 'DELETE'])

restaurant_view = RestaurantAPI.as_view('restaurant_api')
app.add_url_rule('/restaurants', view_func=restaurant_view, methods=['GET'])

restaurant_categories_view = RestaurantCategoriesAPI.as_view('restaurant_categories_api')
app.add_url_rule('/restaurant_categories', view_func=restaurant_categories_view, methods=['GET'])

recommendation_view = RecommendationAPI.as_view('recommendation_api')
app.add_url_rule('/recommendations', view_func=recommendation_view, methods=['GET', 'POST', 'DELETE'])

review_view = ReviewAPI.as_view('review_api')
app.add_url_rule('/reviews', view_func=review_view, methods=['GET', 'POST', 'PUT', 'DELETE'])


if __name__ == "__main__":
    app.run(host='0.0.0.0')
