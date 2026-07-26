import streamlit as st
import pandas as pd
import pickle
import random

# ---------------- Page Config ---------------- #

st.set_page_config(
    page_title="Amazon Product Recommendation System",
    page_icon="🛒",
    layout="wide"
)

# ---------------- Load Data ---------------- #

products = pickle.load(open("products.pkl", "rb"))
similarity = pickle.load(open("similarity.pkl", "rb"))

# ---------------- Header ---------------- #

st.markdown("""
<h1 style='text-align:center;color:#FF9900;'>
🛒 Amazon Product Recommendation System
</h1>
""", unsafe_allow_html=True)

st.markdown("""
<p style='text-align:center;font-size:18px;color:gray;'>
Discover Similar Products using Machine Learning
</p>
""", unsafe_allow_html=True)

# ---------------- Price Cleaning ---------------- #

USD_TO_INR = 83.0  # conversion rate (update as needed)

price = (
    products["Selling Price"]
    .astype(str)
    .str.replace("$", "", regex=False)
    .str.replace(",", "", regex=False)
)

products["Price_Num"] = pd.to_numeric(price, errors="coerce")
products["Price_Num"] = products["Price_Num"].fillna(0)

# Convert to INR for display and filtering
products["Price_INR"] = products["Price_Num"] * USD_TO_INR


def format_inr(amount):
    """Format a number as Indian Rupees with Indian-style comma grouping."""
    amount = round(amount)
    s = str(amount)

    if len(s) <= 3:
        formatted = s
    else:
        last3 = s[-3:]
        rest = s[:-3]
        parts = []
        while len(rest) > 2:
            parts.insert(0, rest[-2:])
            rest = rest[:-2]
        if rest:
            parts.insert(0, rest)
        formatted = ",".join(parts) + "," + last3

    return f"₹{formatted}"

# ---------------- Dashboard ---------------- #

total_products = len(products)

total_categories = (
    products["Category"]
    .fillna("Unknown")
    .nunique()
)

avg_price = products["Price_INR"].mean()

c1, c2, c3, c4 = st.columns(4)

c1.metric("📦 Products", total_products)
c2.metric("🔍 Search", "Ready")
c3.metric("📂 Categories", total_categories)
c4.metric("💰 Avg Price", format_inr(avg_price))

st.divider()

# ---------------- Image Function ---------------- #

def show_image(url, width=220):
    try:
        if pd.notna(url) and str(url).startswith("http"):
            st.image(url, width=width)
        else:
            st.info("No Image Available")
    except Exception:
        st.info("Image Cannot Be Displayed")

# ---------------- Recommendation Function ---------------- #

def recommend_products(product_name, n=5):
    idx = products.index[products["Product Name"] == product_name]

    if len(idx) == 0:
        return pd.DataFrame()

    idx = idx[0]

    distances = sorted(
        list(enumerate(similarity[idx])),
        key=lambda x: x[1],
        reverse=True
    )

    result = []

    for i in distances[1:n + 1]:
        item = products.iloc[i[0]].copy()
        item["Similarity"] = round(i[1] * 100, 2)
        result.append(item)

    return pd.DataFrame(result)

# ---------------- Sidebar ---------------- #

st.sidebar.header("Filter Products")

filtered_products = products.copy()

categories = ["All"] + sorted(
    filtered_products["Category"]
    .fillna("Unknown")
    .unique()
    .tolist()
)

selected_category = st.sidebar.selectbox(
    "Select Category",
    categories,
    key="category_select"
)

if selected_category != "All":
    filtered_products = filtered_products[
        filtered_products["Category"] == selected_category
    ]

sort_option = st.sidebar.selectbox(
    "Sort By",
    ["Default", "Price: Low to High", "Price: High to Low"],
    key="sort_option"
)

min_price = int(filtered_products["Price_INR"].min())
max_price = int(filtered_products["Price_INR"].max())

price_range = st.sidebar.slider(
    "Select Price Range (₹)",
    min_price,
    max_price,
    (min_price, max_price),
    key="price_slider"
)

filtered_products = filtered_products[
    (filtered_products["Price_INR"] >= price_range[0]) &
    (filtered_products["Price_INR"] <= price_range[1])
]

if sort_option == "Price: Low to High":
    filtered_products = filtered_products.sort_values("Price_INR")
elif sort_option == "Price: High to Low":
    filtered_products = filtered_products.sort_values("Price_INR", ascending=False)

st.sidebar.success(f"📦 Products Found: {len(filtered_products)}")

if filtered_products.empty:
    st.warning("No Products Found")
    st.stop()

# ---------------- Product Selection ---------------- #

st.markdown("## 🔍 Search Product")

selected_product = st.selectbox(
    "",
    filtered_products["Product Name"].tolist(),
    label_visibility="collapsed",
    key="product_selector"
)

selected_data = products[products["Product Name"] == selected_product].iloc[0]

# ---------------- Selected Product ---------------- #

st.divider()

st.markdown("## 🛍 Selected Product")

col1, col2 = st.columns([1, 3])

with col1:
    show_image(selected_data["Image"], 300)

with col2:
    st.markdown(
        f"""
        <h2 style="color:#1f77b4;">
        {selected_data["Product Name"]}
        </h2>
        """,
        unsafe_allow_html=True
    )

    st.write(f"**📂 Category:** {selected_data['Category']}")
    st.success(f"💰 Price : {format_inr(selected_data['Price_INR'])}")

    rating = random.choice([
        "⭐⭐⭐⭐⭐ (5.0)",
        "⭐⭐⭐⭐☆ (4.8)",
        "⭐⭐⭐⭐☆ (4.6)",
        "⭐⭐⭐☆☆ (4.2)"
    ])
    st.warning(f"⭐ Rating : {rating}")

    stock = random.choice([
        "🟢 In Stock",
        "🟡 Limited Stock",
        "🔴 Out of Stock"
    ])
    st.info(stock)

    st.success("🚚 Free Delivery")
    st.info("🔒 Secure Payment")

    b1, b2 = st.columns(2)

    with b1:
        st.button("❤️ Add to Wishlist", key="wishlist_btn")

    with b2:
        st.button("🛒 Add to Cart", key="cart_btn")

    st.markdown("### 📝 Product Description")

    st.write(
        "This product is recommended using a Machine Learning "
        "content-based recommendation system. Similar products "
        "are identified based on product features and tags."
    )

st.divider()

recommend_btn = st.button(
    "🚀 Recommend Similar Products",
    use_container_width=True
)

# ---------------- Recommended Products ---------------- #

if recommend_btn:
    st.markdown("## 🎯 Recommended Products")

    recommendations = recommend_products(selected_product)

    if recommendations.empty:
        st.warning("No Recommendations Found")
    else:
        for rank, (_, item) in enumerate(recommendations.iterrows(), start=1):
            st.divider()

            col1, col2 = st.columns([1, 3])

            with col1:
                show_image(item["Image"], 220)

            with col2:
                st.markdown(f"### 🥇 Recommendation #{rank}")

                st.markdown(
                    f"""
                    <h3 style="color:#1f77b4;">
                    {item["Product Name"]}
                    </h3>
                    """,
                    unsafe_allow_html=True
                )

                st.write(f"**📂 Category:** {item['Category']}")
                st.success(f"💰 Price : {format_inr(item['Price_INR'])}")
                st.info(f"🎯 Similarity Score : {item['Similarity']}%")

                if "tags" in item.index:
                    tags = str(item["tags"])
                    st.write("**🏷 Tags:**")
                    if len(tags) > 200:
                        st.write(tags[:200] + "...")
                    else:
                        st.write(tags)

                st.success("✅ Similar product based on Machine Learning recommendation.")
