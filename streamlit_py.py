import time
import streamlit as st
import pandas as pd
from functools import wraps


# Initialize global variable for execution time
total_execution_time = 0.0
st.set_page_config(layout="wide")

def time_tracker(threshold=0.0):
    """Decorator to track function execution time."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            global total_execution_time
            start = time.time()
            result = func(*args, **kwargs)
            end = time.time()
            execution_time = end - start
            total_execution_time += execution_time  # Fix accumulation

            if execution_time > threshold:
                st.warning(f"⚠️ {func.__name__} exceeded the threshold of {threshold:.2f} seconds")

            return result

        return wrapper

    return decorator


@time_tracker(threshold=1.0)
def read_excel_file(source, sheet_name, skiprows):
    """Reads Excel file and returns a DataFrame."""
    df = pd.read_excel(source, sheet_name=sheet_name, engine='openpyxl', skiprows=skiprows)
    #print("Raw Data (Immediately after reading):\n", df)  # Debug print
    return df
@time_tracker(threshold=1.0)
def try_convert_date(date_str):
    for fmt in ('%m/%d/%y', '%m/%d/%Y', '%m-%d-%y', '%m-%d-%Y'):  # Add more formats as needed
        try:
            return pd.to_datetime(date_str, format=fmt, errors='raise').strftime('%m/%d/%Y')
        except ValueError:
            pass  # Try the next format
    return ''  # Return empty string if none of the formats match

@time_tracker(threshold=1.0)
def watch_list(df):
    member_name = df.columns[3] # column D
    final_rating = df.columns[26] # column AA
    last_ccr = df.columns[32]  # column AG
    last_qrr = df.columns[34]   # column AI
    comments = df.columns[35]

    # Convert 'Final Rating' to Numeric

    df[final_rating] = pd.to_numeric(df[final_rating], errors='coerce')

    # Fix Date Formatting: Handle Excel Serial Dates
    df[last_ccr] = pd.to_datetime(df[last_ccr], errors='coerce').dt.strftime('%m/%d/%Y').fillna('')
    df[last_qrr] = pd.to_datetime(df[last_qrr], errors='coerce').dt.strftime('%m/%d/%Y').fillna('')

    df[comments] = df[comments].fillna('')

    # Filter Data
    watchlist_df = df[(df[final_rating] > 5) & df[member_name].notna() & (df[member_name] != '')]
    watchlist_df=watchlist_df.reset_index(drop=True)

    watchlist_df = watchlist_df[~watchlist_df.iloc[:, 0].astype(str).str.contains('conting', case=False, na=False)]
    #watchlist_df = watchlist_df.iloc[:, 1:]
    # Rename & Sort
    pivot_data = watchlist_df[[member_name, final_rating, last_ccr, last_qrr, comments]]

    pivot_data.columns = ['Member Name', 'Final Rating', 'Last CCR', 'Last QRR', 'Comments']
    pivot_data = pivot_data.sort_values(by='Final Rating', ascending=False)
    pivot_data= pivot_data.reset_index(drop=True)
    pivot_data.index = pivot_data.index + 1
    # Apply CSS styling to make 'Comments' column wider

    return pivot_data

@time_tracker(threshold=1.0)
def outstanding_indebtedness(df):
    member_name = df.columns[1]
    total_assets = df.columns[5]
    exposure = df.columns[10]
    borrowing_capacity = df.columns[14]
    remaining_capacity_repo = df.columns[25]
    remaining_capacity_non_repo = df.columns[26]


    # Convert columns to numeric
    df[exposure] = pd.to_numeric(df[exposure], errors='coerce').round(0)
    df[borrowing_capacity] = pd.to_numeric(df[borrowing_capacity], errors='coerce')
    df[remaining_capacity_repo] = pd.to_numeric(df[remaining_capacity_repo], errors='coerce')
    df[remaining_capacity_non_repo] = pd.to_numeric(df[remaining_capacity_non_repo], errors='coerce')

    df = df[df[exposure].notna() & (df[exposure] != 0)]

    # Extract and rename relevant columns
    data = df[[member_name, exposure, borrowing_capacity, remaining_capacity_repo, remaining_capacity_non_repo]].copy()
    data.columns = ['Member Name', 'Exposure', 'Borrowing Capacity', 'Remaining Capacity (Repo)', 'Remaining Capacity (Non-Repo)']

    # Sort data by exposure and reset index
    data = data.sort_values(by='Exposure', ascending=False).reset_index(drop=True)
    data.index = data.index + 1  # Start index at 1 for readability

    return data



# Streamlit UI
st.title("📊 Risk Report Dashboard as of 02-10-2025")

comprehensive = "/Users/admin/Documents/FLBNY/Book1.xlsx"
outsanding_indeb_file = "/Users/admin/Documents/FLBNY/Outstanding Indebtedness-02-07-2025-23-45-00.xlsx"

if st.button("🔄 Refresh Data"):
    with st.spinner("Processing..."):
        #st.set_page_config(layout="wide")

        df = read_excel_file(comprehensive, sheet_name="Schedule", skiprows=4)
        df2 = read_excel_file(outsanding_indeb_file, sheet_name="Member Outstanding Indebtedness", skiprows=2)

        processed_watch = watch_list(df)
        processed_outsantind_indebt = outstanding_indebtedness(df2)
        #st.success("Data processed successfully!")
        col1,col2 = st.columns(2)
        with col1:
            st.markdown("<h3 style='text-align: center;'>Watchlist</h3>", unsafe_allow_html=True)
            st.dataframe(processed_watch)
            st.write(f" Watchlist Memebers: {processed_watch.shape[0]}")

        with col2:
            st.markdown("<h3 style='text-align: center;'>Top Borrowers</h3>", unsafe_allow_html=True)
            st.dataframe(processed_outsantind_indebt)
            st.write(f" Total members who borrow: {processed_outsantind_indebt.shape[0]}")
        col3,col4 = st.columns(2)
        with col3:
            st.markdown("<h3 style='text-align: center;'>Rating Migration QoQ</h3>", unsafe_allow_html=True)

        with col4:
            st.markdown("<h3 style='text-align: center;'>Reviews in Progress</h3>", unsafe_allow_html=True)
        # Show execution time

        st.write(f"⏳ **Total Execution Time:** {total_execution_time:.4f} seconds")
