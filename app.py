import datetime
from fpdf import FPDF
import pandas as pd
import streamlit as st

# إعدادات صفحة التطبيق
st.set_page_config(
    page_title="نظام إدارة محطة الكهرباء", page_icon="⚡", layout="wide"
)

st.title("⚡ نظام إدارة محطة الكهرباء - اليمن")
st.markdown("إدارة المشتركين، قراءات العدادات، الفواتير، وكشوفات الـ PDF.")

# محاكاة قاعدة بيانات مؤقتة في الذاكرة
if "subscribers" not in st.session_state:
    st.session_state.subscribers = pd.DataFrame(
        columns=[
            "رقم المشترك",
            "اسم المشترك",
            "رقم الهاتف",
            "المربع",
            "نوع الفوترة",
            "سعر الكيلو",
            "القراءة السابقة",
            "القراءة الحالية",
            "الاستهلاك",
            "المبلغ المطلوب",
            "المبلغ المدفوع",
            "المتبقي",
        ]
    )

menu = ["إدارة المشتركين وحساب الفواتير", "إضافة مشترك جديد", "تقارير وتصدير PDF"]
choice = st.sidebar.selectbox("القائمة الرئيسية", menu)

# --- 1. إضافة مشترك جديد ---
if choice == "إضافة مشترك جديد":
    st.subheader("➕ إضافة مشترك جديد إلى المحطة")

    with st.form("add_sub_form"):
        col1, col2 = st.columns(2)
        with col1:
            name = st.text_input("اسم المشترك الثلاثي")
            phone = st.text_input("رقم الهاتف (للتواصل / واتساب)")
            block = st.text_input("المربع أو خط التوزيع (مثلاً: المربع الشرقي)")
        with col2:
            billing_type = st.selectbox(
                "دورة الفوترة", ["شهري", "نصف شهري (كل 15 يوم)"]
            )
            price_per_unit = st.number_input("سعر الكيلو (بالريال اليمني)", value=300)
            prev_reading = st.number_input(
                "قراءة العداد السابقة", value=0, min_value=0
            )

        submit_btn = st.form_submit_button("حفظ المشترك")

        if submit_btn:
            if name:
                new_id = len(st.session_state.subscribers) + 1
                new_data = {
                    "رقم المشترك": new_id,
                    "اسم المشترك": name,
                    "رقم الهاتف": phone,
                    "المربع": block,
                    "نوع الفوترة": billing_type,
                    "سعر الكيلو": price_per_unit,
                    "القراءة السابقة": prev_reading,
                    "القراءة الحالية": prev_reading,
                    "الاستهلاك": 0,
                    "المبلغ المطلوب": 0,
                    "المبلغ المدفوع": 0,
                    "المتبقي": 0,
                }
                st.session_state.subscribers = pd.concat(
                    [
                        st.session_state.subscribers,
                        pd.DataFrame([new_data]),
                    ],
                    ignore_index=True,
                )
                st.success(
                    f"تم إضافة المشترك ({name}) بنجاح برقم تعريف #{new_id}!"
                )
            else:
                st.error("الرجاء إدخال اسم المشترك على الأقل.")

# --- 2. إدارة المشتركين وحساب الفواتير ---
elif choice == "إدارة المشتركين وحساب الفواتير":
    st.subheader("📋 قائمة المشتركين وتحديث القراءات والتحصيل")

    if st.session_state.subscribers.empty:
        st.info("لا يوجد مشتركين حالياً. قم بإضافة مشتركين من القائمة الجانبية.")
    else:
        edited_df = st.data_editor(
            st.session_state.subscribers, num_rows="dynamic", use_container_width=True
        )

        if st.button(
            "🔄 تحديث الحسابات تلقائياً (الاستهلاك والفواتير)",
            type="primary",
        ):
            for index, row in edited_df.iterrows():
                consumption = max(
                    0, row["القراءة الحالية"] - row["القراءة السابقة"]
                )
                edited_df.at[index, "الاستهلاك"] = consumption
                total_due = consumption * row["سعر الكيلو"]
                edited_df.at[index, "المبلغ المطلوب"] = total_due
                edited_df.at[index, "المتبقي"] = max(
                    0, total_due - row["المبلغ المدفوع"]
                )

            st.session_state.subscribers = edited_df
            st.success("تم تحديث الحسابات وقيم الاستهلاك بنجاح!")
            st.rerun()

# --- 3. تقارير وتصدير PDF ---
elif choice == "تقارير وتصدير PDF":
    st.subheader("📄 إصدار كشوفات وحسابات PDF")

    if st.session_state.subscribers.empty:
        st.warning("لا توجد بيانات لتصديرها.")
    else:
        sub_names = st.session_state.subscribers["اسم المشترك"].tolist()
        selected_sub = st.selectbox(
            "اختر المشترك لطباعة كشف حسابه", sub_names
        )

        if st.button("📥 توليد كشف حساب PDF"):
            sub_data = st.session_state.subscribers[
                st.session_state.subscribers["اسم المشترك"] == selected_sub
            ].iloc[0]

            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", "B", 16)
            pdf.cell(
                200, 10, txt="Electricity Station Invoice - Al-Dhalea", ln=True, align="C"
            )
            pdf.set_font("Arial", "", 12)
            pdf.ln(10)

            pdf.cell(
                200, 10, txt=f"Subscriber Name: {sub_data['اسم المشترك']}", ln=True
            )
            pdf.cell(
                200, 10, txt=f"Phone: {sub_data['رقم الهاتف']}", ln=True
            )
            pdf.cell(
                200, 10, txt=f"Area/Block: {sub_data['المربع']}", ln=True
            )
            pdf.cell(
                200, 10, txt=f"Billing Cycle: {sub_data['نوع الفوترة']}", ln=True
            )
            pdf.ln(5)
            pdf.cell(
                200, 10, txt=f"Previous Reading: {sub_data['القراءة السابقة']}", ln=True
            )
            pdf.cell(
                200, 10, txt=f"Current Reading: {sub_data['القراءة الحالية']}", ln=True
            )
            pdf.cell(
                200, 10, txt=f"Total Consumption: {sub_data['الاستهلاك']} Units", ln=True
            )
            pdf.cell(
                200, 10, txt=f"Total Due: {sub_data['المبلغ المطلوب']} YER", ln=True
            )
            pdf.cell(
                200, 10, txt=f"Amount Paid: {sub_data['المبلغ المدفوع']} YER", ln=True
            )
            pdf.cell(
                200, 10, txt=f"Remaining Balance: {sub_data['المتبقي']} YER", ln=True
            )

            pdf_filename = f"Invoice_{selected_sub}.pdf"
            pdf.output(pdf_filename)

            with open(pdf_filename, "rb") as f:
                st.download_button(
                    label="⬇️ اضغط هنا لتحميل ملف الـ PDF على هاتفك",
                    data=f,
                    file_name=pdf_filename,
                    mime="application/pdf",
                )
