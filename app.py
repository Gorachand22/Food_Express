import streamlit as st
from db import DB
import numpy as np
import plotly.graph_objects as go
import plotly.express as px

db = DB()
session_state = st.session_state

st.title('Welcome to FoodieExpress')
st.write('Choose an option from the sidebar')

# Streamlit App
st.sidebar.title('FoodieExpress')
ln = st.sidebar.selectbox('Account', ['Create Account', 'Log in', 'Delete Account'])

if ln == 'Create Account':
    st.sidebar.title('Create Account')
    name = st.text_input('Enter Name')
    email = st.text_input('Enter email')
    password = st.text_input('Enter password', type='password')

    btn = st.button('Sign Up')
    # if the button is clicked
    if btn:
        result = db.log_in(email, password)
        bar = st.progress(0)

        for i in range(1, 101):
            bar.progress(i)

        if result == False:
            try:
                result1 = db.add_user(name, email, password)
                if result1 == True:
                    st.balloons()
                    st.success('Sign Up Successful')
                    st.info('Now You Can Proceed For Login')
                else:
                    st.error('Sign Up Failed')
            except Exception as e:
                st.error(str(e))
        else:
            st.warning('This Email Is Already Exists, Kindly Log in')

elif ln == 'Log in':
    st.sidebar.title('Log in')
    email = st.text_input('Enter Current email')
    password = st.text_input('Enter Current password', type='password')
    btn = st.button('Sign in')

    if btn or (hasattr(session_state, 'is_logged_in') and session_state.is_logged_in):
        session_state.is_logged_in = True

        user_option = st.sidebar.selectbox('Menu', ['fetch_menu', 'Never Order', 'veg_non_veg', 'Cheap Restaurant',
                                                    'N Most Paying', 'Food Order', 'Monthly Sales', 'MOM Growth',
                                                    'n Day Growth', 'Place a Order'])

        if user_option == 'fetch_menu':
            st.title('Check restaurant\'s name')

            r_name = db.fetch_restaurant_names()

            source = st.selectbox('Restaurants', sorted(r_name))
            if st.button('Search'):
                results = db.fetch_menu(source)
                st.dataframe(results)

        # Which flight from Source to Destination is the cheapest, and what is its price?
        elif user_option == 'Never Order':
            st.title('Never Order')
            if st.button('Check'):
                results = db.never_order()
                st.dataframe(results)

        # Veg and nonveg orders
        elif user_option == 'veg_non_veg':
            st.title('Veg Vs Nonveg')
            results, names, frequency1, frequency2 = db.veg_non_veg()
            if st.button('Check'):
                st.dataframe(results)

            if st.button('Analysis'):
                # bar graph for Non-Veg
                fig_non_veg = px.bar(
                    x=names,
                    y=frequency1,
                    labels={'x': 'Names', 'y': 'Non-Veg Count'},
                    color=names)
                st.header("For Non Veg")
                st.plotly_chart(fig_non_veg, theme="streamlit", use_container_width=True)

                # bar graph for Veg
                fig_veg = px.bar(
                    x=names,
                    y=frequency2,
                    labels={'x': 'Names', 'y': 'Veg Count'},
                    color=names)
                st.header("For Veg")
                st.plotly_chart(fig_veg, theme="streamlit", use_container_width=True)

        # food Orders
        elif user_option == 'Food Order':
            st.title('Food Vs Number of time order')
            results, names, frequency1 = db.food_order()
            if st.button('Check'):
                st.dataframe(results)

            if st.button('Analysis'):
                # bar graph
                fig = px.bar(
                    x=names,
                    y=frequency1,
                    labels={'x': 'Food Names', 'y': 'Number Of Order'},
                    color=names)
                st.header("Bar Graph")
                st.plotly_chart(fig, theme="streamlit", use_container_width=True)

        elif user_option == 'Monthly Sales':
            st.title('Monthly Sales')
            col1, col2 = st.columns(2)

            month, r_Name = db.fetch_date_names()

            with col1:
                mth = st.selectbox('Month', sorted(month))
            with col2:
                R_N = st.selectbox('Restaurant Names', sorted(r_Name))

            if st.button('Extract Sales'):
                results = db.fetch_all_monthly_sales(mth, R_N)
                st.dataframe(results)

        # Cheap Restaurant
        elif user_option == 'Cheap Restaurant':
            st.title('Cheap Restaurant')
            results, R_Name, avg_price = db.fetch_cheap_restaurant_names()
            if st.button('Check'):
                st.dataframe(results)

            if st.button('Analysis'):
                # bar graph
                fig = px.bar(
                    x=R_Name,
                    y=avg_price,
                    labels={'x': 'Restaurant Names', 'y': 'Avg Price'},
                    color=R_Name)
                st.header("Bar Graph")
                st.plotly_chart(fig, theme="streamlit", use_container_width=True)

        elif user_option == 'N Most Paying':
            st.title('N Most Paying Users')
            n = np.arange(1, 6)
            nth = st.selectbox('users', sorted(n))
            if st.button('Search'):
                results = db.most_paying_names(nth)
                st.dataframe(results)

        # food Orders
        elif user_option == 'MOM Growth':
            st.title('MOM Growth')
            results, month_name, growth_per = db.MOM_growth()
            if st.button('Check'):
                st.dataframe(results)

            if st.button('Analysis'):
                # line plot
                fig = px.line(
                    x=month_name,
                    y=growth_per,
                    labels={'x': 'Month Names', 'y': 'Growth Rate(%)'},
                    line_shape="linear",  # You can change the line shape if desired
                    markers=True,  # Display markers on the line
                    color_discrete_sequence=["red"]
                )  # Set line color
                st.header("Line Plot")
                st.plotly_chart(fig, theme="streamlit", use_container_width=True)

        # # find the growth rate on the basis of n days back date
        elif user_option == 'n Day Growth':
            st.title('n Day Growth')
            col1, col2 = st.columns(2)

            r_Name = db.fetch_restaurant_names()
            n = np.arange(1, 11)

            with col1:
                mth = st.selectbox('Day', sorted(n))
            with col2:
                R_N = st.selectbox('Restaurant Names', sorted(r_Name))
            results, res_name, dates, growth_per = db.n_growth_rate(mth, R_N)
            if st.button('Check'):
                st.dataframe(results)

            if st.button('Analysis'):
                # line plot
                fig = px.line(
                    x=dates,
                    y=growth_per,
                    labels={'x': 'Dates', 'y': 'Growth Rate(%)'},
                    line_shape="linear",  # You can change the line shape if desired
                    markers=True,  # Display markers on the line
                    color_discrete_sequence=["red"]
                )  # Set line color
                st.header(f'{res_name} {mth}_Day_Growth(%)')
                st.plotly_chart(fig, theme="streamlit", use_container_width=True)
        
        # # find the growth rate on the basis of n days back date
        elif user_option == 'Place a Order':
            st.title('Place a Order')

            r_Name = db.fetch_restaurant_names()
            R_N = st.selectbox('Restaurant Names', sorted(r_Name))
            veg_names,non_veg_names  = db.food_type(R_N)
            col2, col3 = st.columns(2)
            with col2:
                V_N = st.selectbox('Veg Foods', sorted(veg_names))
            with col2:
                N_V_N = st.selectbox('Non Veg Foods', sorted(non_veg_names))
                
            if st.button('Order'):
                result = db.place_order(R_N, V_N, N_V_N, email)
                if result == True:
                    st.success('Order Placed')
                else:
                    st.error('Order Failed')
        else:
            st.error('Incorrect Email or Password')

elif ln == 'Delete Account':
    st.sidebar.title('Delete Account')
    email = st.text_input('Enter Current email')
    password = st.text_input('Enter Current password', type='password')
    btn = st.button('Delete')
    
    # if the button is clicked
    if btn:
        result = db.log_in(email, password)
        bar = st.progress(0)

        for i in range(1, 101):
            bar.progress(i)
        
        if result == True:
            try:
                result1 = db.delete_user(email)
                if result1 == True:
                    st.warning('Delete Successful')
                else:
                    st.error('Delete Failed')
            except Exception as e:
                st.error(str(e))
        else:
            st.warning('This Email Is Not Registered, Kindly Register first')