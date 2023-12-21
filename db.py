import streamlit as st
import mysql.connector
import pandas as pd
import numpy as np
import time

class DB:
    def __init__(self):
        # connect to the database
        try:
            self.conn = conn = mysql.connector.connect(
            host='127.0.0.1',
            port=4306, ## Here Your may be 3306 
            user='root', 
            # password = 'Your Password', # I don't have password but if have then do like this
            database='db' # Database
            )
            self.mycursor = self.conn.cursor()
            print('Connection established')
        except Exception as e:
            print(f'Connection error: {e}')
    
    def fetch_restaurant_names(self):
        r_name = []
        self.mycursor.execute("""SELECT DISTINCT(r_name) FROM restaurants""")
        data = self.mycursor.fetchall()
        for item in data:
            r_name.append(item[0])
        return r_name
    
    def fetch_menu(self, restaurant):
        # Fetch menu items for the selected restaurant
        self.mycursor.execute('''
        SELECT t1.f_name, t2.price FROM food t1
        JOIN 	
        (SELECT f_id, price FROM menu
        WHERE r_id = (SELECT r_id FROM restaurants
			        WHERE r_name = '{}')) t2
        ON t1.f_id = t2.f_id
        '''.format(restaurant))
        data = self.mycursor.fetchall()
        return pd.DataFrame(data, columns=['Food Name','Price'])
    
    # users who never orders
    def never_order(self):
        # Fetch menu items for the selected restaurant
        self.mycursor.execute('''
        SELECT user_id, name, email FROM users
        WHERE user_id NOT IN (SELECT DISTINCT(user_id) FROM orders
                              WHERE user_id IS NOT NULL);
        ''')
        data = self.mycursor.fetchall()
        return pd.DataFrame(data, columns=['user_id', 'name', 'email'])
    
    # veg, non_veg order by users
    def veg_non_veg(self):
        # Fetch menu items for the selected restaurant
        names = []
        frequency1 = []
        frequency2 = []
        self.mycursor.execute('''
        SELECT m2.name, m1.non_veg_count, m1.veg_count FROM 
                            (SELECT user_id,
                            MAX(CASE WHEN type = 'Non-veg' THEN cnt END) AS non_veg_count,
                            MAX(CASE WHEN type = 'Veg' THEN cnt END) AS veg_count
                            FROM (
                                    SELECT u.user_id, f.type, COUNT(*) as cnt FROM users u
                              JOIN orders o ON u.user_id = o.user_id
                              JOIN order_details od ON o.order_id = od.order_id
                              JOIN food f ON od.f_id = f.f_id
                              GROUP BY u.user_id, f.type) t
                            GROUP BY user_id) m1
        JOIN users m2 ON m1.user_id  = m2.user_id ORDER BY m1.veg_count DESC, m1.non_veg_count DESC
        ''')
        data = self.mycursor.fetchall()
        result = pd.DataFrame(data, columns=['name', 'non_veg_count', 'veg_count'])
        for item in data:
            names.append(item[0])
            frequency1.append(item[1])
            frequency2.append(item[-1])
        return result, names, frequency1, frequency2
    
    # order of food type
    def food_order(self):
        
        food_names = []
        frequency1 = []
        self.mycursor.execute('''
            SELECT f_name, COUNt(*) FROM orders o
            JOIN order_details od ON o.order_id = od.order_id
            JOIN food f ON f.f_id = od.f_id
            GROUP BY f_name;
        ''')
        data = self.mycursor.fetchall()
        result = pd.DataFrame(data, columns=['food name', 'Number Of Time Order'])
        for item in data:
            food_names.append(item[0])
            frequency1.append(item[-1])

        return result, food_names, frequency1
    
    def fetch_date_names(self):

        month = []
        r_name = []
        self.mycursor.execute("""
        SELECT monthname(date), r_name FROM orders o
        JOIN restaurants r ON r.r_id  = o.r_id
        """)

        data = self.mycursor.fetchall()

        for item in data:
            month.append(item[0])
            r_name.append(item[-1])

        return list(set(month)), list(set(r_name))
    
    # monthly sales
    def fetch_all_monthly_sales(self, mth, R_N):

        self.mycursor.execute('''
        SELECT monthname(date), SUM(amount) FROM orders o
        JOIN restaurants r ON r.r_id  = o.r_id
        WHERE r_name = '{}' AND monthname(date) = '{}'
        GROUP BY monthname(date)
        '''.format(R_N, mth))
        data = self.mycursor.fetchall()
        return pd.DataFrame(data, columns=['Month_Name', 'Sales'])
    

    def fetch_cheap_restaurant_names(self):

        r_name = []
        avg_price = []
        self.mycursor.execute("""
            SELECT r.r_name, AVG(m.price) AS average_price
            FROM restaurants r
            JOIN menu m ON r.r_id = m.r_id
            GROUP BY r.r_name
            ORDER BY average_price;
        """)

        data = self.mycursor.fetchall()

        for item in data:
            r_name.append(item[0])
            avg_price.append(item[-1])

        return pd.DataFrame(data, columns=['Restaurant Name', 'Avg Price']), r_name, avg_price

    # Find N most paying customers of each month
    def most_paying_names(self, n):

        self.mycursor.execute("""
            SELECT month_name, name, total FROM (SELECT MONTHNAME(date) AS 'month_name',user_id, SUM(amount) AS 'total',			
	        RANK() OVER(PARTITION BY MONTHNAME(date) ORDER BY SUM(amount) DESC) AS 'month_rank'	FROM orders						
	        GROUP BY MONTHNAME(date),user_id						
	        ORDER BY MONTHNAME(date) DESC) t1
            JOIN users t2 ON t1.user_id = t2.user_id
            WHERE t1.month_rank < {}
            ORDER BY month_name DESC
        """.format(n))

        data = self.mycursor.fetchall()

        return pd.DataFrame(data, columns=['Month Name', 'User Name','Total'])
    
    # MOM growth
    def MOM_growth(self):

        month_name = []
        growth_per = []
        self.mycursor.execute("""
            SELECT 
            DATE_FORMAT(date, '%b') AS 'month',
            SUM(amount) AS 'Total',
            ((SUM(amount) - LAG(SUM(amount)) OVER (ORDER BY MONTH(date))) / NULLIF(LAG(SUM(amount)) OVER (ORDER BY MONTH(date)), 0)) * 100 AS 'MOM_growth'
            FROM orders
            GROUP BY MONTH(date)
            ORDER BY MONTH(date);
        """)

        data = self.mycursor.fetchall()

        for item in data:
            month_name.append(item[0])
            growth_per.append(item[-1])

        return pd.DataFrame(data, columns=['Month','Total', 'MOM_growth(%)']), month_name, growth_per
    
    
    # find the growth rate on the basis of n days back date
    def n_growth_rate(self, n, r_name):

        res_name = []
        growth_per = []
        dates = []
        self.mycursor.execute("""
                    SELECT DISTINCT r_name ,date,
	                CASE WHEN `change` IS NULL THEN 0 ELSE `change` END as 'n_day_percent_change'
                    FROM 
                    (SELECT r_id,amount,date,((amount-LAG(amount, {0}) OVER(order by date))/LAG(amount, {0}) OVER(order by date))*100 AS 'change'
                    FROM orders) t1
                    JOIN restaurants t2 ON t1.r_id = t2.r_id WHERE r_name = '{1}';
                """.format(n,r_name))

        data = self.mycursor.fetchall()
        da = pd.DataFrame(data, columns=['r_Name','Date', f'{n}_day_growth(%)'])
        data1 = da.iloc[:,1:]

        for item in data:
            res_name.append(item[0])
            dates.append(item[1])
            growth_per.append(item[-1])

        return data1, res_name[0],dates, growth_per

    def get_id(self):
        self.id = np.nan
        self.mycursor.execute("""
                            SELECT MAX(user_id)+1 FROM users;
                            """)
        data = self.mycursor.fetchall()
        self.id = data[0][0]
        return self.id
    
    # Add User
    def add_user(self, name, email, password):
            if name != '' and email != '' and password != '':
                if email.endswith('@gmail.com') and len(password) >= 6:
                    try:
                        ID = self.get_id()
                        self.mycursor.execute("""
                            INSERT INTO users (user_id , name, email, password) VALUES (%s, %s, %s, %s);
                            """,(ID, name, email, password))
                        # Commit the changes to the database
                        self.conn.commit()
                        return True
                    
                    except Exception as e:
                    # Rollback in case of an error
                        self.conn.rollback()
                        print(f'Error: {e}')
                else:
                    return False
            else:
                return False

    # Log In
    def log_in(self,email, password):
        self.mycursor.execute("""
                    SELECT DISTINCT email, password FROM users;
                """)
        data = self.mycursor.fetchall()

        for item in data:
            if item[0] == email and item[1] == password:
                return True
        return False
    

    # delete user
    def delete_user(self,email):
        try:
            self.mycursor.execute("""
                    DELETE FROM users WHERE email = %s """, (email,))
                # Commit the changes to the database
            self.conn.commit()
            return True
        except Exception as e:
            # Rollback in case of an error
            self.conn.rollback()
            print(f'Error: {e}')
    
    def food_type(self, r_name):
        veg_names = []
        non_veg_names = []
        self.mycursor.execute("""
            SELECT
	            CASE WHEN type = 'Veg' THEN f_name ELSE '' END AS veg_food,
	            CASE WHEN type = 'Non-veg' THEN f_name ELSE '' END AS non_veg_food
                FROM restaurants r
                JOIN menu m ON r.r_id = m.r_id
                JOIN food d ON d.f_id = m.f_id
                WHERE r_name = '{}' """.format(r_name))
        
        data = self.mycursor.fetchall()
        for item in data:
            if item[0] != '':
                veg_names.append(item[0])
            if item[1] != '':
                non_veg_names.append(item[1])
        
        return veg_names, non_veg_names
    
    # get_user_id
    def get_user_id(self, email):
        # email = self.get_email()
        if email:
            self.mycursor.execute("""
                SELECT user_id FROM users
                WHERE email = '{}' """.format(email))
        data = self.mycursor.fetchall()
        if data:
            user_id = data[0][0]
            return user_id
        return None

    # get_r_id
    def get_r_id(self, r_name):
        self.mycursor.execute("""
                    SELECT r_id FROM restaurants WHERE r_name = '{}' """.format(r_name))
        data = self.mycursor.fetchall()
        r_id = data[0][0]
        return r_id
    
    # get_r_id
    def get_food_id(self, V, NV):
        f_id = []
        self.mycursor.execute("""
                    SELECT f_id FROM food WHERE f_name IN ('{}','{}') """.format(V,NV))
        data = self.mycursor.fetchall()
        for item in data:
            f_id.append(item[0]) 
        
        return f_id
    
    # get_amount
    def get_amount(self, r_id, f_id1 = 0, f_id2=0):
        self.mycursor.execute("""
                    SELECT SUM(price) FROM menu
                    WHERE r_id = {} AND f_id IN ({}, {}) """.format(r_id, f_id1, f_id2))
        data = self.mycursor.fetchall()
        amount = data[0][0]
        return amount
    
    # get_order_id
    def get_order_id(self):
        self.mycursor.execute("""
                    SELECT MAX(order_id) +1 FROM orders""")
        data = self.mycursor.fetchall()
        order_id = data[0][0]
        return order_id

    # get_order_details_id
    def get_order_details_id(self):
        self.mycursor.execute("""
                    SELECT MAX(id) +1 FROM order_details""")
        data = self.mycursor.fetchall()
        order_details_id = data[0][0]
        return order_details_id


    # place a order
    def place_order(self, R_N, V_N, N_V_N, email):
        if R_N != '' and (V_N != '' or N_V_N != ''):
            user_id = self.get_user_id(email)
            r_id = self.get_r_id(R_N)
            f_id = self.get_food_id(V_N, N_V_N)
            if len(f_id) == 1: 
                amount = self.get_amount(r_id, f_id)
            else:
                amount = self.get_amount(r_id, f_id[0], f_id[1])

            if f_id:
                order_id = self.get_order_id()
                order_details_id = self.get_order_details_id()

                if user_id != None:
                    try:
                        self.mycursor.execute("""
                            INSERT INTO orders (order_id, user_id, r_id, amount, date) 
                            VALUES (%s, %s, %s, %s, %s);
                        """, (order_id, user_id, r_id, amount, time.strftime("%Y-%m-%d")))
                        self.conn.commit()
                        
                        if len(f_id) == 1:
                            self.mycursor.execute("""
                                INSERT INTO order_details (id, order_id, f_id) 
                                VALUES (%s, %s, %s);
                            """, (order_details_id, order_id, f_id[0]))
                            self.conn.commit()
                        else:
                            self.mycursor.execute("""
                                INSERT INTO order_details (id, order_id, f_id) 
                                VALUES (%s, %s, %s), (%s, %s, %s);
                            """, (order_details_id, order_id, f_id[0], order_details_id+1, order_id, f_id[1]))
                            self.conn.commit()
                        return True
                    
                    except Exception as e:
                        self.conn.rollback()
                        print(f'Error: {e}')
                else:
                    return False