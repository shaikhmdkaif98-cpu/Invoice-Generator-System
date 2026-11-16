
import streamlit as st
import pandas as pd
import hashlib
import secrets
import os
import re
from io import BytesIO
from datetime import date
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle
)

# ---------------- PAGE SETTINGS ----------------

st.set_page_config(
    page_title="Invoice Generator",
    page_icon="🧾",
    layout="wide"
)

st.title("🧾 Invoice Generator System")

USERS_FILE = "users.txt"
INVOICE_FOLDER = "invoices"

os.makedirs(INVOICE_FOLDER, exist_ok=True)

# ---------------- SESSION STATE ----------------

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "username" not in st.session_state:
    st.session_state.username = ""

if "invoice_pdf" not in st.session_state:
    st.session_state.invoice_pdf = None

if "invoice_filename" not in st.session_state:
    st.session_state.invoice_filename = "Invoice.pdf"


# ---------------- PASSWORD FUNCTIONS ----------------

def make_password_hash(password, salt):
    password_hash = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode(),
        salt.encode(),
        200000
    )

    return password_hash.hex()


def read_users():
    users = {}

    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, "r") as file:
            for line in file:
                parts = line.strip().split("|")

                if len(parts) == 3:
                    username, salt, password_hash = parts
                    users[username] = (salt, password_hash)

    return users


# ---------------- PDF GENERATION ----------------

def create_invoice_pdf(
    customer_name,
    customer_email,
    invoice_number,
    invoice_date,
    products,
    subtotal,
    gst_amount,
    grand_total,
    gst_option
):

    buffer = BytesIO()

    pdf = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=20 * mm,
        leftMargin=20 * mm,
        topMargin=20 * mm,
        bottomMargin=20 * mm
    )

    styles = getSampleStyleSheet()
    elements = []

    elements.append(
        Paragraph("<b>INVOICE</b>", styles["Title"])
    )

    elements.append(Spacer(1, 15))

    elements.append(
        Paragraph(
            f"<b>Invoice Number:</b> {escape(str(invoice_number))}",
            styles["Normal"]
        )
    )

    elements.append(
        Paragraph(
            f"<b>Date:</b> {invoice_date.strftime('%d-%m-%Y')}",
            styles["Normal"]
        )
    )

    elements.append(Spacer(1, 15))

    elements.append(
        Paragraph("<b>Customer Details</b>", styles["Heading2"])
    )

    elements.append(
        Paragraph(
            f"Name: {escape(str(customer_name))}",
            styles["Normal"]
        )
    )

    elements.append(
        Paragraph(
            f"Email: {escape(str(customer_email))}",
            styles["Normal"]
        )
    )

    elements.append(Spacer(1, 20))

    # Product table

    table_data = [
        ["Product", "Quantity", "Price", "Total"]
    ]

    for _, row in products.iterrows():

        product_name = escape(str(row["Product"]))
        quantity = int(row["Quantity"])
        price = float(row["Price"])
        total = quantity * price

        table_data.append([
            product_name,
            str(quantity),
            f"Rs. {price:.2f}",
            f"Rs. {total:.2f}"
        ])

    product_table = Table(
        table_data,
        colWidths=[75 * mm, 25 * mm, 35 * mm, 40 * mm]
    )

    product_table.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.darkblue),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("ALIGN", (1, 1), (-1, -1), "CENTER"),
            ("PADDING", (0, 0), (-1, -1), 8),
            ("BACKGROUND", (0, 1), (-1, -1), colors.whitesmoke)
        ])
    )

    elements.append(product_table)

    elements.append(Spacer(1, 25))

    # GST Summary

    elements.append(
        Paragraph(
            f"Subtotal: Rs. {subtotal:.2f}",
            styles["Normal"]
        )
    )

    elements.append(
        Paragraph(
            f"GST Option: {gst_option}",
            styles["Normal"]
        )
    )

    elements.append(
        Paragraph(
            f"GST Amount: Rs. {gst_amount:.2f}",
            styles["Normal"]
        )
    )

    elements.append(Spacer(1, 10))

    elements.append(
        Paragraph(
            f"<b>Grand Total: Rs. {grand_total:.2f}</b>",
            styles["Heading2"]
        )
    )

    elements.append(Spacer(1, 30))

    elements.append(
        Paragraph(
            "Thank you for your business!",
            styles["Heading2"]
        )
    )

    pdf.build(elements)

    return buffer.getvalue()


# ---------------- LOGIN AND SIGNUP ----------------

if not st.session_state.logged_in:

    login_tab, signup_tab = st.tabs(["Login", "Sign Up"])

    with login_tab:

        st.subheader("Login to Your Account")

        with st.form("login_form"):

            login_username = st.text_input("Username")
            login_password = st.text_input(
                "Password",
                type="password"
            )

            login_button = st.form_submit_button("Login")

            if login_button:

                users = read_users()

                if login_username in users:

                    salt, saved_hash = users[login_username]

                    entered_hash = make_password_hash(
                        login_password,
                        salt
                    )

                    if entered_hash == saved_hash:

                        st.session_state.logged_in = True
                        st.session_state.username = login_username

                        st.success("Login Successful!")
                        st.rerun()

                    else:
                        st.error("Incorrect Password")

                else:
                    st.error("Username not found")

    with signup_tab:

        st.subheader("Create New Account")

        with st.form("signup_form"):

            new_username = st.text_input("Create Username")
            new_password = st.text_input(
                "Create Password",
                type="password"
            )
            confirm_password = st.text_input(
                "Confirm Password",
                type="password"
            )

            signup_button = st.form_submit_button("Sign Up")

            if signup_button:

                users = read_users()

                if not new_username or not new_password:
                    st.error("Please enter username and password")

                elif new_username in users:
                    st.error("Username already exists")

                elif new_password != confirm_password:
                    st.error("Passwords do not match")

                else:

                    salt = secrets.token_hex(16)

                    password_hash = make_password_hash(
                        new_password,
                        salt
                    )

                    with open(USERS_FILE, "a") as file:
                        file.write(
                            f"{new_username}|{salt}|{password_hash}\n"
                        )

                    st.success("Account Created Successfully!")
                    st.info("Now login with your account.")


# ---------------- MAIN DASHBOARD ----------------

else:

    st.success(
        f"Welcome, {st.session_state.username}!"
    )

    if st.button("Logout"):

        st.session_state.logged_in = False
        st.session_state.username = ""
        st.session_state.invoice_pdf = None

        st.rerun()

    st.divider()

    st.header("Create New Invoice")

    # Customer details

    st.subheader("Customer Details")

    col1, col2 = st.columns(2)

    with col1:
        customer_name = st.text_input("Customer Name")

    with col2:
        customer_email = st.text_input("Customer Email")

    col3, col4 = st.columns(2)

    with col3:
        invoice_number = st.text_input(
            "Invoice Number",
            value="INV-001"
        )

    with col4:
        invoice_date = st.date_input(
            "Invoice Date",
            value=date.today()
        )

    st.divider()

    # Product details

    st.subheader("Product Details")

    default_products = pd.DataFrame({
        "Product": ["Laptop"],
        "Quantity": [1],
        "Price": [50000.0]
    })

    products = st.data_editor(
        default_products,
        num_rows="dynamic",
        use_container_width=True,
        column_config={
            "Product": st.column_config.TextColumn(
                "Product Name",
                required=True
            ),
            "Quantity": st.column_config.NumberColumn(
                "Quantity",
                min_value=1,
                step=1
            ),
            "Price": st.column_config.NumberColumn(
                "Price",
                min_value=0.0,
                step=100.0
            )
        }
    )

    st.divider()

    # GST Settings

    st.subheader("GST Settings")

    gst_option = st.selectbox(
        "Select GST Option",
        [
            "Add GST (+18%)",
            "Remove GST (-18%)",
            "No GST"
        ]
    )

    # ---------------- CALCULATION ----------------

    if st.button("Generate Invoice", type="primary"):

        if not customer_name.strip():
            st.error("Please enter customer name")

        elif not invoice_number.strip():
            st.error("Please enter invoice number")

        elif products.empty:
            st.error("Please add at least one product")

        elif (
            products["Product"].isna().any()
            or (products["Product"].astype(str).str.strip() == "").any()
            or products["Quantity"].isna().any()
            or products["Price"].isna().any()
            or (products["Quantity"] <= 0).any()
            or (products["Price"] < 0).any()
        ):
            st.error("Please enter valid product details")

        else:

            # Calculate product total

            products = products.copy()

            products["Total"] = (
                products["Quantity"] * products["Price"]
            )

            entered_total = products["Total"].sum()

            # GST calculation

            if gst_option == "Add GST (+18%)":

                subtotal = entered_total
                gst_amount = subtotal * 0.18
                grand_total = subtotal + gst_amount

            elif gst_option == "Remove GST (-18%)":

                grand_total = entered_total
                subtotal = grand_total / 1.18
                gst_amount = grand_total - subtotal

            else:

                subtotal = entered_total
                gst_amount = 0
                grand_total = subtotal

            # Create PDF

            pdf_data = create_invoice_pdf(
                customer_name,
                customer_email,
                invoice_number,
                invoice_date,
                products,
                subtotal,
                gst_amount,
                grand_total,
                gst_option
            )

            # Save PDF

            safe_invoice_number = re.sub(
                r"[^A-Za-z0-9_-]",
                "_",
                invoice_number
            )

            filename = f"{safe_invoice_number}.pdf"

            invoice_path = os.path.join(
                INVOICE_FOLDER,
                filename
            )

            with open(invoice_path, "wb") as file:
                file.write(pdf_data)

            # Store PDF in session

            st.session_state.invoice_pdf = pdf_data
            st.session_state.invoice_filename = filename

            st.success("Invoice Generated Successfully!")

    # ---------------- INVOICE SUMMARY ----------------

    if st.session_state.invoice_pdf is not None:

        st.divider()

        st.header("Invoice Ready")

        st.success("Your PDF invoice is ready to download.")

        st.download_button(
            label="📥 Download Invoice PDF",
            data=st.session_state.invoice_pdf,
            file_name=st.session_state.invoice_filename,
            mime="application/pdf",
            type="primary",
            use_container_width=True
        )

        st.caption(
            "Click the button above to download your invoice."
        )

        
    # ---------------- INVOICE HISTORY ----------------

    st.divider()

    st.header("📁 Invoice History")

    invoice_files = sorted(
        [
            file for file in os.listdir(INVOICE_FOLDER)
            if file.lower().endswith(".pdf")
        ],
        reverse=True
    )

    if invoice_files:

        st.write("Your previously generated invoices:")

        for invoice in invoice_files:

            invoice_path = os.path.join(
                INVOICE_FOLDER,
                invoice
            )

            with open(invoice_path, "rb") as file:
                pdf_data = file.read()

            col1, col2 = st.columns([3, 1])

            with col1:
                st.write("🧾 " + invoice)

            with col2:
                st.download_button(
                    label="📥 Download",
                    data=pdf_data,
                    file_name=invoice,
                    mime="application/pdf",
                    key="history_" + invoice
                )

    else:
        st.info("No invoices found. Generate your first invoice!")
