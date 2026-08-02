import streamlit as st
import pandas as pd
import pickle
import random
import sqlite3
import os

# ============================================================
#  PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="Amazon Product Recommendation System",
    page_icon="🛒",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================
#  SQLITE PERSISTENCE (wishlist & cart survive restarts/refreshes)
# ============================================================

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "app_data.db")


def get_conn():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS wishlist (
            product_name TEXT PRIMARY KEY
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS cart (
            product_name TEXT PRIMARY KEY,
            qty INTEGER DEFAULT 1
        )
    """)
    conn.commit()
    return conn


def db_load_set(table):
    conn = get_conn()
    rows = conn.execute(f"SELECT product_name FROM {table}").fetchall()
    conn.close()
    return set(r[0] for r in rows)


def db_add(table, product_name):
    conn = get_conn()
    conn.execute(f"INSERT OR IGNORE INTO {table} (product_name) VALUES (?)", (product_name,))
    conn.commit()
    conn.close()


def db_remove(table, product_name):
    conn = get_conn()
    conn.execute(f"DELETE FROM {table} WHERE product_name = ?", (product_name,))
    conn.commit()
    conn.close()


def db_clear(table):
    conn = get_conn()
    conn.execute(f"DELETE FROM {table}")
    conn.commit()
    conn.close()

# ============================================================
#  SESSION STATE INIT (hydrated from SQLite on first load)
# ============================================================

if "dark_mode" not in st.session_state:
    st.session_state.dark_mode = False

if "db_loaded" not in st.session_state:
    st.session_state.wishlist = db_load_set("wishlist")
    st.session_state.cart = db_load_set("cart")
    st.session_state.db_loaded = True

# ============================================================
#  SIDEBAR — APPEARANCE (must run before CSS is generated)
# ============================================================

st.sidebar.header("⚙️ Appearance")
st.session_state.dark_mode = st.sidebar.toggle(
    "🌙 Dark Mode", value=st.session_state.dark_mode, key="dark_mode_toggle"
)

# ============================================================
#  GLOBAL STYLE (custom CSS, theme-aware for light/dark mode)
# ============================================================

if st.session_state.dark_mode:
    THEME = dict(
        bg="#0E1117", card_bg="#1A1D24", border="#2A2E37",
        text="#F5F5F5", subtext="#9CA3AF", heading="#F5F5F5",
        price_bg="#123524", price_text="#4ADE80",
        badge_green_bg="#123524", badge_green_text="#4ADE80",
        badge_amber_bg="#3A2E12", badge_amber_text="#FBBF24",
        badge_red_bg="#3A1518", badge_red_text="#F87171",
        badge_blue_bg="#122A3A", badge_blue_text="#60A5FA",
        accent="#FF9900",
    )
else:
    THEME = dict(
        bg="#FAFAFA", card_bg="#FFFFFF", border="#ECECEC",
        text="#131921", subtext="#6b7280", heading="#131921",
        price_bg="#EAF7EE", price_text="#067D3F",
        badge_green_bg="#EAF7EE", badge_green_text="#067D3F",
        badge_amber_bg="#FFF6E5", badge_amber_text="#B7791F",
        badge_red_bg="#FDEDEE", badge_red_text="#C0392B",
        badge_blue_bg="#EAF2FE", badge_blue_text="#1D4ED8",
        accent="#FF9900",
    )

st.markdown(f"""
<style>
    .main {{
        background-color: {THEME['bg']};
    }}
    .stApp {{
        background-color: {THEME['bg']};
        color: {THEME['text']};
    }}

    .hero-title {{
        text-align: center;
        font-size: 42px;
        font-weight: 800;
        color: {THEME['accent']};
        margin-bottom: 0px;
        letter-spacing: -0.5px;
    }}
    .hero-subtitle {{
        text-align: center;
        font-size: 16px;
        color: {THEME['subtext']};
        margin-top: 4px;
        margin-bottom: 20px;
    }}

    .product-card {{
        background-color: {THEME['card_bg']};
        border: 1px solid {THEME['border']};
        border-radius: 14px;
        padding: 22px 26px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.08);
        margin-bottom: 14px;
    }}

    .product-title {{
        font-size: 22px;
        font-weight: 700;
        color: {THEME['heading']};
        margin-bottom: 6px;
    }}

    .price-tag {{
        display: inline-block;
        background-color: {THEME['price_bg']};
        color: {THEME['price_text']};
        font-weight: 700;
        font-size: 16px;
        padding: 6px 14px;
        border-radius: 8px;
        margin-right: 8px;
    }}

    .badge {{
        display: inline-block;
        font-size: 13px;
        font-weight: 600;
        padding: 4px 10px;
        border-radius: 20px;
        margin-right: 6px;
        margin-top: 6px;
    }}
    .badge-green {{ background-color: {THEME['badge_green_bg']}; color: {THEME['badge_green_text']}; }}
    .badge-amber {{ background-color: {THEME['badge_amber_bg']}; color: {THEME['badge_amber_text']}; }}
    .badge-red   {{ background-color: {THEME['badge_red_bg']};   color: {THEME['badge_red_text']}; }}
    .badge-blue  {{ background-color: {THEME['badge_blue_bg']};  color: {THEME['badge_blue_text']}; }}

    .section-heading {{
        font-size: 26px;
        font-weight: 700;
        color: {THEME['heading']};
        margin-top: 10px;
        margin-bottom: 10px;
        border-left: 5px solid {THEME['accent']};
        padding-left: 12px;
    }}

    .rec-rank {{
        display: inline-block;
        background-color: {THEME['accent']};
        color: white;
        font-weight: 700;
        font-size: 13px;
        padding: 3px 10px;
        border-radius: 20px;
        margin-bottom: 6px;
    }}

    .review-card {{
        background-color: {THEME['card_bg']};
        border: 1px solid {THEME['border']};
        border-radius: 10px;
        padding: 14px 18px;
        margin-bottom: 10px;
    }}
    .review-author {{
        font-weight: 700;
        color: {THEME['heading']};
        font-size: 14px;
    }}
    .review-text {{
        color: {THEME['subtext']};
        font-size: 14px;
        margin-top: 4px;
    }}

    div[data-testid="stMetric"] {{
        background-color: {THEME['card_bg']};
        border: 1px solid {THEME['border']};
        border-radius: 12px;
        padding: 14px;
        box-shadow: 0 1px 6px rgba(0,0,0,0.06);
    }}

    footer {{visibility: hidden;}}
</style>
""", unsafe_allow_html=True)

# ============================================================
#  DATA LOADING (cached so it doesn't reload on every rerun)
# ============================================================

@st.cache_data(show_spinner="Loading product catalog...")
def load_data():
    try:
        products = pickle.load(open("products.pkl", "rb"))
        similarity = pickle.load(open("similarity.pkl", "rb"))
        return products, similarity
    except FileNotFoundError:
        st.error(
            "⚠️ Required data files not found. Make sure `products.pkl` "
            "and `similarity.pkl` are in the app directory."
        )
        st.stop()
    except Exception as e:
        st.error(f"⚠️ Failed to load data: {e}")
        st.stop()


products, similarity = load_data()

# ============================================================
#  HEADER
# ============================================================

st.markdown("<div class='hero-title'>🛒 Amazon Product Recommendation System</div>", unsafe_allow_html=True)
st.markdown("<div class='hero-subtitle'>Discover similar products using content-based Machine Learning</div>", unsafe_allow_html=True)

# ============================================================
#  PRICE CLEANING / CONVERSION
# ============================================================

USD_TO_INR = 83.0  # update as needed

@st.cache_data(show_spinner=False)
def prepare_prices(df):
    df = df.copy()
    price = (
        df["Selling Price"]
        .astype(str)
        .str.replace("$", "", regex=False)
        .str.replace(",", "", regex=False)
    )
    df["Price_Num"] = pd.to_numeric(price, errors="coerce").fillna(0)
    df["Price_INR"] = df["Price_Num"] * USD_TO_INR
    return df


products = prepare_prices(products)


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

# ============================================================
#  DASHBOARD METRICS
# ============================================================

total_products = len(products)
total_categories = products["Category"].fillna("Unknown").nunique()
avg_price = products["Price_INR"].mean()
max_price_overall = products["Price_INR"].max()

c1, c2, c3, c4 = st.columns(4)
c1.metric("📦 Total Products", f"{total_products:,}")
c2.metric("📂 Categories", total_categories)
c3.metric("💰 Avg. Price", format_inr(avg_price))
c4.metric("🏆 Highest Price", format_inr(max_price_overall))

st.divider()

# ============================================================
#  INSIGHTS / ANALYTICS
# ============================================================

with st.expander("📊 Catalog Insights", expanded=False):
    ic1, ic2 = st.columns(2)

    with ic1:
        st.markdown("**Products per Category**")
        cat_counts = (
            products["Category"].fillna("Unknown")
            .value_counts()
            .head(10)
            .sort_values(ascending=True)
        )
        st.bar_chart(cat_counts, horizontal=True, color=THEME["accent"])

    with ic2:
        st.markdown("**Price Distribution (₹)**")
        price_bins = pd.cut(
            products.loc[products["Price_INR"] > 0, "Price_INR"],
            bins=10
        ).value_counts().sort_index()
        price_bins.index = [f"{int(iv.left):,}–{int(iv.right):,}" for iv in price_bins.index]
        st.bar_chart(price_bins, color=THEME["accent"])

# ============================================================
#  HELPERS
# ============================================================

def show_image(url, width=220):
    if pd.notna(url) and str(url).startswith("http"):
        try:
            st.image(url, width=width)
        except Exception:
            st.info("🖼 Image could not be displayed")
    else:
        st.info("🖼 No image available")


# Deterministic "fake" rating/stock so the same product always shows the
# same value in a session (instead of re-randomizing on every interaction).
@st.cache_data(show_spinner=False)
def get_display_meta(product_name):
    seed = abs(hash(product_name)) % (10 ** 6)
    rnd = random.Random(seed)
    rating = rnd.choice([
        ("⭐⭐⭐⭐⭐", 5.0),
        ("⭐⭐⭐⭐☆", 4.8),
        ("⭐⭐⭐⭐☆", 4.6),
        ("⭐⭐⭐☆☆", 4.2),
    ])
    stock = rnd.choice(["In Stock", "Limited Stock", "Out of Stock"])
    return rating, stock


# Deterministic placeholder reviews, generated per product (illustrative only —
# swap this out for real review data if/when you have it).
REVIEW_POOL = [
    ("Priya S.", "Exactly as described, delivery was quick. Would buy again."),
    ("Rahul K.", "Good value for the price. Build quality feels solid."),
    ("Ananya M.", "Matches the photos, packaging was neat and secure."),
    ("Vikram T.", "Does the job well. Nothing fancy but reliable."),
    ("Sneha R.", "Really happy with this purchase, exceeded expectations."),
    ("Arjun D.", "Decent product, took a couple of days longer to arrive."),
]

@st.cache_data(show_spinner=False)
def get_reviews(product_name, n=3):
    seed = abs(hash(product_name + "_reviews")) % (10 ** 6)
    rnd = random.Random(seed)
    picks = rnd.sample(REVIEW_POOL, k=min(n, len(REVIEW_POOL)))
    reviews = []
    for author, text in picks:
        stars = rnd.choice(["⭐⭐⭐⭐⭐", "⭐⭐⭐⭐☆", "⭐⭐⭐☆☆"])
        reviews.append((author, stars, text))
    return reviews


def stock_badge(stock):
    mapping = {
        "In Stock": ("badge-green", "🟢"),
        "Limited Stock": ("badge-amber", "🟡"),
        "Out of Stock": ("badge-red", "🔴"),
    }
    cls, icon = mapping.get(stock, ("badge-blue", "🔵"))
    return f"<span class='badge {cls}'>{icon} {stock}</span>"


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


def toggle_wishlist(product_name):
    if product_name in st.session_state.wishlist:
        st.session_state.wishlist.discard(product_name)
        db_remove("wishlist", product_name)
        st.toast("Removed from wishlist", icon="💔")
    else:
        st.session_state.wishlist.add(product_name)
        db_add("wishlist", product_name)
        st.toast("Added to wishlist", icon="❤️")


def add_to_cart(product_name):
    st.session_state.cart.add(product_name)
    db_add("cart", product_name)
    st.toast("Added to cart", icon="🛒")

# ============================================================
#  SIDEBAR — FILTERS
# ============================================================

st.sidebar.header("🔧 Filter Products")

filtered_products = products.copy()

categories = ["All"] + sorted(
    filtered_products["Category"].fillna("Unknown").unique().tolist()
)

selected_category = st.sidebar.selectbox("Category", categories, key="category_select")

if selected_category != "All":
    filtered_products = filtered_products[filtered_products["Category"] == selected_category]

sort_option = st.sidebar.selectbox(
    "Sort By",
    ["Default", "Price: Low to High", "Price: High to Low"],
    key="sort_option"
)

min_price = int(filtered_products["Price_INR"].min())
max_price = int(filtered_products["Price_INR"].max())

if min_price == max_price:
    st.sidebar.info(f"Only one price point available: {format_inr(min_price)}")
    price_range = (min_price, max_price)
else:
    price_range = st.sidebar.slider(
        "Price Range (₹)", min_price, max_price, (min_price, max_price), key="price_slider"
    )

num_recs = st.sidebar.slider("Number of recommendations", 3, 10, 5, key="num_recs")

filtered_products = filtered_products[
    (filtered_products["Price_INR"] >= price_range[0]) &
    (filtered_products["Price_INR"] <= price_range[1])
]

if sort_option == "Price: Low to High":
    filtered_products = filtered_products.sort_values("Price_INR")
elif sort_option == "Price: High to Low":
    filtered_products = filtered_products.sort_values("Price_INR", ascending=False)

st.sidebar.success(f"📦 {len(filtered_products)} products match your filters")

# ============================================================
#  SIDEBAR — WISHLIST (persisted in SQLite)
# ============================================================

st.sidebar.divider()
st.sidebar.header(f"❤️ Wishlist ({len(st.session_state.wishlist)})")

if st.session_state.wishlist:
    wishlist_df = products[products["Product Name"].isin(st.session_state.wishlist)]

    for _, w in wishlist_df.iterrows():
        wcol1, wcol2 = st.sidebar.columns([4, 1])
        wcol1.caption(f"• {w['Product Name'][:32]}{'...' if len(w['Product Name']) > 32 else ''}")
        if wcol2.button("✕", key=f"remove_wish_{w['Product Name']}"):
            toggle_wishlist(w["Product Name"])
            st.rerun()

    wcsv = wishlist_df[["Product Name", "Category", "Price_INR"]].rename(
        columns={"Price_INR": "Price (INR)"}
    )
    st.sidebar.download_button(
        "⬇️ Export Wishlist (CSV)",
        data=wcsv.to_csv(index=False).encode("utf-8"),
        file_name="wishlist.csv",
        mime="text/csv",
        use_container_width=True,
        key="export_wishlist"
    )

    if st.sidebar.button("Clear Wishlist", key="clear_wishlist", use_container_width=True):
        st.session_state.wishlist = set()
        db_clear("wishlist")
        st.rerun()
else:
    st.sidebar.caption("No items yet — tap ❤️ Add to Wishlist on any product.")

# ============================================================
#  SIDEBAR — CART (persisted in SQLite)
# ============================================================

st.sidebar.divider()
st.sidebar.header(f"🛒 Cart ({len(st.session_state.cart)})")

if st.session_state.cart:
    cart_df = products[products["Product Name"].isin(st.session_state.cart)]

    for _, c in cart_df.iterrows():
        ccol1, ccol2 = st.sidebar.columns([4, 1])
        ccol1.caption(f"• {c['Product Name'][:28]}{'...' if len(c['Product Name']) > 28 else ''} — {format_inr(c['Price_INR'])}")
        if ccol2.button("✕", key=f"remove_cart_{c['Product Name']}"):
            st.session_state.cart.discard(c["Product Name"])
            db_remove("cart", c["Product Name"])
            st.rerun()

    cart_total = cart_df["Price_INR"].sum()
    st.sidebar.markdown(f"**Total: {format_inr(cart_total)}**")

    ccsv = cart_df[["Product Name", "Category", "Price_INR"]].rename(
        columns={"Price_INR": "Price (INR)"}
    )
    st.sidebar.download_button(
        "⬇️ Export Cart (CSV)",
        data=ccsv.to_csv(index=False).encode("utf-8"),
        file_name="cart.csv",
        mime="text/csv",
        use_container_width=True,
        key="export_cart"
    )

    if st.sidebar.button("Clear Cart", key="clear_cart", use_container_width=True):
        st.session_state.cart = set()
        db_clear("cart")
        st.rerun()
else:
    st.sidebar.caption("Cart is empty — tap 🛒 Add to Cart on any product.")

if filtered_products.empty:
    st.warning("No products found for the selected filters. Try widening your price range or category.")
    st.stop()

# ============================================================
#  PRODUCT SEARCH / SELECT
# ============================================================

st.markdown("<div class='section-heading'>🔍 Search Product</div>", unsafe_allow_html=True)

selected_product = st.selectbox(
    "",
    filtered_products["Product Name"].tolist(),
    label_visibility="collapsed",
    key="product_selector"
)

selected_data = products[products["Product Name"] == selected_product].iloc[0]

# ============================================================
#  SELECTED PRODUCT PANEL
# ============================================================

st.markdown("<div class='section-heading'>🛍 Selected Product</div>", unsafe_allow_html=True)

st.markdown("<div class='product-card'>", unsafe_allow_html=True)
col1, col2 = st.columns([1, 3])

with col1:
    show_image(selected_data["Image"], 260)

with col2:
    st.markdown(f"<div class='product-title'>{selected_data['Product Name']}</div>", unsafe_allow_html=True)
    st.caption(f"📂 {selected_data['Category']}")

    st.markdown(f"<span class='price-tag'>💰 {format_inr(selected_data['Price_INR'])}</span>", unsafe_allow_html=True)

    rating, stock = get_display_meta(selected_data["Product Name"])
    st.markdown(
        f"<span class='badge badge-amber'>{rating[0]} ({rating[1]})</span>"
        + stock_badge(stock)
        + "<span class='badge badge-blue'>🚚 Free Delivery</span>"
        + "<span class='badge badge-blue'>🔒 Secure Payment</span>",
        unsafe_allow_html=True
    )

    st.write("")

    is_wishlisted = selected_product in st.session_state.wishlist
    is_in_cart = selected_product in st.session_state.cart

    b1, b2 = st.columns(2)
    with b1:
        wish_label = "💔 Remove from Wishlist" if is_wishlisted else "❤️ Add to Wishlist"
        if st.button(wish_label, key="wishlist_btn", use_container_width=True):
            toggle_wishlist(selected_product)
            st.rerun()
    with b2:
        cart_label = "✅ In Cart" if is_in_cart else "🛒 Add to Cart"
        if st.button(cart_label, key="cart_btn", use_container_width=True, type="primary", disabled=is_in_cart):
            add_to_cart(selected_product)
            st.rerun()

    with st.expander("📝 Product Description"):
        st.write(
            "This product is recommended using a machine-learning "
            "content-based recommendation system. Similar products "
            "are identified based on shared product features and tags."
        )

    with st.expander("💬 Customer Reviews"):
        for author, stars, text in get_reviews(selected_product):
            st.markdown(
                f"""<div class='review-card'>
                <span class='review-author'>{author}</span> &nbsp; {stars}
                <div class='review-text'>{text}</div>
                </div>""",
                unsafe_allow_html=True
            )

st.markdown("</div>", unsafe_allow_html=True)

st.write("")

if "show_recs" not in st.session_state:
    st.session_state.show_recs = False

if st.button("🚀 Recommend Similar Products", use_container_width=True, type="primary"):
    st.session_state.show_recs = True

# ============================================================
#  RECOMMENDATIONS
# ============================================================

if st.session_state.show_recs:
    top_row1, top_row2 = st.columns([5, 1])
    with top_row1:
        st.markdown("<div class='section-heading'>🎯 Recommended For You</div>", unsafe_allow_html=True)
    with top_row2:
        if st.button("✕ Hide", key="hide_recs", use_container_width=True):
            st.session_state.show_recs = False
            st.rerun()

    with st.spinner("Finding similar products..."):
        recommendations = recommend_products(selected_product, n=num_recs)

    if recommendations.empty:
        st.warning("No recommendations found for this product.")
    else:
        rows = list(recommendations.iterrows())
        for row_start in range(0, len(rows), 2):
            pair = rows[row_start:row_start + 2]
            grid_cols = st.columns(len(pair))

            for col, (rank_offset, (_, item)) in zip(grid_cols, enumerate(pair)):
                rank = row_start + rank_offset + 1
                with col:
                    st.markdown("<div class='product-card'>", unsafe_allow_html=True)
                    show_image(item["Image"], 220)

                    st.markdown(f"<span class='rec-rank'>#{rank} MATCH</span>", unsafe_allow_html=True)
                    st.markdown(f"<div class='product-title' style='font-size:18px'>{item['Product Name']}</div>", unsafe_allow_html=True)
                    st.caption(f"📂 {item['Category']}")

                    st.markdown(f"<span class='price-tag'>💰 {format_inr(item['Price_INR'])}</span>", unsafe_allow_html=True)
                    st.progress(min(int(item["Similarity"]), 100), text=f"🎯 {item['Similarity']}% match")

                    if "tags" in item.index:
                        tags = str(item["tags"])
                        with st.expander("🏷 Tags"):
                            st.write(tags[:300] + ("..." if len(tags) > 300 else ""))

                    st.write("")

                    rec_wishlisted = item["Product Name"] in st.session_state.wishlist
                    rec_in_cart = item["Product Name"] in st.session_state.cart

                    rec_b1, rec_b2 = st.columns(2)
                    with rec_b1:
                        rec_wish_label = "💔 Remove" if rec_wishlisted else "❤️ Add to Wishlist"
                        if st.button(
                            rec_wish_label,
                            key=f"rec_wish_{item['Product Name']}_{rank}",
                            use_container_width=True
                        ):
                            toggle_wishlist(item["Product Name"])
                            st.rerun()
                    with rec_b2:
                        rec_cart_label = "✅ In Cart" if rec_in_cart else "🛒 Add to Cart"
                        if st.button(
                            rec_cart_label,
                            key=f"rec_cart_{item['Product Name']}_{rank}",
                            use_container_width=True,
                            type="primary",
                            disabled=rec_in_cart
                        ):
                            add_to_cart(item["Product Name"])
                            st.rerun()

                    st.markdown("</div>", unsafe_allow_html=True)

# ============================================================
#  FOOTER
# ============================================================

st.divider()
st.markdown(
    f"<p style='text-align:center;color:{THEME['subtext']};font-size:13px;'>"
    "Built with Streamlit • Content-based recommendation engine"
    "</p>",
    unsafe_allow_html=True
)
